import math
from datetime import datetime
from flask import abort, current_app, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from . import questions_bp
from ..auth.security import current_profile, login_required
from ..data.questions import QUESTIONS, add_question, find_question, persist_question, update_question
from ..data.academic import DATA, find
from ..data.curriculum import TOPICS, find_subject, find_topic, subjects_for_profile
from ..storage import absolute_file_path, delete_stored_file, save_uploaded_file, stored_file
from ..data.notifications import add_role_notification
from ..data.reviews import actor_identity, add_review_event, review_history


ACCESS_ROLES = {"teacher", "school_coordinator", "institute_coordinator"}
MANAGE_ROLES = {"teacher"}
REVIEW_ROLES = {"school_coordinator", "institute_coordinator"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
IMAGE_MIME_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}


def ensure_access(manage=False):
    profile = current_profile()
    allowed = MANAGE_ROLES if manage else ACCESS_ROLES
    if profile["key"] not in allowed:
        abort(403)
    return profile


def question_in_scope(profile, question):
    if profile["key"] == "institute_coordinator":
        return True
    if profile["key"] == "teacher":
        return question.get("autor_id") == profile.get("teacher_id")
    return question.get("instituicao_id") == profile.get("institution_id")


def profile_institution_id(profile):
    if profile["key"] == "teacher":
        teacher = find("professores", profile["teacher_id"])
        return teacher["instituicao_id"] if teacher else ""
    return profile.get("institution_id", "")


def question_values(form, current=None):
    current = current or {}
    question_type = form.get("tipo", current.get("tipo", "objetiva"))
    if question_type not in {"objetiva", "aberta"}:
        abort(400)
    alternatives = {
        letter: form.get(f"alternativa_{letter.lower()}", "").strip() or current.get("alternativas", {}).get(letter, "")
        for letter in "ABCD"
    }
    materia_id = form.get("materia_id", current.get("materia_id", "mat-001"))
    assunto_id = form.get("assunto_id", current.get("assunto_id", "ass-001"))
    subject = find_subject(materia_id)
    topic = find_topic(assunto_id)
    allowed_subject_ids = {item["id"] for item in subjects_for_profile(current_profile())}
    if not subject or materia_id not in allowed_subject_ids or not topic or topic["materia_id"] != materia_id:
        abort(400)
    profile = current_profile()
    return {
        "materia_id": materia_id,
        "assunto_id": assunto_id,
        "disciplina": subject["nome"],
        "assunto": topic["nome"],
        "operacao": form.get("operacao", "Soma"),
        "dificuldade": form.get("dificuldade", "Fácil"),
        "enunciado": form.get("enunciado", "").strip() or current.get("enunciado", "Nova questão de Matemática"),
        "tipo": question_type,
        "alternativas": alternatives if question_type == "objetiva" else {},
        "gabarito": form.get("gabarito", "A") if question_type == "objetiva" else "",
        "resposta_esperada": form.get("resposta_esperada", "").strip(),
        "explicacao": form.get("explicacao", "").strip(),
        "autor": current.get("autor") or profile["name"],
        "autor_id": current.get("autor_id") or profile.get("teacher_id", ""),
        "instituicao_id": profile_institution_id(profile) or form.get("instituicao_id", current.get("instituicao_id", "")),
    }


