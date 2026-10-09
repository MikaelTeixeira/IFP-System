import base64
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import pypdfium2
import zxingcpp
from flask import abort, current_app, flash, redirect, render_template, request, send_file, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from . import scanner_bp
from .layout import BUBBLE_RADIUS_MM, MARKER_CENTERS_MM, MARKER_SIZE_MM, TEMPLATE_VERSION, answer_rows, question_manifest
from .results import READY_STATES, current_attempt, preview_results, publish_results, rectify_paper_page
from .vision import analyze_answers, annotated_page, iter_upload_pages, prepare_page, save_page, validate_upload
from ..auth.security import check_csrf, csrf_token, current_profile, roles_required
from ..data.academic import DATA, SCOPE_KEYS, eligible_students, matches_scope, student_audience
from ..data.answer_sheets import (
    REVIEWABLE_STATES, add_batch_page, create_batch, decide_page, find_sheets, finish_batch, get_batch, get_sheet,
    identify_page, issue_sheet, list_batches, review_page, sheet_for_token,
)
from ..data.assessments import ASSESSMENTS, find_assessment
from ..data.questions import QUESTIONS


ALLOWED_ROLES = ("school_coordinator", "institute_coordinator", "it_admin")


@scanner_bp.before_request
def scan_request_limits():
    if request.endpoint == "scanner.upload_batch":
        request.max_content_length = current_app.config["SCAN_UPLOAD_MAX_BYTES"] + 1024 * 1024


@scanner_bp.errorhandler(RequestEntityTooLarge)
def upload_too_large(_error):
    flash("O arquivo excede o limite de 50 MB por lote.", "danger")
    return redirect(url_for("scanner.index"))


def _accessible_assessments(profile):
    if profile["key"] == "school_coordinator":
        return [item for item in ASSESSMENTS if profile["institution_id"] in item.get("instituicao_ids", [])]
    return ASSESSMENTS


def _assessment_or_404(assessment_id):
    assessment = find_assessment(assessment_id)
    if not assessment or assessment not in _accessible_assessments(current_profile()):
        abort(404)
    return assessment


def _scope_selection(assessment, values):
    profile = current_profile()
    ids = set(assessment.get("instituicao_ids", []))
    if profile["key"] == "school_coordinator":
        ids &= {profile["institution_id"]}
    institutions = [item for item in DATA["instituicoes"] if item["id"] in ids]
    scope = {key: values.get(key, "").strip() for key in SCOPE_KEYS}
    if scope["institution_id"] and scope["institution_id"] not in ids:
        raise ValueError("A instituição selecionada não pertence ao público deste simulado.")
    if profile["key"] == "school_coordinator":
        scope["institution_id"] = profile["institution_id"]
    allowed_series = set(assessment.get("serie_ids", []))
    series = [item for item in DATA["series"] if item["instituicao_id"] in ids
              and (not allowed_series or item["id"] in allowed_series)
              and (not scope["institution_id"] or item["instituicao_id"] == scope["institution_id"])]
    series_names = sorted({item["nome"] for item in series})
    if scope["series_name"] and scope["series_name"] not in series_names:
        raise ValueError("A série/ano selecionada não está disponível para este público.")
    series_map = {item["id"]: item for item in series}
    classes = [item for item in DATA["turmas"] if item["serie_id"] in series_map]
    school_years = sorted({item["ano_letivo"] for item in classes}, reverse=True)
    if scope["school_year"] and scope["school_year"] not in school_years:
        raise ValueError("O ano letivo selecionado não está disponível.")
    classes = [item for item in classes
               if (not scope["series_name"] or series_map[item["serie_id"]]["nome"] == scope["series_name"])
               and (not scope["school_year"] or item["ano_letivo"] == scope["school_year"])]
    if scope["class_id"] and scope["class_id"] not in {item["id"] for item in classes}:
        raise ValueError("A turma não pertence à série, ano letivo ou instituição selecionada.")
    institutions_map = {item["id"]: item for item in institutions}
    options = {
        "institutions": institutions, "series_names": series_names, "school_years": school_years,
        "classes": [{**item, "series_name": series_map[item["serie_id"]]["nome"],
                     "institution_name": institutions_map[item["instituicao_id"]]["nome"]} for item in classes],
    }
    return scope, options


