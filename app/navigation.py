from flask import url_for


def build_navigation(profile):
    if not profile:
        return []

    items = [{"key": "inicio", "label": "Início", "url": url_for("core.dashboard"), "icon": "home", "group": "Visão geral"}]
    role = profile["key"]

    if role == "student":
        items.extend([
            {"key": "notificacoes", "label": "Notificações", "url": url_for("student_area.notifications"), "icon": "notification", "group": "Visão geral"},
            {"key": "meus-simulados", "label": "Meus simulados", "url": url_for("student_area.assessments"), "icon": "assessment", "group": "Aprendizagem"},
            {"key": "revisao", "label": "Materiais de revisão", "url": url_for("student_area.review"), "icon": "curriculum", "group": "Aprendizagem"},
            {"key": "meu-cadastro", "label": "Meu cadastro", "url": url_for("academic.detail", entity="alunos", item_id=profile["student_id"]), "icon": "person", "group": "Perfil"},
        ])
    elif role == "teacher":
        items.extend([
            {"key": "solicitacoes-questoes", "label": "Solicitações de questões", "url": url_for("assessments.teacher_requests"), "icon": "assessment", "group": "Trabalho docente"},
            {"key": "correcoes", "label": "Correções", "url": url_for("assessments.corrections"), "icon": "questions", "group": "Trabalho docente"},
            {"key": "materiais", "label": "Materiais de revisão", "url": url_for("materials.index"), "icon": "curriculum", "group": "Trabalho docente"},
            {"key": "curriculo", "label": "Meus assuntos", "url": url_for("curriculum.index"), "icon": "curriculum", "group": "Trabalho docente"},
            {"key": "questoes", "label": "Banco de questões", "url": url_for("questions.list_questions"), "icon": "questions", "group": "Trabalho docente"},
            {"key": "turmas", "label": "Minhas turmas", "url": url_for("academic.list_entities", entity="turmas"), "icon": "class", "group": "Turmas e perfil"},
            {"key": "alunos", "label": "Alunos", "url": url_for("academic.list_entities", entity="alunos"), "icon": "people", "group": "Turmas e perfil"},
            {"key": "meu-cadastro", "label": "Meu cadastro", "url": url_for("academic.detail", entity="professores", item_id=profile["teacher_id"]), "icon": "person", "group": "Turmas e perfil"},
        ])
    else:
        if role in {"school_coordinator", "institute_coordinator"}:
            items.append({"key": "relatorios", "label": "Relatórios", "url": url_for("reports.index"), "icon": "chart", "group": "Visão geral"})
        if role in {"institute_coordinator", "it_admin"}:
            items.extend([
                {"key": "municipios", "label": "Municípios", "url": url_for("academic.list_entities", entity="municipios"), "icon": "place", "group": "Rede escolar"},
                {"key": "instituicoes", "label": "Instituições", "url": url_for("academic.list_entities", entity="instituicoes"), "icon": "school", "group": "Rede escolar"},
            ])
        elif role == "school_coordinator":
            items.append({"key": "instituicoes", "label": "Minha instituição", "url": url_for("academic.detail", entity="instituicoes", item_id=profile["institution_id"]), "icon": "school", "group": "Rede escolar"})
        items.extend([
            {"key": "series", "label": "Séries", "url": url_for("academic.list_entities", entity="series"), "icon": "layers", "group": "Rede escolar"},
            {"key": "turmas", "label": "Turmas", "url": url_for("academic.list_entities", entity="turmas"), "icon": "class", "group": "Rede escolar"},
            {"key": "alunos", "label": "Alunos", "url": url_for("academic.list_entities", entity="alunos"), "icon": "people", "group": "Rede escolar"},
            {"key": "professores", "label": "Professores", "url": url_for("academic.list_entities", entity="professores"), "icon": "person", "group": "Rede escolar"},
        ])
        if role in {"school_coordinator", "institute_coordinator"}:
            items.extend([
                {"key": "curriculo", "label": "Matérias e assuntos", "url": url_for("curriculum.index"), "icon": "curriculum", "group": "Avaliações"},
                {"key": "questoes", "label": "Banco de questões", "url": url_for("questions.list_questions"), "icon": "questions", "group": "Avaliações"},
                {"key": "simulados", "label": "Solicitar simulado" if role == "school_coordinator" else "Simulados", "url": url_for("assessments.list_assessments"), "icon": "assessment", "group": "Avaliações"},
            ])
    if role == "it_admin":
        items.append({"key": "usuarios", "label": "Usuários", "url": url_for("users.index"), "icon": "people", "group": "Administração"})
    return items
