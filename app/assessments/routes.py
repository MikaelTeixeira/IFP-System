from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for

from . import assessments_bp
from ..auth.security import current_profile, login_required
from ..data.academic import DATA, find
from ..data.assessments import (
    ASSESSMENTS,
    ASSESSMENT_REQUESTS,
    add_assessment,
    add_assessment_request,
    delete_assessment,
    find_assessment,
    find_assessment_request,
    find_request_assignment,
    find_request_submission,
    refresh_request_status,
    persist_assessment_request,
    submit_request_question,
    teacher_request_history,
    update_assessment,
)
from ..data.curriculum import find_subject, subjects_for_profile
from ..data.questions import QUESTIONS, find_question, persist_question
from ..data.notifications import add_notification, add_role_notification
from ..data.reviews import add_review_event
from ..data.attempts import attempts_with_graded_answers, attempts_with_pending_answers, grade_open_answers
from ..extensions import db
from ..models import AssessmentAttempt


ACCESS_ROLES = {"school_coordinator", "institute_coordinator", "it_admin"}
MANAGE_ROLES = {"institute_coordinator", "it_admin"}
SCHEDULE_ROLES = {"institute_coordinator", "it_admin"}


def ensure_access(manage=False):
    profile = current_profile()
    if profile["key"] not in (MANAGE_ROLES if manage else ACCESS_ROLES):
        abort(403)
    return profile


def assessment_in_scope(profile, assessment):
    return profile["key"] in {"institute_coordinator", "it_admin"} or profile.get("institution_id") in assessment.get("instituicao_ids", [])


def assessment_values(form, current=None):
    current = current or {}
    question_ids = form.getlist("question_ids") or current.get("question_ids", [])
    institution_ids = form.getlist("institution_ids") or current.get("institution_ids", [])
    try:
        duration = max(1, int(form.get("duracao", current.get("duracao", 40))))
    except (TypeError, ValueError):
        duration = 40
    return {
        "titulo": form.get("titulo", "").strip() or current.get("titulo", "Novo simulado de Matemática"),
        "modalidade": form.get("modalidade", current.get("modalidade", "Remoto")),
        "publico": form.get("publico", "").strip() or current.get("publico", "7º ano"),
        "duracao": duration,
        "data": form.get("data", "").strip(),
        "descricao": form.get("descricao", "").strip(),
        "question_ids": question_ids,
        "instituicao_ids": institution_ids,
        "tentativa_unica": form.get("tentativa_unica", "") == "1" if form else current.get("tentativa_unica", True),
    }


def request_in_scope(profile, assessment_request):
    return profile["key"] in {"institute_coordinator", "it_admin"} or profile.get("institution_id") == assessment_request["instituicao_id"]


def request_form_options(profile):
    institution_id = profile["institution_id"]
    series = [item for item in DATA["series"] if item["instituicao_id"] == institution_id and item["status"] == "Ativa"]
    subjects = [item for item in subjects_for_profile(profile) if item["status"] == "Ativa"]
    teachers = [
        item for item in DATA["professores"]
        if item["instituicao_id"] == institution_id and item["status"].lower() in {"ativo", "ativa"}
    ]
    eligible_teachers = {
        subject["id"]: [teacher for teacher in teachers if subject["id"] in teacher.get("disciplina_ids", [])]
        for subject in subjects
    }
    return series, subjects, eligible_teachers


def enrich_request(assessment_request):
    item = dict(assessment_request)
    item["instituicao"] = find("instituicoes", item["instituicao_id"])
    item["series"] = [find("series", series_id) for series_id in item["serie_ids"] if find("series", series_id)]
    subject_lookup = {subject["id"]: subject for subject in subjects_for_profile({"key": "institute_coordinator"})}
    item["atribuicoes_detalhadas"] = []
    for assignment in item["atribuicoes"]:
        detailed = {
            "materia": subject_lookup.get(assignment["materia_id"]),
            "professor": find("professores", assignment["professor_id"]),
            "quantidade_questoes": max(1, int(assignment.get("quantidade_questoes", 1))),
            "entregas": [],
        }
        for submission in assignment.get("entregas", []):
            detailed["entregas"].append({**submission, "questao": find_question(submission["question_id"])})
        item["atribuicoes_detalhadas"].append(detailed)
    return item