def _can_access_batch(batch):
    if batch["assessment_id"] not in {item["id"] for item in _accessible_assessments(current_profile())}:
        return False
    profile = current_profile()
    if profile["key"] != "school_coordinator":
        return True
    # A network assessment does not grant a school access to other schools' batches.
    return batch.get("scope", {}).get("institution_id") == profile["institution_id"]


def _batch_or_404(batch_id):
    batch = get_batch(batch_id)
    if not batch or not _can_access_batch(batch):
        abort(404)
    return batch


def _qr_data_uri(token):
    image = np.asarray(zxingcpp.create_barcode(token, zxingcpp.BarcodeFormat.QRCode).to_image(scale=8))
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("Não foi possível gerar o QR Code.")
    return "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")


def _short_issue(issues):
    return ("; ".join(issues[:2]) + (f" (+{len(issues) - 2} ocorrência(s))" if len(issues) > 2 else ""))[:300]


@scanner_bp.get("/")
@roles_required(*ALLOWED_ROLES)
def index():
    assessments = _accessible_assessments(current_profile())
    selected_id = request.args.get("assessment_id") or (assessments[0]["id"] if assessments else None)
    assessment = _assessment_or_404(selected_id) if selected_id else None
    scope, options, students = {}, {}, []
    if assessment:
        try:
            scope, options = _scope_selection(assessment, request.args)
        except ValueError as exc:
            flash(str(exc), "danger")
            scope, options = _scope_selection(assessment, {})
        students = eligible_students(assessment, scope)
    batches = [item for item in list_batches() if _can_access_batch(item)
               and (not assessment or item["assessment_id"] == assessment["id"])
               and matches_scope(item.get("scope", {}), scope)]
    return render_template(
        "scanner/index.html", page_title="Cartões-resposta", assessments=assessments,
        assessment=assessment, scope=scope, options=options, student_count=len(students),
        batches=batches, csrf_token=csrf_token(), active_navigation="cartoes-resposta",
    )


@scanner_bp.get("/simulados/<assessment_id>/imprimir")
@roles_required(*ALLOWED_ROLES)
def print_cards(assessment_id):
    assessment = _assessment_or_404(assessment_id)
    try:
        manifest = question_manifest(assessment, QUESTIONS)
        scope, _ = _scope_selection(assessment, request.args)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("scanner.index", assessment_id=assessment_id))
    classes = {item["id"]: item for item in DATA["turmas"]}
    series = {item["id"]: item for item in DATA["series"]}
    institutions = {item["id"]: item for item in DATA["instituicoes"]}
    cards = []
    for student in eligible_students(assessment, scope):
        school_class = classes.get(student.get("turma_id"), {})
        school_series = series.get(school_class.get("serie_id"), {})
        sheet = issue_sheet(assessment_id, student["id"],
                            {"questions": manifest, "audience": student_audience(student)})
        cards.append({
            "sheet": sheet, "student": student, "school_class": school_class, "series": school_series,
            "institution": institutions.get(student["instituicao_id"], {}), "qr": _qr_data_uri(sheet["token"]),
        })
    rows = answer_rows(manifest)
    blocks = sorted({row["block"] for row in rows})
    block_letters = {
        block: list("ABCDE"[:max(len(row["options"]) for row in rows if row["block"] == block)])
        for block in blocks
    }
    return render_template(
        "scanner/print.html", assessment=assessment, cards=cards, rows=rows,
        blocks=blocks, block_letters=block_letters, question_count=len(manifest), scope=scope,
        marker_centers=MARKER_CENTERS_MM, marker_size=MARKER_SIZE_MM,
        bubble_radius=BUBBLE_RADIUS_MM, template_version=TEMPLATE_VERSION,
    )


