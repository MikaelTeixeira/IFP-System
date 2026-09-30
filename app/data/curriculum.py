from copy import deepcopy


INITIAL_SUBJECTS = [
    {"id": "mat-001", "nome": "Matemática", "escopo": "global", "instituicao_id": "", "status": "Ativa", "criado_por": "T.I."},
    {"id": "mat-002", "nome": "Língua Portuguesa", "escopo": "global", "instituicao_id": "", "status": "Ativa", "criado_por": "T.I."},
    {"id": "mat-003", "nome": "Ciências", "escopo": "global", "instituicao_id": "", "status": "Ativa", "criado_por": "T.I."},
    {"id": "mat-004", "nome": "História", "escopo": "global", "instituicao_id": "", "status": "Ativa", "criado_por": "T.I."},
]

INITIAL_TOPICS = [
    {"id": "ass-001", "nome": "Operações primárias", "materia_id": "mat-001", "status": "Ativo"},
    {"id": "ass-002", "nome": "Frações", "materia_id": "mat-001", "status": "Ativo"},
    {"id": "ass-003", "nome": "Leitura e interpretação", "materia_id": "mat-002", "status": "Ativo"},
    {"id": "ass-004", "nome": "Seres vivos", "materia_id": "mat-003", "status": "Ativo"},
    {"id": "ass-005", "nome": "História do Brasil", "materia_id": "mat-004", "status": "Ativo"},
]

SUBJECTS = deepcopy(INITIAL_SUBJECTS)
TOPICS = deepcopy(INITIAL_TOPICS)


def find_subject(subject_id):
    return next((item for item in SUBJECTS if item["id"] == subject_id), None)


def find_topic(topic_id):
    return next((item for item in TOPICS if item["id"] == topic_id), None)


def subject_name(subject_id):
    subject = find_subject(subject_id)
    return subject["nome"] if subject else "Não informada"


def topic_name(topic_id):
    topic = find_topic(topic_id)
    return topic["nome"] if topic else "Não informado"


def subjects_for_profile(profile):
    if not profile:
        return []
    institution_id = profile.get("institution_id", "")
    if profile["key"] == "school_coordinator":
        return [item for item in SUBJECTS if item["escopo"] == "global" or item.get("instituicao_id") == institution_id]
    if profile["key"] == "teacher":
        from .academic import find

        teacher = find("professores", profile["teacher_id"])
        subject_ids = set(teacher.get("disciplina_ids", [])) if teacher else set()
        return [item for item in SUBJECTS if item["id"] in subject_ids]
    return list(SUBJECTS)


def topics_for_subject(subject_id):
    return [item for item in TOPICS if item["materia_id"] == subject_id]


def add_subject(nome, escopo, instituicao_id, criado_por):
    sequence = max([int(item["id"].split("-")[-1]) for item in SUBJECTS] or [0]) + 1
    subject = {
        "id": f"mat-{sequence:03d}",
        "nome": nome,
        "escopo": escopo,
        "instituicao_id": instituicao_id if escopo == "instituicao" else "",
        "status": "Ativa",
        "criado_por": criado_por,
    }
    SUBJECTS.append(subject)
    return subject


def add_topic(nome, subject_id, criado_por=""):
    sequence = max([int(item["id"].split("-")[-1]) for item in TOPICS] or [0]) + 1
    topic = {"id": f"ass-{sequence:03d}", "nome": nome, "materia_id": subject_id, "status": "Ativo", "criado_por": criado_por}
    TOPICS.append(topic)
    return topic


def update_topic(topic_id, nome):
    topic = find_topic(topic_id)
    if topic:
        topic["nome"] = nome
    return topic


def delete_topic(topic_id):
    topic = find_topic(topic_id)
    if topic:
        TOPICS.remove(topic)
    return topic
