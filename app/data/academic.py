from copy import deepcopy

from flask import current_app, has_app_context


INITIAL_DATA = {
    "municipios": [
        {"id": "mun-001", "nome": "Fortaleza", "uf": "CE", "codigo": "2304400", "status": "Ativo"},
        {"id": "mun-002", "nome": "Caucaia", "uf": "CE", "codigo": "2303709", "status": "Ativo"},
        {"id": "mun-003", "nome": "Maracanaú", "uf": "CE", "codigo": "2307650", "status": "Ativo"},
    ],
    "instituicoes": [
        {"id": "inst-001", "nome": "Escola Horizonte", "municipio_id": "mun-001", "codigo": "EH-01", "status": "Ativa"},
        {"id": "inst-002", "nome": "Colégio Caminhos", "municipio_id": "mun-001", "codigo": "CC-02", "status": "Ativa"},
        {"id": "inst-003", "nome": "Escola Lagoa Azul", "municipio_id": "mun-002", "codigo": "ELA-03", "status": "Ativa"},
        {"id": "inst-004", "nome": "Centro Educacional Girassol", "municipio_id": "mun-003", "codigo": "CEG-04", "status": "Ativa"},
    ],
    "series": [
        {"id": "ser-001", "nome": "7º ano", "instituicao_id": "inst-001", "turno": "Manhã", "status": "Ativa"},
        {"id": "ser-002", "nome": "8º ano", "instituicao_id": "inst-001", "turno": "Manhã", "status": "Ativa"},
        {"id": "ser-003", "nome": "9º ano", "instituicao_id": "inst-001", "turno": "Tarde", "status": "Ativa"},
        {"id": "ser-004", "nome": "8º ano", "instituicao_id": "inst-002", "turno": "Tarde", "status": "Ativa"},
        {"id": "ser-005", "nome": "9º ano", "instituicao_id": "inst-003", "turno": "Manhã", "status": "Ativa"},
    ],
    "turmas": [
        {"id": "tur-001", "nome": "Turma A", "serie_id": "ser-003", "instituicao_id": "inst-001", "ano_letivo": "2026", "turno": "Tarde", "status": "Ativa"},
        {"id": "tur-002", "nome": "Turma B", "serie_id": "ser-003", "instituicao_id": "inst-001", "ano_letivo": "2026", "turno": "Tarde", "status": "Ativa"},
        {"id": "tur-003", "nome": "Turma A", "serie_id": "ser-002", "instituicao_id": "inst-001", "ano_letivo": "2026", "turno": "Manhã", "status": "Ativa"},
        {"id": "tur-004", "nome": "Turma A", "serie_id": "ser-004", "instituicao_id": "inst-002", "ano_letivo": "2026", "turno": "Tarde", "status": "Ativa"},
        {"id": "tur-005", "nome": "Turma A", "serie_id": "ser-005", "instituicao_id": "inst-003", "ano_letivo": "2026", "turno": "Manhã", "status": "Ativa"},
    ],
    "alunos": [
        {"id": "alu-001", "nome": "Ana Clara Souza", "cpf": "30123456780", "email": "ana.souza@aluno.ifp.edu.br", "matricula": "2026001", "turma_id": "tur-001", "instituicao_id": "inst-001", "ingresso": "10/02/2026", "status": "Ativa"},
        {"id": "alu-002", "nome": "João Pedro Alves", "cpf": "30234567891", "email": "joao.alves@aluno.ifp.edu.br", "matricula": "2026002", "turma_id": "tur-001", "instituicao_id": "inst-001", "ingresso": "10/02/2026", "status": "Ativo"},
        {"id": "alu-003", "nome": "Mariana Costa", "cpf": "30345678902", "email": "mariana.costa@aluno.ifp.edu.br", "matricula": "2026003", "turma_id": "tur-002", "instituicao_id": "inst-001", "ingresso": "11/02/2026", "status": "Ativa"},
        {"id": "alu-004", "nome": "Lucas Nascimento", "cpf": "30456789013", "email": "lucas.nascimento@aluno.ifp.edu.br", "matricula": "2026004", "turma_id": "tur-002", "instituicao_id": "inst-001", "ingresso": "11/02/2026", "status": "Pendente"},
        {"id": "alu-005", "nome": "Sofia Ribeiro", "cpf": "30567890124", "email": "sofia.ribeiro@aluno.ifp.edu.br", "matricula": "2026005", "turma_id": "tur-003", "instituicao_id": "inst-001", "ingresso": "12/02/2026", "status": "Ativa"},
        {"id": "alu-006", "nome": "Gabriel Freitas", "cpf": "30678901235", "email": "gabriel.freitas@aluno.ifp.edu.br", "matricula": "2026006", "turma_id": "tur-004", "instituicao_id": "inst-002", "ingresso": "12/02/2026", "status": "Ativo"},
        {"id": "alu-007", "nome": "Lívia Moreira", "cpf": "30789012346", "email": "livia.moreira@aluno.ifp.edu.br", "matricula": "2026007", "turma_id": "tur-005", "instituicao_id": "inst-003", "ingresso": "13/02/2026", "status": "Ativa"},
    ],
    "professores": [
        {"id": "pro-001", "nome": "Rafael Lima", "cpf": "20123456789", "email": "rafael.lima@ifp.edu.br", "disciplina_ids": ["mat-001"], "turma_ids": ["tur-001", "tur-002"], "instituicao_id": "inst-001", "status": "Ativo"},
        {"id": "pro-002", "nome": "Camila Mendes", "cpf": "20234567890", "email": "camila.mendes@ifp.edu.br", "disciplina_ids": ["mat-002"], "turma_ids": ["tur-001", "tur-003"], "instituicao_id": "inst-001", "status": "Ativa"},
        {"id": "pro-003", "nome": "Paulo Andrade", "cpf": "20345678901", "email": "paulo.andrade@ifp.edu.br", "disciplina_ids": ["mat-003"], "turma_ids": ["tur-002"], "instituicao_id": "inst-001", "status": "Ativo"},
        {"id": "pro-004", "nome": "Renata Gomes", "cpf": "20456789012", "email": "renata.gomes@ifp.edu.br", "disciplina_ids": ["mat-001"], "turma_ids": ["tur-004"], "instituicao_id": "inst-002", "status": "Ativa"},
        {"id": "pro-005", "nome": "Diego Rocha", "cpf": "20567890123", "email": "diego.rocha@ifp.edu.br", "disciplina_ids": ["mat-004"], "turma_ids": ["tur-005"], "instituicao_id": "inst-003", "status": "Ativo"},
    ],
}