def _process_page(batch, page_number, image, seen, previous):
    token, normalized, quality = prepare_page(image)
    root = current_app.config["SCAN_ROOT"]
    original_path = save_page(root, batch["id"], page_number, image)
    normalized_path = save_page(root, batch["id"], page_number, normalized, "aligned")
    values = {
        "page_number": page_number, "answer_sheet_id": None, "student_id": None,
        "status": "Falha", "image_path": normalized_path, "detected_answers": {}, "confidence": 0,
        "issue": "", "analysis": {"original_path": original_path, "quality": quality},
    }
    sheet = sheet_for_token(token)
    if not sheet:
        values["issue"] = ("QR não foi lido. Digitalize novamente ou confira os dados impressos."
                           if not token else "QR inválido, não reconhecido ou cartão não emitido neste ambiente.")
        values["analysis"]["failure_reason"] = "qr_unreadable" if not token else "qr_invalid"
    elif sheet["assessment_id"] != batch["assessment_id"]:
        values["issue"] = "O cartão pertence a outro simulado."
    elif not matches_scope(sheet.get("snapshot", {}).get("audience", {}), batch["scope"]):
        values["issue"] = "O cartão não pertence à instituição, série/ano, turma ou ano letivo selecionado."
    elif sheet["id"] in seen:
        values["issue"] = "Cartão duplicado neste lote. Confira a outra página deste estudante."
    else:
        seen.add(sheet["id"])
        values.update({"answer_sheet_id": sheet["id"], "student_id": sheet["student_id"]})
        manifest = sheet.get("snapshot", {}).get("questions", [])
        if sheet["template_version"] != TEMPLATE_VERSION or not manifest:
            values["issue"] = "Modelo anterior de cartão. Gere um cartão atualizado antes de digitalizar."
        elif not quality["aligned"]:
            values.update({"status": "Revisão", "issue": _short_issue(quality["issues"])})
        else:
            answers, confidence, issues, diagnostics = analyze_answers(normalized, manifest)
            issues = quality["issues"] + issues
            if sheet["id"] in previous:
                issues.insert(0, "Este cartão já foi enviado em outro lote. Confira a duplicidade.")
            current = find_assessment(batch["assessment_id"])
            try:
                current_manifest = question_manifest(current, QUESTIONS)
            except ValueError:
                current_manifest = []
            if current_manifest != manifest:
                issues.insert(0, "A composição do simulado mudou após a emissão. A leitura usa as questões originais do cartão.")
            blocking_states = {"duvidosa", "multipla", "desalinhada"}
            requires_review = (bool(quality["issues"]) or sheet["id"] in previous
                               or current_manifest != manifest
                               or any(item["state"] in blocking_states for item in diagnostics.values())
                               or confidence < .80)
            overlay_path = save_page(root, batch["id"], page_number,
                                     annotated_page(normalized, diagnostics, answers), "reading")
            values.update({
                "status": "Revisão" if requires_review else "Lido",
                "detected_answers": answers, "confidence": confidence, "issue": _short_issue(issues),
            })
            values["analysis"].update({
                "issues": issues, "questions": diagnostics, "manifest": manifest,
                "overlay_path": overlay_path, "original_answers": dict(answers),
            })
    add_batch_page(batch["id"], values)


@scanner_bp.post("/simulados/<assessment_id>/enviar")
@roles_required(*ALLOWED_ROLES)
def upload_batch(assessment_id):
    check_csrf()
    assessment = _assessment_or_404(assessment_id)
    uploaded = request.files.get("scan_file")
    try:
        if not uploaded or not uploaded.filename:
            raise ValueError("Selecione um PDF ou uma imagem para iniciar a leitura.")
        scope, _ = _scope_selection(assessment, request.form)
        question_manifest(assessment, QUESTIONS)
        data, extension = validate_upload(uploaded, current_app.config["SCAN_UPLOAD_MAX_BYTES"])
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("scanner.index", assessment_id=assessment_id))
    previous = {page["answer_sheet_id"] for item in list_batches() if _can_access_batch(item)
                for page in item["pages"] if page.get("answer_sheet_id") and page["status"] not in {"Falha", "Ignorada"}}
    batch = create_batch(assessment_id, uploaded.filename, current_profile(), scope)
    seen = set()
    try:
        for page_number, image in iter_upload_pages(
            data, extension, current_app.config["SCAN_MAX_PAGES"], current_app.config["SCAN_MAX_PIXELS"],
        ):
            _process_page(batch, page_number, image, seen, previous)
        finish_batch(batch["id"])
        flash("Digitalização processada. Confira as páginas sinalizadas para revisão.", "success")
    except (ValueError, RuntimeError, cv2.error, pypdfium2.PdfiumError) as exc:
        current_app.logger.warning("Scanner batch %s failed: %s", batch["id"], exc)
        finish_batch(batch["id"], "Não foi possível concluir o arquivo. Confira o formato, as páginas e a resolução e envie novamente.")
        flash("O lote não foi concluído. As páginas já lidas foram preservadas para conferência.", "danger")
    return redirect(url_for("scanner.batch_detail", batch_id=batch["id"]))