@assessments_bp.get("")
@login_required
def list_assessments():
    profile = ensure_access()
    requests = [item for item in ASSESSMENT_REQUESTS if request_in_scope(profile, item)]
    records = list(ASSESSMENTS)
    if profile["key"] == "school_coordinator":
        records = [item for item in records if assessment_in_scope(profile, item)]
    query = request.args.get("q", "").strip().lower()
    status = request.args.get("status", "")
    if query:
        records = [item for item in records if query in f"{item['titulo']} {item['assunto']} {item['publico']}".lower()]
    if status:
        records = [item for item in records if item["status"] == status]
    return render_template(
        "assessments/list.html",
        page_title="Solicitações de simulados" if profile["key"] == "school_coordinator" else "Simulados",
        records=records,
        requests=[enrich_request(item) for item in requests],
        school_request_view=profile["key"] == "school_coordinator",
        can_manage=profile["key"] in MANAGE_ROLES,
        query=request.args.get("q", ""),
        selected_status=status,
        active_navigation="simulados",
    )


@assessments_bp.route("/solicitar", methods=["GET", "POST"])
@login_required
def request_assessment():
    profile = current_profile()
    if profile["key"] != "school_coordinator":
        abort(403)
    series, subjects, eligible_teachers = request_form_options(profile)
    allowed_series = {item["id"] for item in series}
    allowed_subjects = {item["id"] for item in subjects}
    selected_series = request.form.getlist("serie_ids")
    selected_subjects = request.form.getlist("materia_ids")
    error = None

    if request.method == "POST":
        selected_series = list(dict.fromkeys(item for item in selected_series if item in allowed_series))
        selected_subjects = list(dict.fromkeys(item for item in selected_subjects if item in allowed_subjects))
        assignments = []
        invalid_assignment = False
        invalid_quantity = False
        for subject_id in selected_subjects:
            teacher_id = request.form.get(f"professor_{subject_id}", "")
            eligible_ids = {teacher["id"] for teacher in eligible_teachers[subject_id]}
            try:
                question_count = int(request.form.get(f"quantidade_{subject_id}", ""))
                if question_count < 1 or question_count > 50:
                    invalid_quantity = True
            except (TypeError, ValueError):
                question_count = 0
                invalid_quantity = True
            if teacher_id not in eligible_ids:
                invalid_assignment = True
            else:
                assignments.append({
                    "materia_id": subject_id,
                    "professor_id": teacher_id,
                    "quantidade_questoes": question_count,
                })

        if not selected_series:
            error = "Selecione ao menos um ano para o simulado."
        elif not selected_subjects:
            error = "Selecione ao menos uma matéria."
        elif invalid_assignment or len(assignments) != len(selected_subjects):
            error = "Escolha um professor habilitado para cada matéria selecionada."
        elif invalid_quantity:
            error = "Informe entre 1 e 50 questões para cada matéria selecionada."
        elif not request.form.get("prazo", "").strip():
            error = "Defina o prazo para os professores enviarem as questões."
        else:
            try:
                deadline = datetime.strptime(request.form.get("prazo", ""), "%Y-%m-%d").date()
                if deadline < datetime.now().date():
                    error = "O prazo não pode estar no passado."
            except ValueError:
                error = "Defina um prazo válido para o envio das questões."
        if not error:
            institution = find("instituicoes", profile["institution_id"])
            assessment_request = add_assessment_request({
                "titulo": f"Solicitação de simulado — {institution['nome']}",
                "instituicao_id": profile["institution_id"],
                "serie_ids": selected_series,
                "atribuicoes": [{**assignment, "entregas": []} for assignment in assignments],
                "prazo": request.form.get("prazo", "").strip(),
                "observacoes": request.form.get("observacoes", "").strip(),
            })
            for assignment in assignments:
                subject = find_subject(assignment["materia_id"])
                add_role_notification(
                    "teacher", assignment["professor_id"], "Nova solicitação de simulado",
                    f"Você foi designado para {subject['nome']} e deve enviar {assignment['quantidade_questoes']} "
                    f"{'questão' if assignment['quantidade_questoes'] == 1 else 'questões'}. Prazo: {assessment_request['prazo']}.",
                    url_for("assessments.answer_request", request_id=assessment_request["id"], materia_id=assignment["materia_id"]), "assessment_request",
                )
            flash("Solicitação enviada aos professores responsáveis.", "success")
            return redirect(url_for("assessments.request_detail", request_id=assessment_request["id"]))

    return render_template(
        "assessments/request_form.html",
        page_title="Solicitar simulado",
        series=series,
        subjects=subjects,
        eligible_teachers=eligible_teachers,
        selected_series=selected_series,
        selected_subjects=selected_subjects,
        values=request.form,
        error=error,
        active_navigation="simulados",
    ), 400 if error else 200