DATA = deepcopy(INITIAL_DATA)

ENTITY_CONFIG = {
    "municipios": {"singular": "Município", "plural": "Municípios", "prefix": "mun", "columns": ["nome", "uf", "codigo", "status"], "fields": ["nome", "uf", "codigo"]},
    "instituicoes": {"singular": "Instituição", "plural": "Instituições", "prefix": "inst", "columns": ["nome", "municipio", "codigo", "status"], "fields": ["nome", "municipio_id", "codigo"]},
    "series": {"singular": "Série", "plural": "Séries", "prefix": "ser", "columns": ["nome", "instituicao", "turno", "status"], "fields": ["nome", "instituicao_id", "turno"]},
    "turmas": {"singular": "Turma", "plural": "Turmas", "prefix": "tur", "columns": ["nome", "serie", "instituicao", "ano_letivo", "status"], "fields": ["nome", "serie_id", "instituicao_id", "ano_letivo", "turno"]},
    "alunos": {"singular": "Aluno", "plural": "Alunos", "prefix": "alu", "columns": ["nome", "email", "matricula", "instituicao", "status"], "fields": ["nome", "cpf", "email", "matricula", "turma_id", "instituicao_id", "ingresso"]},
    "professores": {"singular": "Professor", "plural": "Professores", "prefix": "pro", "columns": ["nome", "email", "disciplinas", "instituicao", "status"], "fields": ["nome", "cpf", "email", "disciplina_ids", "instituicao_id"]},
}


def find(entity, item_id):
    return next((item for item in DATA[entity] if item["id"] == item_id), None)


def display_name(entity, item_id):
    item = find(entity, item_id)
    return item["nome"] if item else "Não informado"


