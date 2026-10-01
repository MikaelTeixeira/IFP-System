import math
import unicodedata

from flask import abort, flash, redirect, render_template, request, url_for

from . import academic_bp
from .permissions import can_access, can_manage, record_in_scope, scoped_records
from ..auth.security import current_profile, login_required
from ..data.academic import (
    DATA,
    ENTITY_CONFIG,
    add_record,
    delete_record,
    enrich,
    find,
    find_identity_conflict,
    normalize_cpf,
    normalize_email,
    toggle_record,
    update_record,
)
from ..data.curriculum import SUBJECTS, subjects_for_profile


FIELD_LABELS = {
    "nome": "Nome",
    "uf": "UF",
    "codigo": "Código",
    "municipio_id": "Município",
    "instituicao_id": "Instituição",
    "serie_id": "Série",
    "turma_id": "Turma",
    "ano_letivo": "Ano letivo",
    "turno": "Turno",
    "matricula": "Matrícula",
    "ingresso": "Data de ingresso",
    "cpf": "CPF",
    "email": "E-mail",
    "disciplina_ids": "Disciplinas aprovadas",
}

FIELD_HELP = {
    "codigo": "identificador oficial do município, como o código IBGE",
    "cpf": "somente um cadastro pode usar este CPF",
    "email": "somente um cadastro pode usar este e-mail",
    "disciplina_ids": "selecione uma ou mais matérias do catálogo aprovado",
}

OPTION_ENTITIES = {
    "municipio_id": "municipios",
    "instituicao_id": "instituicoes",
    "serie_id": "series",
    "turma_id": "turmas",
}


def entity_or_404(entity):
    config = ENTITY_CONFIG.get(entity)
    if not config:
        abort(404)
    return config


def ensure_access(entity, item_id=None, manage=False):
    profile = current_profile()
    if not can_access(profile, entity):
        abort(403)
    if manage and not can_manage(profile, entity):
        abort(403)
    if item_id and not record_in_scope(profile, entity, item_id):
        abort(403)
    return profile


def form_options(profile, config):
    options = {}
    for field in config["fields"]:
        option_entity = OPTION_ENTITIES.get(field)
        if option_entity:
            source = scoped_records(profile, option_entity) if can_access(profile, option_entity) else DATA[option_entity]
            options[field] = [enrich(option_entity, item) for item in source]
        elif field == "disciplina_ids":
            options[field] = subjects_for_profile(profile)
    return options


def form_values(entity, config, profile):
    values = {}
    for field in config["fields"]:
        if field == "disciplina_ids":
            values[field] = request.form.getlist(field)
        else:
            values[field] = request.form.get(field, "").strip()
    if "cpf" in values:
        values["cpf"] = normalize_cpf(values["cpf"])
    if "email" in values:
        values["email"] = normalize_email(values["email"])
    if profile["key"] == "school_coordinator" and entity in {"series", "turmas", "alunos", "professores"}:
        values["instituicao_id"] = profile["institution_id"]
    return values


def identity_error(values, exclude_id=None):
    field, record = find_identity_conflict(values.get("cpf", ""), values.get("email", ""), exclude_id)
    if not field:
        return None
    label = "CPF" if field == "cpf" else "E-mail"
    return f"{label} já cadastrado para {record['nome']}. Informe um dado diferente."


def relationship_error(entity, values):
    institution_id = values.get("instituicao_id", "")
    if entity == "instituicoes" and not find("municipios", values.get("municipio_id")):
        return "Selecione um município válido."
    if entity in {"series", "turmas", "alunos", "professores"} and not find("instituicoes", institution_id):
        return "Selecione uma instituição válida."
    if entity == "turmas":
        series = find("series", values.get("serie_id"))
        if not series or series.get("instituicao_id") != institution_id:
            return "A série selecionada deve pertencer à mesma instituição da turma."
    if entity == "alunos":
        school_class = find("turmas", values.get("turma_id"))
        if not school_class or school_class.get("instituicao_id") != institution_id:
            return "A turma selecionada deve pertencer à mesma instituição do aluno."
    if entity == "professores":
        allowed = {
            subject["id"] for subject in SUBJECTS
            if subject.get("escopo") == "global" or subject.get("instituicao_id") == institution_id
        }
        if any(subject_id not in allowed for subject_id in values.get("disciplina_ids", [])):
            return "Selecione apenas matérias globais ou pertencentes à instituição do professor."
    return None