@assessments_bp.get("/solicitacoes/<request_id>")
@login_required
def request_detail(request_id):
    profile = ensure_access()
    assessment_request = find_assessment_request(request_id)
    if not assessment_request:
        abort(404)
    if not request_in_scope(profile, assessment_request):
        abort(403)
    return render_template(
        "assessments/request_detail.html",
        page_title="Solicitação de simulado",
        assessment_request=enrich_request(assessment_request),
        can_review=profile["key"] == "school_coordinator",
        active_navigation="simulados",
    )


@assessments_bp.get("/solicitacoes-professor")
@login_required
def teacher_requests():
    profile = current_profile()
    if profile["key"] != "teacher":
        abort(403)
    records = []
    for assessment_request in ASSESSMENT_REQUESTS:
        item = enrich_request(assessment_request)
        for detail in item["atribuicoes_detalhadas"]:
            if detail["professor"]["id"] == profile["teacher_id"]:
                teacher_item = dict(item)
                teacher_item["minha_atribuicao"] = detail
                records.append(teacher_item)
    return render_template(
        "assessments/teacher_requests.html",
        page_title="Solicitações de questões",
        requests=records,
        active_navigation="solicitacoes-questoes",
    )


@assessments_bp.get("/correcoes")
@login_required
def corrections():
    profile = current_profile()
    if profile["key"] != "teacher":
        abort(403)
    pending_records = []
    for attempt, pending in attempts_with_pending_answers(profile["teacher_id"]):
        assessment = find_assessment(attempt.assessment_id)
        student = find("alunos", attempt.student_id)
        if assessment and student:
            pending_records.append({"attempt": attempt, "assessment": assessment, "student": student, "pending_count": len(pending)})
    history_records = []
    for attempt, graded in attempts_with_graded_answers(profile["teacher_id"]):
        assessment = find_assessment(attempt.assessment_id)
        student = find("alunos", attempt.student_id)
        if assessment and student:
            history_records.append({
                "attempt": attempt,
                "assessment": assessment,
                "student": student,
                "graded_count": len(graded),
                "last_graded_at": max(
                    (answer.graded_at for answer in graded if answer.graded_at),
                    default=attempt.submitted_at or attempt.started_at,
                ),
                "average_grade": sum(answer.grade for answer in graded) / len(graded),
            })
    return render_template(
        "assessments/corrections.html",
        page_title="Correções",
        pending_records=pending_records,
        history_records=history_records,
        active_navigation="correcoes",
    )