def enrich(entity, item):
    from .curriculum import subject_name

    enriched = dict(item)
    if item.get("municipio_id"):
        enriched["municipio"] = display_name("municipios", item["municipio_id"])
    if item.get("instituicao_id"):
        enriched["instituicao"] = display_name("instituicoes", item["instituicao_id"])
    if item.get("serie_id"):
        enriched["serie"] = display_name("series", item["serie_id"])
    if item.get("turma_id"):
        enriched["turma"] = display_name("turmas", item["turma_id"])
    if item.get("turma_ids"):
        enriched["turmas"] = ", ".join(display_name("turmas", item_id) for item_id in item["turma_ids"])
    if item.get("disciplina_ids"):
        enriched["disciplinas"] = ", ".join(subject_name(item_id) for item_id in item["disciplina_ids"])
    return enriched


def add_record(entity, values):
    prefix = ENTITY_CONFIG[entity]["prefix"]
    sequence = max([int(item["id"].split("-")[-1]) for item in DATA[entity]] or [0]) + 1
    record = {"id": f"{prefix}-{sequence:03d}", **values, "status": "Ativo" if entity not in {"instituicoes", "series", "turmas", "alunos"} else "Ativa"}
    if entity == "professores":
        record["turma_ids"] = []
    DATA[entity].append(record)
    _persist_reference_record(entity, record)
    return record


def update_record(entity, item_id, values):
    record = find(entity, item_id)
    if record:
        record.update(values)
        _persist_reference_record(entity, record)
    return record


def toggle_record(entity, item_id):
    record = find(entity, item_id)
    if not record:
        return None
    active = record.get("status", "").lower() in {"ativo", "ativa"}
    feminine = entity in {"instituicoes", "series", "turmas", "alunos"}
    record["status"] = ("Inativa" if feminine else "Inativo") if active else ("Ativa" if feminine else "Ativo")
    _persist_reference_record(entity, record)
    return record


def delete_record(entity, item_id):
    record = find(entity, item_id)
    if not record:
        return None
    if has_app_context() and current_app.config.get("DATABASE_ENABLED", False):
        from ..extensions import db
        from ..models import (
            GradeSeries, Institution, Municipality, Notification, SchoolClass,
            Student, StudentAttendanceSummary, Teacher,
        )

        model_class = {
            "municipios": Municipality,
            "instituicoes": Institution,
            "series": GradeSeries,
            "turmas": SchoolClass,
            "alunos": Student,
            "professores": Teacher,
        }[entity]
        if entity == "alunos":
            StudentAttendanceSummary.query.filter_by(student_id=item_id).delete()
            Notification.query.filter_by(recipient_role="student", recipient_id=item_id).delete()
        elif entity == "professores":
            Notification.query.filter_by(recipient_role="teacher", recipient_id=item_id).delete()
        model = db.session.get(model_class, item_id)
        if model:
            db.session.delete(model)
        db.session.commit()
    DATA[entity].remove(record)
    return record


def _persist_reference_record(entity, record):
    if not has_app_context() or not current_app.config.get("DATABASE_ENABLED", False):
        return
    from ..extensions import db
    from ..models import GradeSeries, Institution, Municipality, SchoolClass, Student, Teacher, UserAccount

    if entity == "municipios":
        model = Municipality(id=record["id"], name=record["nome"], state=record["uf"], code=record["codigo"], status=record["status"])
    elif entity == "instituicoes":
        model = Institution(id=record["id"], name=record["nome"], municipality_id=record["municipio_id"], code=record["codigo"], status=record["status"])
    elif entity == "series":
        model = GradeSeries(
            id=record["id"], name=record["nome"], institution_id=record["instituicao_id"],
            shift=record["turno"], status=record["status"],
        )
    elif entity == "turmas":
        model = SchoolClass(
            id=record["id"], name=record["nome"], series_id=record["serie_id"],
            institution_id=record["instituicao_id"], school_year=record["ano_letivo"],
            shift=record.get("turno", ""), status=record["status"],
        )
    elif entity == "alunos":
        account = _sync_person_account(record, "student", UserAccount, db)
        model = Student(
            id=record["id"], name=record["nome"], cpf=record["cpf"], email=record["email"],
            enrollment=record["matricula"], class_id=record.get("turma_id") or None,
            institution_id=record["instituicao_id"], admission=record.get("ingresso", ""),
            status=record["status"], user_account_id=account.id,
        )
    elif entity == "professores":
        account = _sync_person_account(record, "teacher", UserAccount, db)
        model = Teacher(
            id=record["id"], name=record["nome"], cpf=record["cpf"], email=record["email"],
            subject_ids=list(record.get("disciplina_ids", [])), class_ids=list(record.get("turma_ids", [])),
            institution_id=record["instituicao_id"], status=record["status"], user_account_id=account.id,
        )
    else:
        return
    db.session.merge(model)
    db.session.commit()


