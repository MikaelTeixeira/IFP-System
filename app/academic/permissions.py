from ..data.academic import DATA


ENTITY_ROLES = {
    "municipios": {"institute_coordinator", "it_admin"},
    "instituicoes": {"school_coordinator", "institute_coordinator", "it_admin"},
    "series": {"teacher", "school_coordinator", "institute_coordinator", "it_admin"},
    "turmas": {"teacher", "school_coordinator", "institute_coordinator", "it_admin"},
    "alunos": {"student", "teacher", "school_coordinator", "institute_coordinator", "it_admin"},
    "professores": {"teacher", "school_coordinator", "institute_coordinator", "it_admin"},
}


def can_access(profile, entity):
    return profile and profile["key"] in ENTITY_ROLES.get(entity, set())


def can_manage(profile, entity):
    if not profile:
        return False
    if profile["key"] in {"institute_coordinator", "it_admin"}:
        return True
    return profile["key"] == "school_coordinator" and entity in {"series", "turmas", "alunos", "professores"}


def scoped_records(profile, entity):
    records = list(DATA[entity])
    role = profile["key"]
    if role in {"institute_coordinator", "it_admin"}:
        return records
    if role == "school_coordinator":
        institution_id = profile["institution_id"]
        if entity == "instituicoes":
            return [record for record in records if record["id"] == institution_id]
        return [record for record in records if record.get("instituicao_id") == institution_id]
    if role == "teacher":
        teacher = next((item for item in DATA["professores"] if item["id"] == profile["teacher_id"]), None)
        class_ids = teacher.get("turma_ids", []) if teacher else []
        if entity == "professores":
            return [record for record in records if record["id"] == profile["teacher_id"]]
        if entity == "turmas":
            return [record for record in records if record["id"] in class_ids]
        if entity == "series":
            series_ids = {item["serie_id"] for item in DATA["turmas"] if item["id"] in class_ids}
            return [record for record in records if record["id"] in series_ids]
        if entity == "alunos":
            return [record for record in records if record.get("turma_id") in class_ids]
    if role == "student" and entity == "alunos":
        return [record for record in records if record["id"] == profile["student_id"]]
    return []


def record_in_scope(profile, entity, item_id):
    return any(record["id"] == item_id for record in scoped_records(profile, entity))
