from flask import abort, flash, redirect, render_template, request, url_for

from . import curriculum_bp
from ..auth.security import current_profile, login_required
from ..data.academic import DATA, enrich
from ..data.curriculum import (
    SUBJECTS,
    TOPICS,
    add_subject,
    add_topic,
    delete_topic,
    find_subject,
    find_topic,
    subjects_for_profile,
    update_topic,
)


CURRICULUM_ROLES = {"teacher", "school_coordinator", "institute_coordinator"}


def ensure_access():
    profile = current_profile()
    if profile["key"] not in CURRICULUM_ROLES:
        abort(403)
    return profile


def subject_in_scope(profile, subject):
    if profile["key"] == "institute_coordinator":
        return True
    if profile["key"] == "teacher":
        return subject["id"] in {item["id"] for item in subjects_for_profile(profile)}
    return False


def topic_in_scope(profile, topic):
    subject = find_subject(topic["materia_id"]) if topic else None
    return bool(subject and subject_in_scope(profile, subject))


def topic_is_used(topic_id):
    from ..data.materials import MATERIAL_POSTS
    from ..data.questions import QUESTIONS

    return any(item.get("assunto_id") == topic_id for item in QUESTIONS) or any(
        item.get("assunto_id") == topic_id for item in MATERIAL_POSTS
    )


@curriculum_bp.get("")
@login_required
def index():
    profile = ensure_access()
    subjects = []
    for subject in subjects_for_profile(profile):
        item = dict(subject)
        institution = next((record for record in DATA["instituicoes"] if record["id"] == subject.get("instituicao_id")), None)
        item["instituicao"] = institution["nome"] if institution else "Todas as instituições"
        item["assuntos"] = [topic for topic in TOPICS if topic["materia_id"] == subject["id"]]
        item["can_manage_topics"] = subject_in_scope(profile, subject)
        subjects.append(item)
    return render_template(
        "curriculum/index.html",
        page_title="Matérias e assuntos",
        subjects=subjects,
        can_add_topic=any(item["can_manage_topics"] for item in subjects),
        can_add_subject=profile["key"] in {"school_coordinator", "institute_coordinator"},
        is_teacher=profile["key"] == "teacher",
        active_navigation="curriculo",
    )


@curriculum_bp.route("/materias/nova", methods=["GET", "POST"])
@login_required
def create_subject():
    profile = ensure_access()
    if profile["key"] == "teacher":
        abort(403)
    institutions = [enrich("instituicoes", item) for item in DATA["instituicoes"]]
    if profile["key"] == "school_coordinator":
        institutions = [item for item in institutions if item["id"] == profile["institution_id"]]
    if request.method == "POST":
        nome = request.form.get("nome", "").strip() or "Nova matéria"
        if profile["key"] == "school_coordinator":
            escopo = "instituicao"
            institution_id = profile["institution_id"]
        elif profile["key"] == "institute_coordinator":
            escopo = "global"
            institution_id = ""
        subject = add_subject(nome, escopo, institution_id, profile["name"])
        flash(f"Matéria {subject['nome']} adicionada ao catálogo.", "success")
        return redirect(url_for("curriculum.index"))
    return render_template(
        "curriculum/subject_form.html",
        page_title="Nova matéria",
        institutions=institutions,
        fixed_scope="instituicao" if profile["key"] == "school_coordinator" else ("global" if profile["key"] == "institute_coordinator" else ""),
        active_navigation="curriculo",
    )


@curriculum_bp.route("/assuntos/novo", methods=["GET", "POST"])
@login_required
def create_topic():
    profile = ensure_access()
    if profile["key"] == "school_coordinator":
        abort(403)
    subjects = subjects_for_profile(profile)
    if profile["key"] == "teacher":
        subjects = [item for item in subjects if subject_in_scope(profile, item)]
    if request.method == "POST":
        subject_id = request.form.get("materia_id", "")
        subject = find_subject(subject_id)
        if not subject or not subject_in_scope(profile, subject):
            abort(403)
        nome = request.form.get("nome", "").strip() or "Novo assunto"
        add_topic(nome, subject_id, profile["name"])
        flash(f"Assunto {nome} adicionado a {subject['nome']}.", "success")
        return redirect(url_for("curriculum.index"))
    return render_template("curriculum/topic_form.html", page_title="Novo assunto", subjects=subjects, topic=None, values=request.form, active_navigation="curriculo")


@curriculum_bp.route("/assuntos/<topic_id>/editar", methods=["GET", "POST"])
@login_required
def edit_topic(topic_id):
    profile = ensure_access()
    topic = find_topic(topic_id)
    if not topic:
        abort(404)
    if not topic_in_scope(profile, topic):
        abort(403)
    subject = find_subject(topic["materia_id"])
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            return render_template("curriculum/topic_form.html", page_title="Editar assunto", subjects=[subject], topic=topic, values=request.form, error="Informe o nome do assunto.", active_navigation="curriculo"), 400
        update_topic(topic_id, nome)
        flash(f"Assunto atualizado para {nome}.", "success")
        return redirect(url_for("curriculum.index"))
    return render_template("curriculum/topic_form.html", page_title="Editar assunto", subjects=[subject], topic=topic, values=topic, active_navigation="curriculo")


@curriculum_bp.post("/assuntos/<topic_id>/excluir")
@login_required
def remove_topic(topic_id):
    profile = ensure_access()
    topic = find_topic(topic_id)
    if not topic:
        abort(404)
    if not topic_in_scope(profile, topic):
        abort(403)
    if topic_is_used(topic_id):
        flash("Este assunto está vinculado a questões ou materiais e não pode ser excluído.", "danger")
        return redirect(url_for("curriculum.index"))
    name = topic["nome"]
    delete_topic(topic_id)
    flash(f"Assunto {name} excluído.", "success")
    return redirect(url_for("curriculum.index"))