@scanner_bp.get("/lotes/<batch_id>")
@roles_required(*ALLOWED_ROLES)
def batch_detail(batch_id):
    batch = _batch_or_404(batch_id)
    students = {item["id"]: item for item in DATA["alunos"]}
    return render_template(
        "scanner/batch.html", page_title=f"Lote {batch['original_name']}",
        batch={**batch, "pages": [{**item, "student": students.get(item.get("student_id"))} for item in batch["pages"]]},
        assessment=find_assessment(batch["assessment_id"]), active_navigation="cartoes-resposta",
    )


@scanner_bp.get("/lotes/<batch_id>/resultados")
@roles_required(*ALLOWED_ROLES)
def batch_results(batch_id):
    batch = _batch_or_404(batch_id)
    assessment = _assessment_or_404(batch["assessment_id"])
    preview = preview_results(batch, assessment, QUESTIONS)
    return render_template(
        "scanner/results.html", page_title="Prévia das notas", batch=batch,
        assessment=assessment, preview=preview, csrf_token=csrf_token(),
        accessible_batch_ids={item["id"] for item in list_batches() if _can_access_batch(item)},
        active_navigation="cartoes-resposta",
    )


@scanner_bp.post("/lotes/<batch_id>/paginas/<page_id>/decidir")
@roles_required(*ALLOWED_ROLES)
def page_decision(batch_id, page_id):
    check_csrf()
    batch = _batch_or_404(batch_id)
    page = next((item for item in batch["pages"] if item["id"] == page_id), None)
    if not page or page["status"] == "Lançado":
        abort(404)
    action = request.form.get("action", "")
    analysis = dict(page.get("analysis") or {})
    events = list(analysis.get("result_decisions", []))
    event = {"action": action, "reviewer": current_profile().get("account_id", "global"),
             "at": datetime.now(UTC).isoformat()}
    status, issue = page["status"], page["issue"]
    if action == "ignore" and status in {"Falha", "Revisão", *READY_STATES}:
        reason = request.form.get("reason", "")
        if reason not in {"Duplicata", "Nova digitalização", "Página inválida"} or request.form.get("confirm_decision") != "yes":
            abort(400)
        analysis["ignored_previous"] = {"status": status, "issue": issue}
        analysis.pop("result_choice", None)
        status, issue = "Ignorada", f"Desconsiderada: {reason}."
        event["reason"] = reason
    elif action == "restore" and status == "Ignorada":
        previous = analysis.get("ignored_previous", {})
        if previous.get("status") not in {"Falha", "Revisão", *READY_STATES}:
            abort(400)
        status, issue = previous["status"], previous.get("issue", "")
        analysis.pop("ignored_previous", None)
    elif action in {"keep_online", "use_card"} and status in READY_STATES and current_app.config["DATABASE_ENABLED"] and page.get("student_id"):
        attempt = current_attempt(batch["assessment_id"], page["student_id"])
        if not attempt or attempt.id != request.form.get("attempt_id") or request.form.get("confirm_decision") != "yes":
            abort(400)
        event["attempt_id"] = attempt.id
        if action == "keep_online":
            analysis["ignored_previous"] = {"status": status, "issue": issue}
            analysis.pop("result_choice", None)
            status, issue = "Ignorada", "Desconsiderada: tentativa anterior mantida."
        else:
            analysis["result_choice"] = {"decision": "use_card", "attempt_id": attempt.id,
                                         "reviewer": event["reviewer"], "at": event["at"]}
    else:
        abort(400)
    events.append(event)
    analysis["result_decisions"] = events
    try:
        decide_page(batch_id, page_id, status, analysis, issue, expected_status=page["status"])
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("scanner.batch_results", batch_id=batch_id))
    flash("Decisão registrada para esta página.", "success")
    return redirect(url_for("scanner.batch_results", batch_id=batch_id))