def deletion_blocker(entity, item_id):
    from ..data.assessments import ASSESSMENTS, ASSESSMENT_REQUESTS
    from ..data.materials import MATERIAL_POSTS
    from ..data.questions import QUESTIONS
    from ..data.users import list_users
    from ..extensions import db
    from ..models import AssessmentAttempt, AttemptAnswer, ReportSnapshot, StudentAttendanceSummary

    if entity == "municipios":
        if any(item.get("municipio_id") == item_id for item in DATA["instituicoes"] + list_users()):
            return "possui instituições ou usuários vinculados"
    elif entity == "instituicoes":
        related = any(
            item.get("instituicao_id") == item_id
            for group in (DATA["series"], DATA["turmas"], DATA["alunos"], DATA["professores"], SUBJECTS, QUESTIONS, list_users())
            for item in group
        )
        related = related or any(item_id in item.get("instituicao_ids", []) for item in ASSESSMENTS)
        related = related or any(item.get("instituicao_id") == item_id for item in ASSESSMENT_REQUESTS)
        related = related or db.session.get(ReportSnapshot, item_id) is not None
        related = related or StudentAttendanceSummary.query.filter_by(institution_id=item_id).first() is not None
        if related:
            return "possui estrutura acadêmica, usuários ou avaliações vinculadas"
    elif entity == "series":
        related = any(item.get("serie_id") == item_id for item in DATA["turmas"])
        related = related or any(item_id in item.get("serie_ids", []) for item in ASSESSMENTS + ASSESSMENT_REQUESTS)
        if related:
            return "possui turmas, solicitações ou simulados vinculados"
    elif entity == "turmas":
        related = any(item.get("turma_id") == item_id for item in DATA["alunos"])
        related = related or any(item_id in item.get("turma_ids", []) for item in DATA["professores"] + MATERIAL_POSTS)
        if related:
            return "possui estudantes, professores ou materiais vinculados"
    elif entity == "alunos":
        record = find("alunos", item_id)
        related = bool(record.get("_user_account_id"))
        related = related or AssessmentAttempt.query.filter_by(student_id=item_id).first() is not None
        if related:
            return "possui acesso de usuário ou tentativas vinculadas; exclua primeiro o acesso quando aplicável"
    elif entity == "professores":
        record = find("professores", item_id)
        related = bool(record.get("_user_account_id"))
        related = related or any(item.get("autor_id") == item_id for item in QUESTIONS)
        related = related or any(item.get("professor_id") == item_id for item in MATERIAL_POSTS)
        related = related or any(
            assignment.get("professor_id") == item_id
            for assessment_request in ASSESSMENT_REQUESTS
            for assignment in assessment_request.get("atribuicoes", [])
        )
        related = related or AttemptAnswer.query.filter_by(grader_id=item_id).first() is not None
        if related:
            return "possui acesso, questões, materiais, solicitações ou correções vinculadas"
    return None


def user_filter_options(profile):
    institutions = [enrich("instituicoes", item) for item in scoped_records(profile, "instituicoes")]
    municipality_ids = {item["municipio_id"] for item in institutions}
    municipalities = [item for item in DATA["municipios"] if item["id"] in municipality_ids]
    return municipalities, institutions


def navigation_key(entity):
    return "estrutura" if entity in {"series", "turmas", "alunos"} else entity


def normalized_search(value):
    return "".join(
        character for character in unicodedata.normalize("NFKD", str(value or ""))
        if not unicodedata.combining(character)
    ).lower()