@assessments_bp.route("/correcoes/<attempt_id>", methods=["GET", "POST"])
@login_required
def correction_detail(attempt_id):
    profile = current_profile()
    if profile["key"] != "teacher":
        abort(403)
    attempt = db.session.get(AssessmentAttempt, attempt_id)
    if not attempt:
        abort(404)
    owned_answers = [item for item in attempt.answers if item.is_open and (find_question(item.question_id) or {}).get("autor_id") == profile["teacher_id"]]
    if not owned_answers:
        abort(403)
    error = None
    if request.method == "POST":
        try:
            graded, completed = grade_open_answers(attempt, profile["teacher_id"], request.form)
        except ValueError as validation_error:
            error = str(validation_error)
        else:
            if not graded:
                error = "Informe a nota de ao menos uma resposta."
            else:
                if completed:
                    assessment = find_assessment(attempt.assessment_id)
                    add_notification(attempt.student_id, "Resultado disponível", assessment["titulo"], url_for("student_area.assessment_result", assessment_id=attempt.assessment_id), "result_available")
                flash("Correção salva e resultado atualizado.", "success")
                return redirect(url_for("assessments.corrections"))
    records = [{"answer": item, "question": find_question(item.question_id)} for item in owned_answers]
    return render_template(
        "assessments/correction_detail.html", page_title="Corrigir respostas abertas",
        attempt=attempt, assessment=find_assessment(attempt.assessment_id),
        student=find("alunos", attempt.student_id), records=records, error=error,
        active_navigation="correcoes",
    ), 400 if error else 200


@assessments_bp.route("/solicitacoes/<request_id>/responder", methods=["GET", "POST"])
@login_required
def answer_request(request_id):
    profile = current_profile()
    if profile["key"] != "teacher":
        abort(403)
    assessment_request = find_assessment_request(request_id)
    if not assessment_request:
        abort(404)
    requested_subject_id = request.values.get("materia_id", "").strip() or None
    assignment = find_request_assignment(assessment_request, profile["teacher_id"], requested_subject_id)
    if not assignment:
        abort(403)
    subject_id = assignment["materia_id"]
    requested_count = max(1, int(assignment.get("quantidade_questoes", 1)))
    submitted_count = len(assignment.get("entregas", []))
    remaining_count = max(0, requested_count - submitted_count)
    submitted_ids = {item["question_id"] for item in assignment.get("entregas", [])}
    history_ids = teacher_request_history(profile["teacher_id"], subject_id, exclude_request_id=request_id)
    history_ids = [item_id for item_id in history_ids if item_id not in submitted_ids]
    history_id_set = set(history_ids)
    bank_questions = [
        item for item in QUESTIONS
        if item.get("autor_id") == profile["teacher_id"] and item.get("materia_id") == subject_id
        and item["id"] not in submitted_ids and item["id"] not in history_id_set
    ]
    history_questions = [find_question(item_id) for item_id in history_ids if find_question(item_id)]
    selection_error = None
    if request.method == "POST":
        if assessment_request["status"] in {"Pronto para agendar", "Agendado"}:
            flash("Esta solicitação já foi finalizada pela coordenação.", "danger")
            return redirect(url_for("assessments.answer_request", request_id=request_id, materia_id=subject_id))
        selections = []
        for source, field in (("Banco de questões", "bank_question_ids"), ("Histórico", "history_question_ids")):
            for question_id in request.form.getlist(field):
                question = find_question(question_id)
                if (question and question.get("autor_id") == profile["teacher_id"]
                        and question.get("materia_id") == subject_id):
                    selections.append((question_id, source))
        selections = list(dict(selections).items())
        if remaining_count <= 0:
            selection_error = "A quantidade solicitada já foi enviada. Aguarde a avaliação da coordenação."
        elif len(selections) != remaining_count:
            question_label = "questão" if remaining_count == 1 else "questões"
            request_description = (
                "a questão solicitada" if requested_count == 1
                else f"as {requested_count} questões solicitadas"
            )
            selection_error = (
                f"Selecione exatamente {remaining_count} {question_label} para completar "
                f"{request_description} pela coordenação."
            )
        else:
            for question_id, source in selections:
                submit_request_question(assessment_request, profile["teacher_id"], subject_id, question_id, source)
            add_role_notification(
                "school_coordinator", assessment_request["instituicao_id"], "Questões recebidas",
                f"{profile['name']} enviou questões para {find_subject(subject_id)['nome']}.",
                url_for("assessments.request_detail", request_id=request_id), "questions_submitted",
            )
            flash("Questões enviadas para avaliação da coordenação.", "success")
            return redirect(url_for("assessments.answer_request", request_id=request_id, materia_id=subject_id))
    enriched_request = enrich_request(assessment_request)
    detailed_assignment = next(
        item for item in enriched_request["atribuicoes_detalhadas"]
        if item["materia"]["id"] == subject_id and item["professor"]["id"] == profile["teacher_id"]
    )
    return render_template(
        "assessments/teacher_request_detail.html",
        page_title="Responder solicitação",
        assessment_request=enriched_request,
        detailed=detailed_assignment,
        assignment=assignment,
        bank_questions=bank_questions,
        history_questions=history_questions,
        requested_count=requested_count,
        submitted_count=submitted_count,
        remaining_count=remaining_count,
        selection_error=selection_error,
        active_navigation="solicitacoes-questoes",
    ), 400 if selection_error else 200