@scanner_bp.post("/lotes/<batch_id>/resultados/lancar")
@roles_required(*ALLOWED_ROLES)
def launch_batch_results(batch_id):
    check_csrf()
    batch = _batch_or_404(batch_id)
    if request.form.get("confirm_launch") != "yes":
        abort(400)
    assessment = _assessment_or_404(batch["assessment_id"])
    try:
        count = publish_results(batch_id, assessment, QUESTIONS, current_profile(),
                                missing_acknowledged=request.form.get("confirm_missing") == "yes")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("scanner.batch_results", batch_id=batch_id))
    flash(f"{count} resultado{'s' if count != 1 else ''} lançado{'s' if count != 1 else ''} e aluno{'s' if count != 1 else ''} notificado{'s' if count != 1 else ''}.", "success")
    return redirect(url_for("scanner.batch_results", batch_id=batch_id))


@scanner_bp.route("/lotes/<batch_id>/paginas/<page_id>/identificar", methods=["GET", "POST"])
@roles_required(*ALLOWED_ROLES)
def identify_failed_page(batch_id, page_id):
    batch = _batch_or_404(batch_id)
    page = next((item for item in batch["pages"] if item["id"] == page_id), None)
    if (not page or page["status"] != "Falha"
            or page.get("analysis", {}).get("failure_reason") != "qr_unreadable"
            or not page.get("analysis", {}).get("quality", {}).get("aligned")):
        abort(404)

    assessment = find_assessment(batch["assessment_id"])
    eligible = {item["id"]: item for item in eligible_students(assessment, batch["scope"])}
    sheets_by_student = {}
    for sheet in find_sheets(batch["assessment_id"]):
        sheets_by_student.setdefault(sheet["student_id"], []).append(sheet)
    used_sheet_ids = {other["answer_sheet_id"] for item in list_batches() for other in item["pages"]
                      if other["id"] != page_id and other.get("answer_sheet_id") and other["status"] != "Falha"}
    candidates = {}
    for student_id, student in eligible.items():
        sheets = sheets_by_student.get(student_id, [])
        if len(sheets) != 1:
            continue
        sheet = sheets[0]
        snapshot = sheet.get("snapshot", {})
        if (sheet["template_version"] == TEMPLATE_VERSION and sheet["id"] not in used_sheet_ids
                and snapshot.get("questions") and matches_scope(snapshot.get("audience", {}), batch["scope"])):
            candidates[student_id] = (student, sheet)

    if request.method == "POST":
        check_csrf()
        selected = candidates.get(request.form.get("student_id", ""))
        enrollment = request.form.get("enrollment", "").strip()
        if not selected or not enrollment or enrollment != selected[0].get("matricula"):
            flash("Selecione o aluno e digite a matrícula exatamente como está no cartão.", "danger")
        elif request.form.get("confirm_identity") != "yes":
            flash("Confirme que nome, matrícula e simulado correspondem ao cartão.", "danger")
        else:
            sheet = selected[1]
            root = Path(current_app.config["SCAN_ROOT"]).resolve()
            image_path = (root / page["image_path"]).resolve()
            if root not in image_path.parents or not image_path.is_file():
                abort(404)
            image = cv2.imread(str(image_path))
            if image is None:
                abort(404)
            manifest = sheet["snapshot"]["questions"]
            answers, confidence, issues, diagnostics = analyze_answers(image, manifest)
            overlay_path = save_page(root, batch_id, page["page_number"],
                                     annotated_page(image, diagnostics, answers), "reading")
            analysis = dict(page["analysis"])
            analysis.update({"issues": page["analysis"]["quality"]["issues"] + issues,
                             "questions": diagnostics, "manifest": manifest})
            try:
                identify_page(batch_id, page_id, sheet, answers, confidence, analysis, overlay_path, current_profile())
            except ValueError as exc:
                flash(str(exc), "danger")
                return redirect(url_for("scanner.batch_detail", batch_id=batch_id))
            flash("Estudante identificado. Confira todas as respostas antes de lançar o resultado.", "success")
            return redirect(url_for("scanner.page_review", batch_id=batch_id, page_id=page_id))

    return render_template(
        "scanner/identify.html", page_title="Identificar cartão", batch=batch, page=page,
        assessment=assessment, candidates=[item[0] for item in candidates.values()],
        csrf_token=csrf_token(), active_navigation="cartoes-resposta",
    )


