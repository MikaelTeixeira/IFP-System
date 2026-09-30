from flask import url_for


def build_navigation(profile):
    if not profile:
        return []

    items = [{"key": "inicio", "label": "Início", "url": url_for("core.dashboard"), "icon": "home"}]
    role = profile["key"]

    if role == "student":
        items.extend([
            {"key": "notificacoes", "label": "Notificações", "url": url_for("student_area.notifications"), "icon": "notification"},
            {"key": "meus-simulados", "label": "Meus simulados", "url": url_for("student_area.assessments"), "icon": "assessment"},
            {"key": "revisao", "label": "Materiais de revisão", "url": url_for("student_area.review"), "icon": "curriculum"},
            {"key": "meu-cadastro", "label": "Meu cadastro", "url": url_for("academic.detail", entity="alunos", item_id=profile["student_id"]), "icon": "person"},
        ])
    elif role == "teacher":
        items.extend([
            {"key": "solicitacoes-questoes", "label": "Solicitações de questões", "url": url_for("assessments.teacher_requests"), "icon": "assessment"},
            {"key": "correcoes", "label": "Correções abertas", "url": url_for("assessments.corrections"), "icon": "questions"},
            {"key": "materiais", "label": "Materiais de revisão", "url": url_for("materials.index"), "icon": "curriculum"},
            {"key": "curriculo", "label": "Meus assuntos", "url": url_for("curriculum.index"), "icon": "curriculum"},
            {"key": "questoes", "label": "Banco de questões", "url": url_for("questions.list_questions"), "icon": "questions"},
            {"key": "turmas", "label": "Minhas turmas", "url": url_for("academic.list_entities", entity="turmas"), "icon": "class"},
            {"key": "alunos", "label": "Alunos", "url": url_for("academic.list_entities", entity="alunos"), "icon": "people"},
            {"key": "meu-cadastro", "label": "Meu cadastro", "url": url_for("academic.detail", entity="professores", item_id=profile["teacher_id"]), "icon": "person"},
        ])
    else:
        if role in {"institute_coordinator", "it_admin"}:
            items.extend([
                {"key": "municipios", "label": "Municípios", "url": url_for("academic.list_entities", entity="municipios"), "icon": "place"},
                {"key": "instituicoes", "label": "Instituições", "url": url_for("academic.list_entities", entity="instituicoes"), "icon": "school"},
            ])
        elif role == "school_coordinator":
            items.append({"key": "instituicoes", "label": "Minha instituição", "url": url_for("academic.detail", entity="instituicoes", item_id=profile["institution_id"]), "icon": "school"})
        items.extend([
            {"key": "series", "label": "Séries", "url": url_for("academic.list_entities", entity="series"), "icon": "layers"},
            {"key": "turmas", "label": "Turmas", "url": url_for("academic.list_entities", entity="turmas"), "icon": "class"},
            {"key": "alunos", "label": "Alunos", "url": url_for("academic.list_entities", entity="alunos"), "icon": "people"},
            {"key": "professores", "label": "Professores", "url": url_for("academic.list_entities", entity="professores"), "icon": "person"},
        ])
        if role in {"school_coordinator", "institute_coordinator"}:
            items.extend([
                {"key": "relatorios", "label": "Relatórios", "url": url_for("reports.index"), "icon": "chart"},
                {"key": "curriculo", "label": "Matérias e assuntos", "url": url_for("curriculum.index"), "icon": "curriculum"},
                {"key": "questoes", "label": "Banco de questões", "url": url_for("questions.list_questions"), "icon": "questions"},
                {"key": "simulados", "label": "Solicitar simulado" if role == "school_coordinator" else "Simulados", "url": url_for("assessments.list_assessments"), "icon": "assessment"},
            ])
    if role == "it_admin":
        items.append({"key": "usuarios", "label": "Usuários", "url": url_for("users.index"), "icon": "people"})
    return items