def school_request_or_403(request_id):
    profile = current_profile()
    if profile["key"] != "school_coordinator":
        abort(403)
    assessment_request = find_assessment_request(request_id)
    if not assessment_request:
        abort(404)
    if assessment_request["instituicao_id"] != profile["institution_id"]:
        abort(403)
    return assessment_request


@assessments_bp.post("/solicitacoes/<request_id>/questoes/<question_id>/aprovar")
@login_required
def approve_request_question(request_id, question_id):
    assessment_request = school_request_or_403(request_id)
    _, submission = find_request_submission(assessment_request, question_id)
    if not submission:
        abort(404)
    if submission["status"] not in {"Enviada", "Reenviada"}:
        flash("Aguarde o professor reenviar a questão antes da aprovação.", "danger")
        return redirect(url_for("assessments.request_detail", request_id=request_id))
    submission["status"] = "Aprovada"
    submission["avaliada_em"] = datetime.now().strftime("%d/%m/%Y às %H:%M")
    refresh_request_status(assessment_request)
    persist_assessment_request(assessment_request)
    question = find_question(question_id)
    if question and question.get("revisao_status") == "Revisada":
        question["revisao_status"] = "Aprovada"
        persist_question(question)
        add_review_event(question_id, "Aprovada", "Revisão aprovada dentro da solicitação.", request_id)
    flash("Questão aprovada para este simulado.", "success")
    return redirect(url_for("assessments.request_detail", request_id=request_id))


@assessments_bp.post("/solicitacoes/<request_id>/questoes/<question_id>/solicitar-revisao")
@login_required
def revise_request_question(request_id, question_id):
    assessment_request = school_request_or_403(request_id)
    _, submission = find_request_submission(assessment_request, question_id)
    question = find_question(question_id)
    if not submission or not question:
        abort(404)
    observation = request.form.get("observacao", "").strip()
    if not observation:
        flash("Informe o ajuste que o professor deve realizar.", "danger")
        return redirect(url_for("assessments.request_detail", request_id=request_id))
    submission.update({"status": "Revisão solicitada", "revisao_observacao": observation})
    question.update({
        "revisao_status": "Pendente",
        "revisao_observacao": observation,
        "revisao_solicitada_por": current_profile()["name"],
        "revisao_solicitada_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        "revisao_solicitante_role": "school_coordinator",
        "revisao_solicitante_id": assessment_request["instituicao_id"],
    })
    persist_question(question)
    add_review_event(question_id, "Pendente", observation, request_id)
    add_role_notification("teacher", question["autor_id"], "Revisão de questão solicitada", observation, url_for("questions.detail", question_id=question_id), "question_review")
    refresh_request_status(assessment_request)
    persist_assessment_request(assessment_request)
    flash("Revisão solicitada ao professor responsável.", "success")
    return redirect(url_for("assessments.request_detail", request_id=request_id))