@academic_bp.get("/estrutura")
@login_required
def structure():
    profile = ensure_access("series")
    series_records = [enrich("series", item) for item in scoped_records(profile, "series")]
    class_records = [enrich("turmas", item) for item in scoped_records(profile, "turmas")]
    student_records = [enrich("alunos", item) for item in scoped_records(profile, "alunos")]

    series_id = request.args.get("serie_id", "").strip()
    class_id = request.args.get("turma_id", "").strip()
    query = request.args.get("q", "").strip()

    series_by_id = {item["id"]: item for item in series_records}
    classes_by_id = {item["id"]: item for item in class_records}
    for student in student_records:
        school_class = classes_by_id.get(student.get("turma_id"), {})
        grade_series = series_by_id.get(school_class.get("serie_id"), {})
        student["serie_id"] = grade_series.get("id", "")
        student["serie"] = grade_series.get("nome", "Não informada")
    if series_id and series_id not in series_by_id:
        abort(403)
    if class_id:
        selected_class = classes_by_id.get(class_id)
        if not series_id or not selected_class or selected_class.get("serie_id") != series_id:
            abort(400)

    selected_series = series_by_id.get(series_id)
    selected_class = classes_by_id.get(class_id)
    selected_classes = [item for item in class_records if item.get("serie_id") == series_id]
    selected_students = sorted(
        [item for item in student_records if item.get("turma_id") == class_id],
        key=lambda item: normalized_search(item.get("nome")),
    )

    series_class_counts = {
        item["id"]: sum(1 for school_class in class_records if school_class.get("serie_id") == item["id"])
        for item in series_records
    }
    series_student_counts = {
        item["id"]: sum(
            1 for student in student_records
            if classes_by_id.get(student.get("turma_id"), {}).get("serie_id") == item["id"]
        )
        for item in series_records
    }
    class_student_counts = {
        item["id"]: sum(1 for student in student_records if student.get("turma_id") == item["id"])
        for item in class_records
    }

    search_key = normalized_search(query)
    search_results = []
    if search_key:
        search_results = sorted(
            [
                item for item in student_records
                if search_key in normalized_search(item.get("nome"))
                or search_key in normalized_search(item.get("matricula"))
            ],
            key=lambda item: normalized_search(item.get("nome")),
        )

    return render_template(
        "academic/structure.html",
        page_title="Séries, turmas e alunos",
        series_records=series_records,
        selected_series=selected_series,
        selected_series_id=series_id,
        selected_classes=selected_classes,
        selected_class=selected_class,
        selected_class_id=class_id,
        selected_students=selected_students,
        series_class_counts=series_class_counts,
        series_student_counts=series_student_counts,
        class_student_counts=class_student_counts,
        search_results=search_results,
        query=query,
        can_manage_series=can_manage(profile, "series"),
        can_manage_classes=can_manage(profile, "turmas"),
        can_manage_students=can_manage(profile, "alunos"),
        active_navigation="estrutura",
    )

@academic_bp.get("/<entity>")
@login_required
def list_entities(entity):
    config = entity_or_404(entity)
    profile = ensure_access(entity)
    records = [enrich(entity, item) for item in scoped_records(profile, entity)]

    query = request.args.get("q", "").strip().lower()
    status = request.args.get("status", "").strip().lower()
    municipality_id = request.args.get("municipio_id", "").strip()
    institution_id = request.args.get("instituicao_id", "").strip()
    if query:
        records = [item for item in records if query in " ".join(str(value).lower() for value in item.values())]
    if status:
        records = [item for item in records if item.get("status", "").lower() == status]
    if entity in {"alunos", "professores"}:
        if municipality_id:
            allowed_institutions = {item["id"] for item in DATA["instituicoes"] if item["municipio_id"] == municipality_id}
            records = [item for item in records if item.get("instituicao_id") in allowed_institutions]
        if institution_id:
            records = [item for item in records if item.get("instituicao_id") == institution_id]

    per_page = 5
    total = len(records)
    pages = max(1, math.ceil(total / per_page))
    page = min(max(request.args.get("page", 1, type=int), 1), pages)
    start = (page - 1) * per_page
    records = records[start : start + per_page]

    municipalities, institutions = user_filter_options(profile) if entity in {"alunos", "professores"} else ([], [])
    return render_template(
        "academic/list.html",
        page_title=config["plural"],
        page_description=f"Consulte e organize {config['plural'].lower()} dentro do seu escopo.",
        active_navigation=navigation_key(entity),
        entity=entity,
        config=config,
        records=records,
        can_manage=can_manage(profile, entity),
        can_toggle=profile["key"] in {"institute_coordinator", "it_admin"},
        pagination={"page": page, "pages": pages, "total": total},
        query=request.args.get("q", ""),
        selected_status=request.args.get("status", ""),
        selected_municipality=municipality_id,
        selected_institution=institution_id,
        municipalities=municipalities,
        institutions=institutions,
    )


