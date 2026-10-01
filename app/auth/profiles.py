PROFILES = {
    "student": {
        "account_id": "usr-001",
        "label": "Aluno",
        "name": "Ana Clara Souza",
        "initials": "AC",
        "student_id": "alu-001",
        "description": "Acompanhe seus dados acadêmicos e atividades.",
    },
    "teacher": {
        "account_id": "usr-003",
        "label": "Professor",
        "name": "Rafael Lima",
        "initials": "RL",
        "teacher_id": "pro-001",
        "class_ids": ["tur-001", "tur-002"],
        "description": "Consulte suas turmas e estudantes vinculados.",
    },
    "school_coordinator": {
        "account_id": "usr-005",
        "label": "Coord. Colégio",
        "name": "Beatriz Nogueira",
        "initials": "BN",
        "institution_id": "inst-001",
        "description": "Gerencie a estrutura da Escola Horizonte.",
    },
    "institute_coordinator": {
        "account_id": "usr-006",
        "label": "Coord. Instituto",
        "name": "Helena Martins",
        "initials": "HM",
        "description": "Acompanhe e organize todas as instituições.",
    },
    "it_admin": {
        "account_id": "usr-007",
        "label": "Administrador/T.I.",
        "name": "Suporte IFP",
        "initials": "ST",
        "description": "Administre o ambiente demonstrativo.",
    },
}


def get_profile(profile_key):
    profile = PROFILES.get(profile_key)
    if profile is None:
        return None
    return {"key": profile_key, **profile}