def question_image(owner_id, current=None):
    current = current or {}
    if request.form.get("remover_imagem") == "1":
        if current.get("imagem"):
            delete_stored_file(current["imagem"]["arquivo_id"])
        return None
    uploaded = request.files.get("imagem")
    if not uploaded or not uploaded.filename:
        return current.get("imagem")
    filename = secure_filename(uploaded.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("A imagem deve estar em PNG, JPG, JPEG ou WEBP.")
    image = save_uploaded_file(
        uploaded, "question", owner_id, ALLOWED_IMAGE_EXTENSIONS,
        current_app.config["QUESTION_IMAGE_MAX_BYTES"],
    )
    if current.get("imagem"):
        delete_stored_file(current["imagem"]["arquivo_id"])
    return image


def question_form_context(profile, question, error=None):
    subjects = subjects_for_profile(profile)
    institution_id = profile_institution_id(profile)
    institutions = [item for item in DATA["instituicoes"] if item["id"] == institution_id]
    return {
        "question": question,
        "subjects": subjects,
        "topics": TOPICS,
        "institutions": institutions,
        "fixed_institution": True,
        "error": error,
        "active_navigation": "questoes",
    }


@questions_bp.get("")
@login_required
def list_questions():
    profile = ensure_access()
    records = [item for item in QUESTIONS if question_in_scope(profile, item)]
    query = request.args.get("q", "").strip().lower()
    operation = request.args.get("operacao", "")
    difficulty = request.args.get("dificuldade", "")
    revision = request.args.get("revisao", "")
    subject_id = request.args.get("materia_id", "")
    topic_id = request.args.get("assunto_id", "")
    subjects = subjects_for_profile(profile)
    allowed_subject_ids = {item["id"] for item in subjects}
    if subject_id and subject_id not in allowed_subject_ids:
        abort(403)
    topics = [item for item in TOPICS if item["materia_id"] in allowed_subject_ids]
    if not subject_id or not topic_id:
        records = []
    else:
        records = [item for item in records if item.get("materia_id") == subject_id and item.get("assunto_id") == topic_id]
    if query:
        records = [item for item in records if query in f"{item['enunciado']} {item['operacao']} {item['autor']}".lower()]
    if operation:
        records = [item for item in records if item["operacao"] == operation]
    if difficulty:
        records = [item for item in records if item["dificuldade"] == difficulty]
    if revision:
        if revision == "aguardando":
            records = [item for item in records if item.get("revisao_status") in {"Pendente", "Em revisão"}]
        else:
            records = [item for item in records if item.get("revisao_status") == revision]
    per_page = 6
    total = len(records)
    pages = max(1, math.ceil(total / per_page))
    page = min(max(request.args.get("page", 1, type=int), 1), pages)
    records = records[(page - 1) * per_page : page * per_page]
    return render_template(
        "questions/list.html",
        page_title="Banco de questões",
        records=records,
        can_create=profile["key"] == "teacher",
        can_edit=profile["key"] == "teacher",
        can_request_revision=profile["key"] in REVIEW_ROLES,
        curriculum_label="Gerir assuntos" if profile["key"] == "teacher" else "Gerir matérias",
        subjects=subjects,
        topics=topics,
        selected_subject=subject_id,
        selected_topic=topic_id,
        pagination={"page": page, "pages": pages, "total": total},
        query=request.args.get("q", ""),
        selected_operation=operation,
        selected_difficulty=difficulty,
        selected_revision=revision,
        active_navigation="questoes",
    )


@questions_bp.get("/<question_id>")
@login_required
def detail(question_id):
    profile = ensure_access()
    question = find_question(question_id)
    if not question:
        abort(404)
    if not question_in_scope(profile, question):
        abort(403)
    return render_template(
        "questions/detail.html",
        page_title=f"Questão {question_id.split('-')[-1]}",
        question=question,
        can_edit=profile["key"] == "teacher" and question_in_scope(profile, question),
        can_request_revision=profile["key"] in REVIEW_ROLES,
        review_history=review_history(question_id),
        active_navigation="questoes",
    )


@questions_bp.route("/nova", methods=["GET", "POST"])
@login_required
def create():
    profile = ensure_access(manage=True)
    assigned_subject_id = request.form.get("materia_id", "").strip() if request.method == "POST" else request.args.get("materia_id", "").strip()
    if request.method == "POST":
        values = question_values(request.form)
        question = add_question({**values, "imagem": None})
        try:
            question["imagem"] = question_image(question["id"])
            persist_question(question)
        except ValueError as error:
            from ..extensions import db
            from ..models import Question

            QUESTIONS.remove(question)
            model = db.session.get(Question, question["id"])
            if model:
                db.session.delete(model)
                db.session.commit()
            return render_template("questions/form.html", page_title="Nova questão", **question_form_context(profile, values, str(error))), 400
        flash("Questão salva no banco de dados.", "success")
        return redirect(url_for("questions.detail", question_id=question["id"]))
    return render_template("questions/form.html", page_title="Nova questão", **question_form_context(
        profile,
        {"instituicao_id": profile_institution_id(profile), "materia_id": assigned_subject_id},
    ))


@questions_bp.route("/<question_id>/editar", methods=["GET", "POST"])
@login_required
def edit(question_id):
    profile = ensure_access(manage=True)
    question = find_question(question_id)
    if not question:
        abort(404)
    if not question_in_scope(profile, question):
        abort(403)
    if request.method == "POST":
        values = question_values(request.form, question)
        try:
            values["imagem"] = question_image(question_id, question)
        except ValueError as error:
            values["imagem"] = question.get("imagem")
            return render_template("questions/form.html", page_title="Editar questão", **question_form_context(profile, values, str(error))), 400
        update_question(question_id, values)
        if question.get("revisao_status") in {"Pendente", "Em revisão", "Revisão solicitada"}:
            question["revisao_status"] = "Revisada"
            question["revisao_respondida_em"] = datetime.now().strftime("%d/%m/%Y às %H:%M")
            add_review_event(question_id, "Revisada", "Questão atualizada pelo professor.")
            recipient_role = question.get("revisao_solicitante_role", "school_coordinator")
            recipient_id = question.get("revisao_solicitante_id", question.get("instituicao_id", ""))
            add_role_notification(recipient_role, recipient_id, "Questão revisada", f"{question['autor']} reenviou a questão {question_id}.", url_for("questions.detail", question_id=question_id), "question_revised")
            from ..data.assessments import update_submissions_after_question_edit

            update_submissions_after_question_edit(question_id)
            persist_question(question)
        flash("Questão atualizada no banco de dados.", "success")
        return redirect(url_for("questions.detail", question_id=question_id))
    return render_template("questions/form.html", page_title="Editar questão", **question_form_context(profile, question))


@questions_bp.post("/<question_id>/solicitar-revisao")
@login_required
def request_revision(question_id):
    profile = current_profile()
    if profile["key"] not in REVIEW_ROLES:
        abort(403)
    question = find_question(question_id)
    if not question:
        abort(404)
    if not question_in_scope(profile, question):
        abort(403)
    observation = request.form.get("observacao", "").strip()
    if not observation:
        flash("Informe o que deve ser revisado na questão.", "danger")
        return redirect(url_for("questions.detail", question_id=question_id))
    question.update({
        "revisao_status": "Pendente",
        "revisao_observacao": observation,
        "revisao_solicitada_por": profile["name"],
        "revisao_solicitada_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        "revisao_solicitante_role": profile["key"],
        "revisao_solicitante_id": actor_identity(profile),
    })
    persist_question(question)
    add_review_event(question_id, "Pendente", observation)
    add_role_notification("teacher", question["autor_id"], "Revisão de questão solicitada", observation, url_for("questions.detail", question_id=question_id), "question_review")
    flash(f"Revisão solicitada ao professor {question['autor']}.", "success")
    return redirect(url_for("questions.detail", question_id=question_id))


@questions_bp.post("/<question_id>/iniciar-revisao")
@login_required
def start_revision(question_id):
    profile = ensure_access(manage=True)
    question = find_question(question_id)
    if not question or not question_in_scope(profile, question):
        abort(404 if not question else 403)
    if question.get("revisao_status") != "Pendente":
        abort(400)
    question["revisao_status"] = "Em revisão"
    persist_question(question)
    add_review_event(question_id, "Em revisão", "Professor iniciou os ajustes.")
    return redirect(url_for("questions.edit", question_id=question_id))


@questions_bp.post("/<question_id>/aprovar-revisao")
@login_required
def approve_revision(question_id):
    profile = current_profile()
    if profile["key"] not in REVIEW_ROLES:
        abort(403)
    question = find_question(question_id)
    if not question or not question_in_scope(profile, question):
        abort(404 if not question else 403)
    if question.get("revisao_status") != "Revisada":
        abort(400)
    question["revisao_status"] = "Aprovada"
    persist_question(question)
    add_review_event(question_id, "Aprovada", "Revisão aprovada pela coordenação.")
    add_role_notification("teacher", question["autor_id"], "Revisão aprovada", f"A revisão da questão {question_id} foi aprovada.", url_for("questions.detail", question_id=question_id), "review_approved")
    flash("Revisão aprovada.", "success")
    return redirect(url_for("questions.detail", question_id=question_id))


@questions_bp.get("/<question_id>/imagem")
@login_required
def image(question_id):
    question = find_question(question_id)
    if not question or not question.get("imagem"):
        abort(404)
    profile = current_profile()
    if profile["key"] == "student":
        from ..data.assessments import ASSESSMENTS

        student = next(item for item in DATA["alunos"] if item["id"] == profile["student_id"])
        school_class = find("turmas", student["turma_id"])
        allowed = any(
            item["status"] in {"Publicado", "Agendado"}
            and student["instituicao_id"] in item.get("instituicao_ids", [])
            and (not item.get("serie_ids") or school_class["serie_id"] in item["serie_ids"])
            and question_id in item.get("question_ids", [])
            for item in ASSESSMENTS
        )
        if not allowed:
            abort(403)
    elif profile["key"] not in ACCESS_ROLES or not question_in_scope(profile, question):
        abort(403)
    image_data = question["imagem"]
    record = stored_file(image_data["arquivo_id"])
    if not record:
        abort(404)
    return send_file(absolute_file_path(record), mimetype=record.mime_type, download_name=record.original_name, as_attachment=False)