@academic_bp.route("/<entity>/novo", methods=["GET", "POST"])
@login_required
def create(entity):
    config = entity_or_404(entity)
    profile = ensure_access(entity, manage=True)
    if request.method == "POST":
        values = form_values(entity, config, profile)
        if "nome" in values and not values["nome"]:
            values["nome"] = f"Novo {config['singular'].lower()}"
        error = identity_error(values) or relationship_error(entity, values)
        if error:
            flash(error, "danger")
            return render_template("academic/form.html", page_title=f"Novo {config['singular'].lower()}", entity=entity, config=config, record=values, field_labels=FIELD_LABELS, field_help=FIELD_HELP, options=form_options(profile, config), active_navigation=navigation_key(entity)), 400
        record = add_record(entity, values)
        flash(f"{config['singular']} salvo no banco de dados.", "success")
        return redirect(url_for("academic.detail", entity=entity, item_id=record["id"]))
    defaults = {}
    requested_series = find("series", request.args.get("serie_id", ""))
    requested_class = find("turmas", request.args.get("turma_id", ""))
    if requested_class and record_in_scope(profile, "turmas", requested_class["id"]):
        defaults.update({"turma_id": requested_class["id"], "instituicao_id": requested_class["instituicao_id"]})
    elif requested_series and record_in_scope(profile, "series", requested_series["id"]):
        defaults.update({"serie_id": requested_series["id"], "instituicao_id": requested_series["instituicao_id"]})
    if profile["key"] == "school_coordinator":
        defaults["instituicao_id"] = profile["institution_id"]
    return render_template("academic/form.html", page_title=f"Novo {config['singular'].lower()}", entity=entity, config=config, record=defaults, field_labels=FIELD_LABELS, field_help=FIELD_HELP, options=form_options(profile, config), active_navigation=navigation_key(entity))


@academic_bp.get("/<entity>/<item_id>")
@login_required
def detail(entity, item_id):
    config = entity_or_404(entity)
    profile = ensure_access(entity, item_id=item_id)
    record = enrich(entity, find(entity, item_id))
    related = []
    if entity == "municipios":
        related = [("Instituições", "instituicoes", [enrich("instituicoes", item) for item in DATA["instituicoes"] if item["municipio_id"] == item_id])]
    elif entity == "instituicoes":
        related = [
            ("Turmas", "turmas", [enrich("turmas", item) for item in DATA["turmas"] if item["instituicao_id"] == item_id]),
            ("Professores", "professores", [enrich("professores", item) for item in DATA["professores"] if item["instituicao_id"] == item_id]),
        ]
    elif entity == "turmas":
        related = [("Alunos", "alunos", [enrich("alunos", item) for item in DATA["alunos"] if item["turma_id"] == item_id])]
    active_navigation = navigation_key(entity)
    if profile["key"] == "student" or (profile["key"] == "teacher" and entity == "professores"):
        active_navigation = "meu-cadastro"
    return render_template("academic/detail.html", page_title=record["nome"], entity=entity, config=config, record=record, related=related, can_manage=can_manage(profile, entity), can_toggle=profile["key"] in {"institute_coordinator", "it_admin"}, can_delete=profile["key"] == "it_admin", can_transfer=entity == "professores" and profile["key"] in {"institute_coordinator", "it_admin"}, transfer_institutions=[enrich("instituicoes", item) for item in DATA["instituicoes"] if item["id"] != record.get("instituicao_id")], active_navigation=active_navigation)