@assessments_bp.post("/solicitacoes/<request_id>/agendar")
@login_required
def schedule_request(request_id):
    assessment_request = school_request_or_403(request_id)
    refresh_request_status(assessment_request)
    if assessment_request["status"] != "Pronto para agendar":
        flash("Aprove todas as questões antes de agendar o simulado.", "danger")
        return redirect(url_for("assessments.request_detail", request_id=request_id))
    raw_date = request.form.get("data", "").strip()
    try:
        scheduled_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        duration = max(1, int(request.form.get("duracao", "40")))
    except (ValueError, TypeError):
        flash("Informe uma data e uma duração válidas.", "danger")
        return redirect(url_for("assessments.request_detail", request_id=request_id))
    if datetime.strptime(raw_date, "%Y-%m-%d").date() < datetime.now().date():
        flash("A data do simulado não pode estar no passado.", "danger")
        return redirect(url_for("assessments.request_detail", request_id=request_id))
    question_ids = [
        submission["question_id"]
        for assignment in assessment_request["atribuicoes"]
        for submission in assignment.get("entregas", [])
        if submission["status"] == "Aprovada"
    ]
    subjects = [find_subject(assignment["materia_id"])["nome"] for assignment in assessment_request["atribuicoes"]]
    assessment = add_assessment({
        "titulo": request.form.get("titulo", "").strip() or assessment_request["titulo"].replace("Solicitação de ", ""),
        "disciplina": ", ".join(subjects),
        "assunto": "Conteúdos selecionados pelos professores",
        "modalidade": "Remoto",
        "publico": ", ".join(find("series", item_id)["nome"] for item_id in assessment_request["serie_ids"]),
        "duracao": duration,
        "data": scheduled_date,
        "status": "Agendado",
        "question_ids": question_ids,
        "instituicao_ids": [assessment_request["instituicao_id"]],
        "serie_ids": assessment_request["serie_ids"],
        "descricao": assessment_request.get("observacoes", ""),
        "tentativa_unica": True,
    })
    assessment_request.update({"status": "Agendado", "assessment_id": assessment["id"], "agendado_em": datetime.now().strftime("%d/%m/%Y às %H:%M")})
    persist_assessment_request(assessment_request)
    eligible_series = set(assessment_request["serie_ids"])
    for student in DATA["alunos"]:
        school_class = find("turmas", student["turma_id"])
        if school_class and school_class["serie_id"] in eligible_series:
            add_notification(
                student["id"],
                "Novo simulado agendado",
                f"{assessment['titulo']} foi agendado para {scheduled_date}.",
                url_for("student_area.assessment_detail", assessment_id=assessment["id"]),
            )
    flash("Simulado agendado. Os alunos participantes foram notificados.", "success")
    return redirect(url_for("assessments.request_detail", request_id=request_id))


@assessments_bp.get("/<assessment_id>")
@login_required
def detail(assessment_id):
    profile = ensure_access()
    assessment = find_assessment(assessment_id)
    if not assessment:
        abort(404)
    if not assessment_in_scope(profile, assessment):
        abort(403)
    questions = [find_question(question_id) for question_id in assessment["question_ids"] if find_question(question_id)]
    institutions = [item for item in DATA["instituicoes"] if item["id"] in assessment["instituicao_ids"]]
    return render_template("assessments/detail.html", page_title=assessment["titulo"], assessment=assessment, questions=questions, institutions=institutions, can_manage=profile["key"] in MANAGE_ROLES, can_schedule=profile["key"] in SCHEDULE_ROLES, can_publish=profile["key"] in MANAGE_ROLES, can_delete=profile["key"] == "it_admin", active_navigation="simulados")


