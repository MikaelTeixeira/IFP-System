"""Preview and publish reviewed answer sheets as student assessment results."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from flask import current_app, url_for

from ..data.academic import eligible_students
from ..data.answer_sheets import STALE_PAGE, batch_status_values, get_batch, get_sheet, list_batches
from ..data.attempts import corrections_for, lock_students, rectify_attempt
from ..extensions import db
from ..models import AnswerScanBatch, AnswerScanPage, AssessmentAttempt, AttemptAnswer, Notification, Student
from .layout import question_manifest


READY_STATES = {"Lido", "Conferido"}
ACTIVE_STATES = READY_STATES | {"Revisão", "Lançado"}


def current_attempt(assessment_id, student_id):
    return (AssessmentAttempt.query.filter_by(assessment_id=assessment_id, student_id=student_id)
            .filter(AssessmentAttempt.status != "Substituída")
            .order_by(AssessmentAttempt.started_at.desc()).first())


def _roster(batch, assessment, all_pages):
    """Account for the whole expected audience, not only the pages that happened to be scanned."""
    expected = eligible_students(assessment, batch.get("scope", {}))
    received = {page["student_id"] for _, page in all_pages}
    launched = {page["student_id"] for _, page in all_pages if page["status"] == "Lançado"}
    absent = [student for student in expected if student["id"] not in received]
    with_result = set()
    if absent and current_app.config["DATABASE_ENABLED"]:
        with_result = {attempt.student_id for attempt in AssessmentAttempt.query.filter(
            AssessmentAttempt.assessment_id == batch["assessment_id"],
            AssessmentAttempt.student_id.in_([student["id"] for student in absent]),
            AssessmentAttempt.status.notin_(["Substituída", "Em andamento"]),
        )}
    missing = [{"id": student["id"], "name": student["nome"], "enrollment": student.get("matricula", ""),
                "has_result": student["id"] in with_result} for student in absent]
    return {"expected": len(expected), "received": len(expected) - len(absent),
            "launched": sum(student["id"] in launched for student in expected),
            "missing": missing, "without_result": sum(not item["has_result"] for item in missing)}


def preview_results(batch, assessment, questions, batches=None):
    """Use the same checks for the preview and the final POST."""
    batches = batches if batches is not None else list_batches()
    students = {item.id: item.name for item in Student.query.all()} if current_app.config["DATABASE_ENABLED"] else {}
    by_question = {item["id"]: item for item in questions}
    try:
        current_manifest = question_manifest(assessment, questions)
    except ValueError:
        current_manifest = []
    all_pages = [
        (other_batch, page)
        for other_batch in batches if other_batch["assessment_id"] == batch["assessment_id"]
        for page in other_batch["pages"] if page["status"] in ACTIVE_STATES and page.get("student_id")
    ]
    rows = []
    blockers = []
    for page in batch["pages"]:
        row = {"page": page, "student_name": students.get(page.get("student_id"), "Estudante não identificado"),
               "score": None, "total": 0, "blanks": 0, "answers": [], "conflict": None, "choice": None,
               "duplicate": [], "issues": [], "corrections": []}
        rows.append(row)
        if page["status"] in {"Ignorada", "Lançado"}:
            if page["status"] == "Lançado":
                launch = page.get("analysis", {}).get("result_launch", {})
                row.update(score=launch.get("score"), total=launch.get("total", 0), blanks=launch.get("blanks", 0))
                # The published result is the source of truth once a rectification changed it.
                attempt = (db.session.get(AssessmentAttempt, launch.get("attempt_id"))
                           if current_app.config["DATABASE_ENABLED"] and launch.get("attempt_id") else None)
                if attempt:
                    row["score"] = int(attempt.objective_score)
                    row["blanks"] = sum(not answer.answer_text for answer in attempt.answers if not answer.is_open)
                    row["corrections"] = corrections_for(attempt.id)
            continue
        if page["status"] == "Falha":
            row["issues"].append("Identifique este cartão ou desconsidere a página.")
        elif page["status"] == "Revisão":
            row["issues"].append("Confira as respostas antes do lançamento.")
        elif page["status"] not in READY_STATES:
            row["issues"].append("Situação da página não permite lançamento.")
        else:
            sheet = get_sheet(page["answer_sheet_id"]) if page.get("answer_sheet_id") else None
            manifest = sheet.get("snapshot", {}).get("questions", []) if sheet else []
            if not sheet or sheet["student_id"] != page["student_id"] or sheet["assessment_id"] != batch["assessment_id"]:
                row["issues"].append("O cartão emitido não corresponde a esta página.")
            elif not current_manifest or current_manifest != manifest:
                row["issues"].append("A composição mudou desde a emissão; emita e leia um cartão atualizado.")
            elif len(manifest) != len(assessment.get("question_ids", [])):
                row["issues"].append("Este simulado contém questão aberta, que não cabe no cartão-resposta.")
            else:
                row["total"] = len(manifest)
                for question in manifest:
                    number = str(question["number"])
                    answer = page["detected_answers"].get(number, "")
                    live_question = by_question.get(question["question_id"], {})
                    key = live_question.get("gabarito")
                    if answer not in ["", *question["options"]] or key not in question["options"]:
                        row["issues"].append(f"Questão {number}: resposta ou gabarito inválido.")
                        continue
                    row["answers"].append({"number": question["number"], "question_id": question["question_id"],
                                           "answer": answer, "key": key, "correct": bool(answer and answer == key)})
                if len(row["answers"]) == len(manifest):
                    row["score"] = sum(answer["correct"] for answer in row["answers"])
                    row["blanks"] = sum(not answer["answer"] for answer in row["answers"])
            row["duplicate"] = [
                {"batch_id": other_batch["id"], "page_id": other["id"], "page_number": other["page_number"]}
                for other_batch, other in all_pages
                if other["id"] != page["id"] and other["student_id"] == page["student_id"]
            ]
            if row["duplicate"]:
                row["issues"].append("Há outro cartão ativo para este aluno. Desconsidere uma das páginas.")
            if current_app.config["DATABASE_ENABLED"] and page.get("student_id"):
                attempt = current_attempt(batch["assessment_id"], page["student_id"])
                if attempt:
                    row["conflict"] = {"id": attempt.id, "status": attempt.status,
                                       "score": attempt.final_score}
                    choice = page.get("analysis", {}).get("result_choice", {})
                    if choice.get("attempt_id") == attempt.id:
                        row["choice"] = choice.get("decision")
                    if choice.get("decision") != "use_card" or choice.get("attempt_id") != attempt.id:
                        row["issues"].append("Já existe uma tentativa deste aluno. Escolha qual resultado manter.")
        if row["issues"]:
            blockers.append({"page_number": page["page_number"], "messages": row["issues"]})
    if batch.get("error_message"):
        blockers.append({"page_number": None, "messages": ["O processamento deste arquivo falhou. Reenvie o lote completo."]})
    if assessment.get("status") not in {"Publicado", "Agendado"}:
        blockers.append({"page_number": None, "messages": ["Publique o simulado antes de lançar resultados para os alunos."]})
    if not current_app.config["DATABASE_ENABLED"]:
        blockers.append({"page_number": None, "messages": ["Configure um banco persistente para lançar resultados."]})
    ready = [row for row in rows if row["page"]["status"] in READY_STATES and not row["issues"]]
    return {"rows": rows, "blockers": blockers, "ready": ready, "can_publish": bool(ready) and not blockers,
            "roster": _roster(batch, assessment, all_pages),
            "launched_count": sum(row["page"]["status"] == "Lançado" for row in rows),
            "ignored_count": sum(row["page"]["status"] == "Ignorada" for row in rows)}


def publish_results(batch_id, assessment, questions, profile, missing_acknowledged=False):
    """Create every result, archive replaced attempts and notify students in one transaction."""
    if not current_app.config["DATABASE_ENABLED"]:
        raise ValueError("Configure um banco persistente para lançar resultados.")
    try:
        locked_batch = (AnswerScanBatch.query.filter_by(id=batch_id).populate_existing().with_for_update().one_or_none())
        if not locked_batch:
            raise ValueError("Lote não encontrado.")
        lock_students(page.student_id for page in locked_batch.pages if page.student_id)
        db.session.expire_all()
        batch = get_batch(batch_id)
        preview = preview_results(batch, assessment, questions)
        if not preview["can_publish"]:
            raise ValueError("Resolva todas as páginas e conflitos antes de lançar as notas.")
        if preview["roster"]["without_result"] and not missing_acknowledged:
            raise ValueError("Confirme que os alunos sem cartão lido continuarão sem nota.")
        launched_at = datetime.now(UTC).replace(tzinfo=None)
        for index, row in enumerate(preview["ready"]):
            page = row["page"]
            existing = row["conflict"]
            if existing:
                previous = db.session.get(AssessmentAttempt, existing["id"])
                previous.status = "Substituída"
            attempt_id = str(uuid4())
            timestamp = launched_at + timedelta(microseconds=index)
            attempt = AssessmentAttempt(
                id=attempt_id, assessment_id=batch["assessment_id"], student_id=page["student_id"],
                status="Resultado disponível", started_at=timestamp, submitted_at=timestamp,
                duration_seconds=0, remaining_seconds=0, objective_score=float(row["score"]),
                final_score=float(row["score"]),
            )
            attempt.answers = [AttemptAnswer(
                id=str(uuid4()), question_id=answer["question_id"], answer_text=answer["answer"],
                is_open=False, is_correct=answer["correct"], answer_key=answer["key"],
            ) for answer in row["answers"]]
            db.session.add(attempt)
            model = db.session.get(AnswerScanPage, page["id"])
            analysis = deepcopy(model.analysis or {})
            analysis["result_launch"] = {
                "attempt_id": attempt_id, "score": row["score"], "total": row["total"],
                "blanks": row["blanks"], "answers": row["answers"],
                "replaced_attempt_id": existing["id"] if existing else None,
                "reviewer": profile.get("account_id", "global"), "at": timestamp.isoformat(),
            }
            model.analysis = analysis
            model.status = "Lançado"
            db.session.add(Notification(
                id=str(uuid4()), recipient_role="student", recipient_id=page["student_id"],
                kind="paper_result", title="Resultado do cartão-resposta disponível",
                message=assessment["titulo"],
                url=url_for("student_area.assessment_result", assessment_id=batch["assessment_id"]),
            ))
        values = batch_status_values([page.status for page in locked_batch.pages], locked_batch.error_message or "")
        for key, value in values.items():
            setattr(locked_batch, key, value)
        db.session.commit()
        return len(preview["ready"])
    except Exception:
        db.session.rollback()
        raise


def rectify_paper_page(batch_id, page_id, answers, reason, profile):
    """Correct a card misread after launch: the page and the published result change together."""
    try:
        locked_batch = AnswerScanBatch.query.filter_by(id=batch_id).populate_existing().with_for_update().one_or_none()
        model = (AnswerScanPage.query.filter_by(id=page_id, batch_id=batch_id)
                 .populate_existing().with_for_update().one_or_none())
        if not locked_batch or not model:
            raise ValueError("Página não encontrada.")
        launch = (model.analysis or {}).get("result_launch", {})
        if model.status != "Lançado" or not launch.get("attempt_id"):
            raise ValueError(STALE_PAGE)
        by_number = {str(item["number"]): item["question_id"] for item in launch.get("answers", [])}
        if set(answers) != set(by_number):
            raise ValueError("Envie a resposta de todas as questões do cartão.")
        correction = rectify_attempt(
            launch["attempt_id"], "leitura", reason, profile,
            answers={by_number[number]: answer for number, answer in answers.items()},
        )
        if not correction:
            raise ValueError("Nenhuma resposta mudou; a nota continua a mesma.")
        analysis = deepcopy(model.analysis)
        analysis.setdefault("rectifications", []).append({
            "correction_id": correction.id, "previous": dict(model.detected_answers or {}), "answers": dict(answers),
            "reason": correction.reason, "reviewer": correction.actor_id, "at": datetime.now(UTC).isoformat(),
        })
        model.detected_answers = dict(answers)
        model.analysis = analysis
        db.session.commit()
        return correction
    except Exception:
        db.session.rollback()
        raise