def _page_with_manifest(batch_id, page_id, statuses):
    batch = _batch_or_404(batch_id)
    page = next((item for item in batch["pages"] if item["id"] == page_id), None)
    if not page or not page.get("answer_sheet_id") or page["status"] not in statuses:
        abort(404)
    sheet = get_sheet(page["answer_sheet_id"])
    manifest = sheet.get("snapshot", {}).get("questions", []) if sheet else []
    if not manifest:
        abort(404)
    return batch, page, manifest


def _submitted_answers(manifest):
    answers = {str(question["number"]): request.form.get(f"answer_{question['number']}", "") for question in manifest}
    if any(answers[str(question["number"])] not in ["", *question["options"]] for question in manifest):
        abort(400, "Alternativa inválida.")
    return answers


def _render_review(batch, page, manifest, **context):
    student = next((item for item in DATA["alunos"] if item["id"] == page["student_id"]), None)
    return render_template(
        "scanner/review.html", batch=batch, page=page, student=student, manifest=manifest,
        csrf_token=csrf_token(), active_navigation="cartoes-resposta", **context,
    )


@scanner_bp.route("/lotes/<batch_id>/paginas/<page_id>/revisar", methods=["GET", "POST"])
@roles_required(*ALLOWED_ROLES)
def page_review(batch_id, page_id):
    batch, page, manifest = _page_with_manifest(batch_id, page_id, REVIEWABLE_STATES)
    if request.method == "POST":
        check_csrf()
        answers = _submitted_answers(manifest)
        if request.form.get("confirm_review") != "yes":
            flash("Confirme que comparou as respostas com a digitalização.", "danger")
        else:
            try:
                review_page(batch_id, page_id, answers, current_profile())
            except ValueError as exc:
                flash(str(exc), "danger")
                return redirect(url_for("scanner.batch_detail", batch_id=batch_id))
            flash("Respostas conferidas. A leitura original permanece no histórico.", "success")
            return redirect(url_for("scanner.batch_detail", batch_id=batch_id))
    return _render_review(batch, page, manifest, page_title="Conferir cartão")


@scanner_bp.route("/lotes/<batch_id>/paginas/<page_id>/retificar", methods=["GET", "POST"])
@roles_required(*ALLOWED_ROLES)
def page_rectify(batch_id, page_id):
    """Fix a misread card after its result was published; the old grade stays in the history."""
    batch, page, manifest = _page_with_manifest(batch_id, page_id, {"Lançado"})
    selected, reason = page["detected_answers"], ""
    if request.method == "POST":
        check_csrf()
        selected, reason = _submitted_answers(manifest), request.form.get("reason", "")
        if request.form.get("confirm_review") != "yes":
            flash("Confirme que comparou as respostas com a digitalização.", "danger")
        else:
            try:
                correction = rectify_paper_page(batch_id, page_id, selected, reason, current_profile())
            except ValueError as exc:
                flash(str(exc), "danger")
            else:
                before, after = correction.details["objective"]
                flash(f"Resultado retificado: {before:g} → {after:g} acertos. O aluno foi avisado."
                      if before != after else "Respostas retificadas. A nota não mudou.", "success")
                return redirect(url_for("scanner.batch_results", batch_id=batch_id) + f"#pagina-{page['page_number']}")
    return _render_review(batch, page, manifest, page_title="Retificar resultado", rectify=True,
                          selected=selected, reason=reason)


@scanner_bp.get("/lotes/<batch_id>/paginas/<page_id>/imagem")
@roles_required(*ALLOWED_ROLES)
def batch_page_image(batch_id, page_id):
    batch = _batch_or_404(batch_id)
    page = next((item for item in batch["pages"] if item["id"] == page_id), None)
    if not page:
        abort(404)
    variants = {"original": "original_path", "reading": "overlay_path"}
    path = page.get("analysis", {}).get(variants.get(request.args.get("variant"), "")) or page["image_path"]
    root = Path(current_app.config["SCAN_ROOT"]).resolve()
    candidate = (root / path).resolve()
    if root not in candidate.parents or not candidate.is_file():
        abort(404)
    response = send_file(candidate, mimetype="image/png" if candidate.suffix == ".png" else "image/jpeg")
    response.headers["Cache-Control"] = "private, no-store"
    return response
