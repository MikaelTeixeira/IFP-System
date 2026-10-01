from copy import deepcopy

from flask import current_app, has_app_context
from sqlalchemy import func, or_

from .academic import DATA, find
from ..extensions import db
from ..models import UserAccount


ROLE_LABELS = {
    "student": "Aluno",
    "teacher": "Professor",
    "school_coordinator": "Coord. Colégio",
    "institute_coordinator": "Coord. Instituto",
    "it_admin": "T.I.",
}

INITIAL_USER_ACCOUNTS = [
    {"id": "usr-001", "nome": "Ana Clara Souza", "cpf": "30123456780", "email": "ana.souza@aluno.ifp.edu.br", "cargo": "student", "municipio_id": "mun-001", "instituicao_id": "inst-001", "status": "Ativo"},
    {"id": "usr-002", "nome": "João Pedro Alves", "cpf": "30234567891", "email": "joao.alves@aluno.ifp.edu.br", "cargo": "student", "municipio_id": "mun-001", "instituicao_id": "inst-001", "status": "Ativo"},
    {"id": "usr-003", "nome": "Rafael Lima", "cpf": "20123456789", "email": "rafael.lima@ifp.edu.br", "cargo": "teacher", "municipio_id": "mun-001", "instituicao_id": "inst-001", "status": "Ativo"},
    {"id": "usr-004", "nome": "Camila Mendes", "cpf": "20234567890", "email": "camila.mendes@ifp.edu.br", "cargo": "teacher", "municipio_id": "mun-001", "instituicao_id": "inst-001", "status": "Ativo"},
    {"id": "usr-005", "nome": "Beatriz Nogueira", "cpf": "40123456780", "email": "beatriz.nogueira@ifp.edu.br", "cargo": "school_coordinator", "municipio_id": "mun-001", "instituicao_id": "inst-001", "status": "Ativo"},
    {"id": "usr-006", "nome": "Helena Martins", "cpf": "40234567891", "email": "helena.martins@ifp.edu.br", "cargo": "institute_coordinator", "municipio_id": "", "instituicao_id": "", "status": "Ativo"},
    {"id": "usr-007", "nome": "Suporte IFP", "cpf": "40345678902", "email": "suporte@ifp.edu.br", "cargo": "it_admin", "municipio_id": "", "instituicao_id": "", "status": "Ativo"},
]

USER_ACCOUNTS = deepcopy(INITIAL_USER_ACCOUNTS)


def database_active():
    return has_app_context() and current_app.config.get("DATABASE_ENABLED", False)


def list_users():
    if database_active():
        return [item.to_record() for item in UserAccount.query.order_by(UserAccount.name).all()]
    return list(USER_ACCOUNTS)


def find_user(user_id):
    if database_active():
        model = db.session.get(UserAccount, user_id)
        return model.to_record() if model else None
    return next((item for item in USER_ACCOUNTS if item["id"] == user_id), None)


def enrich_user(user):
    item = dict(user)
    municipality = find("municipios", user.get("municipio_id"))
    institution = find("instituicoes", user.get("instituicao_id"))
    item["municipio"] = municipality["nome"] if municipality else "Abrangência geral"
    item["instituicao"] = institution["nome"] if institution else "Instituto"
    item["cargo_nome"] = ROLE_LABELS.get(user["cargo"], user["cargo"])
    return item


def add_user(values):
    current_users = list_users()
    sequence = max([int(item["id"].split("-")[-1]) for item in current_users] or [0]) + 1
    user = {"id": f"usr-{sequence:03d}", **values, "status": "Ativo"}
    if database_active():
        account = UserAccount(
            id=user["id"], name=user["nome"], cpf=user["cpf"], email=user["email"], role=user["cargo"],
            municipality_id=user["municipio_id"] or None, institution_id=user["instituicao_id"] or None,
            status=user["status"],
        )
        db.session.add(account)
        db.session.flush()
        if user["cargo"] in {"student", "teacher"}:
            from ..models import Student, Teacher

            entity = "alunos" if user["cargo"] == "student" else "professores"
            prefix = "alu" if entity == "alunos" else "pro"
            sequence = max([int(item["id"].rsplit("-", 1)[-1]) for item in DATA[entity]] or [0]) + 1
            person_id = f"{prefix}-{sequence:03d}"
            if entity == "alunos":
                person = Student(
                    id=person_id, name=user["nome"], cpf=user["cpf"], email=user["email"],
                    enrollment=f"CAD-{sequence:04d}", class_id=None, institution_id=user["instituicao_id"],
                    admission="", status="Pendente", user_account_id=user["id"],
                )
            else:
                person = Teacher(
                    id=person_id, name=user["nome"], cpf=user["cpf"], email=user["email"],
                    subject_ids=[], class_ids=[], institution_id=user["instituicao_id"],
                    status="Ativo", user_account_id=user["id"],
                )
            db.session.add(person)
        db.session.commit()
        if user["cargo"] in {"student", "teacher"}:
            DATA[entity].append(person.to_record())
    if not any(item["id"] == user["id"] for item in USER_ACCOUNTS):
        USER_ACCOUNTS.append(user)
    return user


def toggle_user(user_id):
    if database_active():
        model = db.session.get(UserAccount, user_id)
        if not model:
            return None
        model.status = "Inativo" if model.status == "Ativo" else "Ativo"
        from ..models import Student, Teacher

        person = Student.query.filter_by(user_account_id=user_id).first()
        if person:
            person.status = "Inativa" if model.status == "Inativo" else "Ativa"
        teacher = Teacher.query.filter_by(user_account_id=user_id).first()
        if teacher:
            teacher.status = model.status
        db.session.commit()
        user = model.to_record()
        cached = next((item for item in USER_ACCOUNTS if item["id"] == user_id), None)
        if cached:
            cached.update(user)
        if person:
            academic_record = find("alunos", person.id)
            if academic_record:
                academic_record.update(person.to_record())
        if teacher:
            academic_record = find("professores", teacher.id)
            if academic_record:
                academic_record.update(teacher.to_record())
        return user
    user = find_user(user_id)
    if user:
        user["status"] = "Inativo" if user["status"] == "Ativo" else "Ativo"
    return user


def user_identity_conflict(cpf, email):
    if database_active():
        model = UserAccount.query.filter(or_(UserAccount.cpf == cpf, func.lower(UserAccount.email) == email.lower())).first()
        return model.to_record() if model else None
    return next((
        item for item in USER_ACCOUNTS
        if item.get("cpf") == cpf or item.get("email", "").lower() == email.lower()
    ), None)