@assessments_bp.route("/novo", methods=["GET", "POST"])
@login_required
def create():
    ensure_access(manage=True)
    if request.method == "POST":
        assessment = add_assessment(assessment_values(request.form))
        flash("Simulado criado como rascunho.", "success")
        return redirect(url_for("assessments.detail", assessment_id=assessment["id"]))
    return render_template("assessments/form.html", page_title="Novo simulado", assessment={}, questions=QUESTIONS, institutions=DATA["instituicoes"], active_navigation="simulados")


@assessments_bp.route("/<assessment_id>/editar", methods=["GET", "POST"])
@login_required
def edit(assessment_id):
    profile = ensure_access(manage=True)
    assessment = find_assessment(assessment_id)
    if not assessment:
        abort(404)
    if not assessment_in_scope(profile, assessment):
        abort(403)
    if request.method == "POST":
        update_assessment(assessment_id, assessment_values(request.form, assessment))
        flash("Simulado atualizado no banco de dados.", "success")
        return redirect(url_for("assessments.detail", assessment_id=assessment_id))
    return render_template("assessments/form.html", page_title="Editar simulado", assessment=assessment, questions=QUESTIONS, institutions=DATA["instituicoes"], active_navigation="simulados")


@assessments_bp.post("/<assessment_id>/excluir")
@login_required
def delete(assessment_id):
    profile = current_profile()
    if profile["key"] != "it_admin":
        abort(403)
    assessment = find_assessment(assessment_id)
    if not assessment:
        abort(404)
    linked_request = any(item.get("assessment_id") == assessment_id for item in ASSESSMENT_REQUESTS)
    if linked_request or AssessmentAttempt.query.filter_by(assessment_id=assessment_id).first():
        flash("O simulado possui solicitação ou tentativa vinculada e não pode ser excluído.", "danger")
        return redirect(url_for("assessments.detail", assessment_id=assessment_id))
    delete_assessment(assessment_id)
    flash("Simulado excluído pelo T.I.", "success")
    return redirect(url_for("assessments.list_assessments"))


@assessments_bp.post("/<assessment_id>/publicar")
@login_required
def publish(assessment_id):
    profile = ensure_access(manage=True)
    assessment = find_assessment(assessment_id)
    if not assessment:
        abort(404)
    if not assessment_in_scope(profile, assessment):
        abort(403)
    update_assessment(assessment_id, {"status": "Publicado"})
    for student in DATA["alunos"]:
        if student["instituicao_id"] in assessment.get("instituicao_ids", []):
            add_notification(student["id"], "Simulado publicado", assessment["titulo"], url_for("student_area.assessment_detail", assessment_id=assessment_id), "assessment_published")
    flash("Simulado publicado e salvo no banco de dados.", "success")
    return redirect(url_for("assessments.detail", assessment_id=assessment_id))


@assessments_bp.post("/<assessment_id>/agendar")
@login_required
def schedule(assessment_id):
    profile = ensure_access()
    if profile["key"] not in SCHEDULE_ROLES:
        abort(403)
    assessment = find_assessment(assessment_id)
    if not assessment:
        abort(404)
    if not assessment_in_scope(profile, assessment):
        abort(403)
    assessment["data"] = request.form.get("data", "").strip() or assessment.get("data", "Data a definir")
    if profile["key"] == "school_coordinator":
        assessment["instituicao_ids"] = [profile["institution_id"]]
    update_assessment(assessment_id, {"data": assessment["data"], "instituicao_ids": assessment.get("instituicao_ids", []), "status": "Agendado"})
    flash("Simulado agendado dentro do escopo permitido.", "success")
    return redirect(url_for("assessments.detail", assessment_id=assessment_id))
