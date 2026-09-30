from flask import abort, current_app, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from . import materials_bp
from ..auth.security import current_profile, roles_required
from ..data.academic import DATA, find
from ..data.curriculum import SUBJECTS, TOPICS, subject_name, topic_name
from ..data.materials import (
    ALLOWED_ATTACHMENT_EXTENSIONS,
    MATERIAL_POSTS,
    add_material,
    attachment_extension,
    delete_material,
    find_material,
    update_material,
)
from ..data.notifications import add_notification
from ..storage import absolute_file_path, delete_stored_file, save_uploaded_file, stored_file


def teacher_record():
    return find("professores", current_profile()["teacher_id"])


def teacher_posts():
    teacher_id = current_profile()["teacher_id"]
    return [item for item in MATERIAL_POSTS if item["professor_id"] == teacher_id]


def enrich_material(material):
    item = dict(material)
    teacher = find("professores", material["professor_id"])
    item["professor"] = teacher["nome"] if teacher else "Professor"
    item["materia"] = subject_name(material["materia_id"])
    item["assunto"] = topic_name(material["assunto_id"])
    item["turmas"] = [find("turmas", class_id) for class_id in material["turma_ids"]]
    return item


def material_form_options(teacher):
    subjects = [item for item in SUBJECTS if item["id"] in teacher.get("disciplina_ids", [])]
    subject_ids = {item["id"] for item in subjects}
    topics = [item for item in TOPICS if item["materia_id"] in subject_ids]
    classes = [find("turmas", class_id) for class_id in teacher.get("turma_ids", []) if find("turmas", class_id)]
    return subjects, subject_ids, topics, classes


def uploaded_attachment(owner_id):
    uploaded = request.files.get("anexo")
    if not uploaded or not uploaded.filename:
        return None, None
    filename = secure_filename(uploaded.filename)
    extension = attachment_extension(filename)
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return None, "O anexo deve estar em PDF, PNG, PPT ou PPTX."
    try:
        return save_uploaded_file(
            uploaded, "material", owner_id, ALLOWED_ATTACHMENT_EXTENSIONS,
            current_app.config["MAX_CONTENT_LENGTH"],
        ), None
    except ValueError as error:
        return None, str(error)


@materials_bp.get("/")
@roles_required("teacher")
def index():
    return render_template(
        "materials/index.html",
        page_title="Materiais de revisão",
        materials=[enrich_material(item) for item in teacher_posts()],
        active_navigation="materiais",
    )


@materials_bp.route("/novo", methods=["GET", "POST"])
@roles_required("teacher")
def create():
    teacher = teacher_record()
    subjects, subject_ids, topics, classes = material_form_options(teacher)
    values = request.form
    selected_classes = request.form.getlist("turma_ids")
    error = None

    if request.method == "POST":
        title = request.form.get("titulo", "").strip()
        description = request.form.get("descricao", "").strip()
        text = request.form.get("texto", "").strip()
        subject_id = request.form.get("materia_id", "")
        topic_id = request.form.get("assunto_id", "")
        selected_classes = [item for item in selected_classes if item in teacher.get("turma_ids", [])]
        topic = next((item for item in topics if item["id"] == topic_id and item["materia_id"] == subject_id), None)
        uploaded = request.files.get("anexo")
        attachment_present = bool(uploaded and uploaded.filename)
        extension = attachment_extension(uploaded.filename) if attachment_present else ""
        if attachment_present and extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
            error = "O anexo deve estar em PDF, PNG, PPT ou PPTX."

        if not error and (not title or not description or subject_id not in subject_ids or not topic or not selected_classes):
            error = "Preencha título, descrição, matéria, assunto e ao menos uma turma."
        if not error and not text and not attachment_present:
            error = "Inclua um texto ou um anexo para publicar o material."

        if not error:
            material = add_material({
                "titulo": title,
                "descricao": description,
                "texto": text,
                "professor_id": teacher["id"],
                "materia_id": subject_id,
                "assunto_id": topic_id,
                "turma_ids": selected_classes,
                "anexo": None,
            })
            if attachment_present:
                attachment, error = uploaded_attachment(material["id"])
                if error:
                    delete_material(material["id"])
                    return render_template("materials/form.html", page_title="Publicar material", subjects=subjects, topics=topics, classes=classes, values=values, selected_classes=selected_classes, material=None, error=error, active_navigation="materiais"), 400
                material["anexo"] = attachment
            for student in DATA["alunos"]:
                if student["turma_id"] in selected_classes:
                    add_notification(student["id"], "Novo material para sua turma", title, url_for("student_area.review"), "material")
            flash("Material publicado para as turmas selecionadas.", "success")
            return redirect(url_for("materials.index"))

    return render_template(
        "materials/form.html",
        page_title="Publicar material",
        subjects=subjects,
        topics=topics,
        classes=classes,
        values=values,
        selected_classes=selected_classes,
        material=None,
        error=error,
        active_navigation="materiais",
    ), 400 if error else 200