@academic_bp.route("/<entity>/<item_id>/editar", methods=["GET", "POST"])
@login_required
def edit(entity, item_id):
    config = entity_or_404(entity)
    profile = ensure_access(entity, item_id=item_id, manage=True)
    record = find(entity, item_id)
    if request.method == "POST":
        values = form_values(entity, config, profile)
        if "nome" in values and not values["nome"]:
            values["nome"] = record["nome"]
        error = identity_error(values, exclude_id=item_id) or relationship_error(entity, values)
        if error:
            flash(error, "danger")
            return render_template("academic/form.html", page_title=f"Editar {config['singular'].lower()}", entity=entity, config=config, record=values, field_labels=FIELD_LABELS, field_help=FIELD_HELP, options=form_options(profile, config), active_navigation=navigation_key(entity)), 400
        update_record(entity, item_id, values)
        flash(f"{config['singular']} atualizado no banco de dados.", "success")
        return redirect(url_for("academic.detail", entity=entity, item_id=item_id))
    return render_template("academic/form.html", page_title=f"Editar {config['singular'].lower()}", entity=entity, config=config, record=record, field_labels=FIELD_LABELS, field_help=FIELD_HELP, options=form_options(profile, config), active_navigation=navigation_key(entity))


@academic_bp.post("/professores/<item_id>/transferir")
@login_required
def transfer_teacher(item_id):
    profile = ensure_access("professores", item_id=item_id)
    if profile["key"] not in {"institute_coordinator", "it_admin"}:
        abort(403)
    institution_id = request.form.get("instituicao_id", "")
    institution = find("instituicoes", institution_id)
    if not institution:
        abort(400)
    teacher = find("professores", item_id)
    allowed_subjects = {
        subject["id"] for subject in SUBJECTS
        if subject.get("escopo") == "global" or subject.get("instituicao_id") == institution_id
    }
    teacher = update_record("professores", item_id, {
        "instituicao_id": institution_id,
        "turma_ids": [],
        "disciplina_ids": [item for item in teacher.get("disciplina_ids", []) if item in allowed_subjects],
    })
    flash(f"{teacher['nome']} foi transferido para {institution['nome']}. Os vínculos de turma foram limpos.", "success")
    return redirect(url_for("academic.detail", entity="professores", item_id=item_id))


@academic_bp.post("/<entity>/<item_id>/alternar")
@login_required
def toggle(entity, item_id):
    config = entity_or_404(entity)
    profile = ensure_access(entity, item_id=item_id)
    if profile["key"] not in {"institute_coordinator", "it_admin"}:
        abort(403)
    record = toggle_record(entity, item_id)
    flash(f"Situação de {record['nome']} alterada para {record['status']}.", "success")
    fallback = url_for("academic.structure") if entity in {"series", "turmas", "alunos"} else url_for("academic.list_entities", entity=entity)
    return redirect(request.referrer or fallback)


@academic_bp.post("/<entity>/<item_id>/excluir")
@login_required
def delete(entity, item_id):
    config = entity_or_404(entity)
    profile = ensure_access(entity, item_id=item_id)
    if profile["key"] != "it_admin":
        abort(403)
    record = find(entity, item_id)
    blocker = deletion_blocker(entity, item_id)
    if blocker:
        flash(f"{config['singular']} não pode ser excluído porque {blocker}.", "danger")
        return redirect(url_for("academic.detail", entity=entity, item_id=item_id))
    delete_record(entity, item_id)
    flash(f"{config['singular']} {record['nome']} excluído pelo T.I.", "success")
    destination = url_for("academic.structure") if entity in {"series", "turmas", "alunos"} else url_for("academic.list_entities", entity=entity)
    return redirect(destination)