def _sync_person_account(record, role, user_model, database):
    from .users import USER_ACCOUNTS

    account = database.session.get(user_model, record.get("_user_account_id")) if record.get("_user_account_id") else None
    if not account:
        account = user_model.query.filter_by(cpf=record["cpf"]).first()
    if not account:
        existing_ids = [int(item.id.rsplit("-", 1)[-1]) for item in user_model.query.all()]
        account = user_model(id=f"usr-{max(existing_ids or [0]) + 1:03d}")
        database.session.add(account)
    institution = find("instituicoes", record["instituicao_id"])
    account.name = record["nome"]
    account.cpf = record["cpf"]
    account.email = record["email"]
    account.role = role
    account.institution_id = record["instituicao_id"]
    account.municipality_id = institution["municipio_id"] if institution else None
    account.status = "Inativo" if record.get("status", "").lower() in {"inativo", "inativa"} else record.get("status", "Ativo")
    database.session.flush()
    record["_user_account_id"] = account.id
    cached = next((item for item in USER_ACCOUNTS if item["id"] == account.id), None)
    if cached:
        cached.update(account.to_record())
    else:
        USER_ACCOUNTS.append(account.to_record())
    return account


def normalize_cpf(value):
    return "".join(character for character in value if character.isdigit())


def normalize_email(value):
    return value.strip().lower()


def find_identity_conflict(cpf="", email="", exclude_id=None):
    normalized_cpf = normalize_cpf(cpf)
    normalized_email = normalize_email(email)
    for entity in ("alunos", "professores"):
        for record in DATA[entity]:
            if record["id"] == exclude_id:
                continue
            if normalized_cpf and normalize_cpf(record.get("cpf", "")) == normalized_cpf:
                return "cpf", record
            if normalized_email and normalize_email(record.get("email", "")) == normalized_email:
                return "email", record
    if has_app_context() and current_app.config.get("DATABASE_ENABLED", False):
        from ..models import UserAccount

        excluded_record = next((find(entity, exclude_id) for entity in ("alunos", "professores") if find(entity, exclude_id)), None)
        excluded_account_id = excluded_record.get("_user_account_id") if excluded_record else None
        for account in UserAccount.query.all():
            if account.id == excluded_account_id:
                continue
            if normalized_cpf and normalize_cpf(account.cpf) == normalized_cpf:
                return "cpf", account.to_record()
            if normalized_email and normalize_email(account.email) == normalized_email:
                return "email", account.to_record()
    return None, None
SCOPE_KEYS = ("institution_id", "series_name", "school_year", "class_id")


def matches_scope(audience, scope):
    """An empty scope key means "any value", so a partial filter still matches."""
    return all(not scope.get(key) or audience.get(key) == scope[key] for key in SCOPE_KEYS)


def student_audience(student):
    school_class = find("turmas", student.get("turma_id", "")) or {}
    return {
        "institution_id": student["instituicao_id"], "class_id": student.get("turma_id", ""),
        "series_name": (find("series", school_class.get("serie_id", "")) or {}).get("nome", ""),
        "school_year": school_class.get("ano_letivo", ""),
    }


def eligible_students(assessment, scope):
    """The students an assessment is meant to reach inside a scope: the expected audience."""
    allowed_series = set(assessment.get("serie_ids", []))
    students = []
    for student in DATA["alunos"]:
        audience = student_audience(student)
        school_class = find("turmas", student.get("turma_id", "")) or {}
        if student["instituicao_id"] not in assessment.get("instituicao_ids", []):
            continue
        if student.get("status", "").lower() not in {"ativo", "ativa"}:
            continue
        if allowed_series and school_class.get("serie_id") not in allowed_series:
            continue
        if matches_scope(audience, scope):
            students.append(student)
    return sorted(students, key=lambda item: (item["instituicao_id"], item.get("turma_id", ""), item["nome"]))