@materials_bp.route("/<material_id>/editar", methods=["GET", "POST"])
@roles_required("teacher")
def edit(material_id):
    teacher = teacher_record()
    material = find_material(material_id)
    if not material:
        abort(404)
    if material["professor_id"] != teacher["id"]:
        abort(403)

    subjects, subject_ids, topics, classes = material_form_options(teacher)
    values = request.form if request.method == "POST" else material
    selected_classes = request.form.getlist("turma_ids") if request.method == "POST" else material["turma_ids"]
    error = None

    if request.method == "POST":
        title = request.form.get("titulo", "").strip()
        description = request.form.get("descricao", "").strip()
        text = request.form.get("texto", "").strip()
        subject_id = request.form.get("materia_id", "")
        topic_id = request.form.get("assunto_id", "")
        selected_classes = [item for item in selected_classes if item in teacher.get("turma_ids", [])]
        topic = next((item for item in topics if item["id"] == topic_id and item["materia_id"] == subject_id), None)
        old_attachment = material.get("anexo")
        uploaded = request.files.get("anexo")
        attachment_present = bool(uploaded and uploaded.filename)
        attachment = old_attachment
        extension = attachment_extension(uploaded.filename) if attachment_present else ""
        if attachment_present and extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
            error = "O anexo deve estar em PDF, PNG, PPT ou PPTX."
        elif request.form.get("remover_anexo"):
            attachment = None

        if not error and (not title or not description or subject_id not in subject_ids or not topic or not selected_classes):
            error = "Preencha título, descrição, matéria, assunto e ao menos uma turma."
        if not error and not text and not attachment:
            error = "Inclua um texto ou um anexo para salvar o material."

        if not error:
            if attachment_present:
                attachment, error = uploaded_attachment(material_id)
            if error:
                return render_template("materials/form.html", page_title="Editar publicação", subjects=subjects, topics=topics, classes=classes, values=values, selected_classes=selected_classes, material=material, error=error, active_navigation="materiais"), 400
            update_material(material_id, {
                "titulo": title,
                "descricao": description,
                "texto": text,
                "materia_id": subject_id,
                "assunto_id": topic_id,
                "turma_ids": selected_classes,
                "anexo": attachment,
            })
            if old_attachment and old_attachment != attachment:
                delete_stored_file(old_attachment["arquivo_id"])
            flash("Publicação atualizada.", "success")
            return redirect(url_for("materials.index"))

    return render_template(
        "materials/form.html",
        page_title="Editar publicação",
        subjects=subjects,
        topics=topics,
        classes=classes,
        values=values,
        selected_classes=selected_classes,
        material=material,
        error=error,
        active_navigation="materiais",
    ), 400 if error else 200


@materials_bp.post("/<material_id>/excluir")
@roles_required("teacher")
def delete(material_id):
    material = find_material(material_id)
    if not material:
        abort(404)
    if material["professor_id"] != current_profile()["teacher_id"]:
        abort(403)
    if material.get("anexo"):
        delete_stored_file(material["anexo"]["arquivo_id"])
    delete_material(material_id)
    flash("Publicação excluída.", "success")
    return redirect(url_for("materials.index"))


@materials_bp.get("/<material_id>/anexo")
@roles_required("student", "teacher")
def attachment(material_id):
    material = find_material(material_id)
    if not material or not material.get("anexo"):
        abort(404)
    profile = current_profile()
    if profile["key"] == "teacher" and material["professor_id"] != profile["teacher_id"]:
        abort(403)
    if profile["key"] == "student":
        student = find("alunos", profile["student_id"])
        if student["turma_id"] not in material["turma_ids"]:
            abort(403)
    attachment_data = material["anexo"]
    record = stored_file(attachment_data["arquivo_id"])
    if not record:
        abort(404)
    return send_file(
        absolute_file_path(record),
        mimetype=record.mime_type,
        download_name=record.original_name,
        as_attachment=False,
    )
