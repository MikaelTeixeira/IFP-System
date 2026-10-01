from io import BytesIO

import pytest

from app import create_app
from app.config import TestConfig


@pytest.fixture()
def client():
    return create_app(TestConfig).test_client()


def login_as(client, profile):
    with client.session_transaction() as session:
        session["profile"] = profile


def test_institute_report_compares_schools_and_shows_ranking(client):
    login_as(client, "institute_coordinator")
    response = client.get("/relatorios/")
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Relatório das escolas" in content
    assert "Ranking de médias" in content
    assert "Escola Horizonte" in content
    assert "Centro Educacional Girassol" in content
    assert 'data-report-chart="bar"' in content
    assert "Evolução de todas as escolas" in content
    assert 'data-report-chart="line"' in content


def test_school_coordinator_report_is_limited_to_own_school(client):
    login_as(client, "school_coordinator")
    response = client.get("/relatorios/", follow_redirects=True)
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Sobre a escola" in content
    assert "Escola Horizonte" in content
    assert "Colégio Caminhos" not in content
    assert client.get("/relatorios/escolas/inst-002").status_code == 403


def test_report_drills_down_from_series_to_class(client):
    login_as(client, "institute_coordinator")
    series_response = client.get("/relatorios/escolas/inst-001/series/ser-003")
    assert series_response.status_code == 200
    assert "Desempenho por turma" in series_response.get_data(as_text=True)
    class_response = client.get("/relatorios/escolas/inst-001/series/ser-003/turmas/tur-001")
    class_content = class_response.get_data(as_text=True)
    assert class_response.status_code == 200
    assert "Desempenho dos estudantes" in class_content
    assert "Ana Clara Souza" in class_content


def test_report_metrics_open_student_relations_and_school_history(client):
    from app.models import StudentAttendanceSummary

    login_as(client, "school_coordinator")
    school = client.get("/relatorios/escolas/inst-001").get_data(as_text=True)
    assert "/relatorios/escolas/inst-001/estudantes/frequencia" in school
    assert "/relatorios/escolas/inst-001/estudantes/faltas" in school
    assert "/relatorios/escolas/inst-001/estudantes/todos" in school
    assert "/relatorios/escolas/inst-001/historico" in school

    attendance = client.get("/relatorios/escolas/inst-001/estudantes/frequencia")
    assert attendance.status_code == 200
    attendance_content = attendance.get_data(as_text=True)
    assert "Estudantes que compareceram" in attendance_content
    assert "Ana Clara Souza" in attendance_content

    absences = client.get("/relatorios/escolas/inst-001/estudantes/faltas")
    assert absences.status_code == 200
    assert "Estudantes que faltaram" in absences.get_data(as_text=True)
    assert "Sofia Ribeiro" in absences.get_data(as_text=True)

    all_students = client.get("/relatorios/escolas/inst-001/estudantes/todos")
    all_content = all_students.get_data(as_text=True)
    assert "Relação total de estudantes" in all_content
    assert "Ana Clara Souza" in all_content and "Sofia Ribeiro" in all_content

    scoped = client.get("/relatorios/escolas/inst-001/estudantes/todos?series_id=ser-003&class_id=tur-001").get_data(as_text=True)
    assert "Ana Clara Souza" in scoped and "João Pedro Alves" in scoped
    assert "Mariana Costa" not in scoped

    history = client.get("/relatorios/escolas/inst-001/historico")
    assert history.status_code == 200
    assert "Histórico da escola" in history.get_data(as_text=True)
    assert "2026" in history.get_data(as_text=True)
    with client.application.app_context():
        assert StudentAttendanceSummary.query.count() == 7


def test_reports_reject_unrelated_profiles(client):
    login_as(client, "teacher")
    assert client.get("/relatorios/").status_code == 403


def test_entry_redirects_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/acesso")


def test_unread_notifications_use_a_visible_numeric_badge(client):
    from app.data.notifications import add_role_notification

    login_as(client, "teacher")
    with client.application.app_context():
        add_role_notification(
            "teacher", "pro-001", "Nova solicitação", "Você recebeu uma nova solicitação.",
            "/simulados/solicitacoes", "assessment_request",
        )

    dashboard = client.get("/inicio").get_data(as_text=True)
    assert 'class="icon-button notification-button has-unread"' in dashboard
    assert 'aria-label="Notificações: 1 não lida"' in dashboard
    assert 'class="notification-button__badge" aria-hidden="true">1</span>' in dashboard

    client.get("/notificacoes")
    dashboard_after_reading = client.get("/inicio").get_data(as_text=True)
    assert "notification-button__badge" not in dashboard_after_reading


def test_free_login_accepts_empty_fields(client):
    response = client.post("/acesso", data={"username": "", "password": "", "profile": "student"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Olá, Ana" in response.get_data(as_text=True)


@pytest.mark.parametrize("profile,label", [
    ("student", "Aluno"),
    ("teacher", "Professor"),
    ("school_coordinator", "Coord. Colégio"),
    ("institute_coordinator", "Coord. Instituto"),
    ("it_admin", "Administrador/T.I."),
])
def test_quick_access_supports_all_profiles(client, profile, label):
    response = client.post(f"/acesso/rapido/{profile}", follow_redirects=True)
    assert response.status_code == 200
    assert label in response.get_data(as_text=True)


def test_teacher_sees_only_linked_students(client):
    login_as(client, "teacher")
    response = client.get("/academico/alunos")
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Ana Clara Souza" in content
    assert "Gabriel Freitas" not in content


def test_school_coordinator_cannot_access_other_school(client):
    login_as(client, "school_coordinator")
    response = client.get("/academico/instituicoes/inst-002")
    assert response.status_code == 403
    assert "Acesso restrito" in response.get_data(as_text=True)


def test_institute_coordinator_can_create_record(client):
    login_as(client, "institute_coordinator")
    response = client.post("/academico/municipios/novo", data={"nome": "Aquiraz", "uf": "CE"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Aquiraz" in response.get_data(as_text=True)
    assert "salvo no banco de dados" in response.get_data(as_text=True)


def test_filter_and_custom_error_pages(client):
    login_as(client, "it_admin")
    filtered = client.get("/academico/alunos?q=Mariana")
    missing = client.get("/pagina-inexistente")
    assert "Mariana Costa" in filtered.get_data(as_text=True)
    assert "Ana Clara Souza" not in filtered.get_data(as_text=True)
    assert missing.status_code == 404
    assert "Página não encontrada" in missing.get_data(as_text=True)


def test_math_question_bank_covers_primary_operations(client):
    from app.data.questions import QUESTIONS

    assert len(QUESTIONS) >= 16
    assert {question["disciplina"] for question in QUESTIONS} == {"Matemática"}
    assert {question["assunto"] for question in QUESTIONS} == {"Operações primárias"}
    assert {question["operacao"] for question in QUESTIONS} == {"Soma", "Subtração", "Multiplicação", "Divisão"}
    assert all(question["gabarito"] in question["alternativas"] for question in QUESTIONS)


def test_teacher_accesses_own_topics_and_questions_but_not_assessments(client):
    login_as(client, "teacher")
    questions = client.get("/questoes")
    assessments = client.get("/simulados")
    curriculum = client.get("/curriculo")
    assert questions.status_code == 200
    assert "Adicionar questão" in questions.get_data(as_text=True)
    assert assessments.status_code == 403
    assert curriculum.status_code == 200
    assert "Meus assuntos" in curriculum.get_data(as_text=True)
    assert "Matemática" in curriculum.get_data(as_text=True)
    assert "Língua Portuguesa" not in curriculum.get_data(as_text=True)


def test_teacher_manages_topics_only_for_assigned_subjects(client):
    from app.data.curriculum import TOPICS

    login_as(client, "teacher")
    assert client.get("/curriculo/materias/nova").status_code == 403
    assert client.post("/curriculo/assuntos/novo", data={"materia_id": "mat-002", "nome": "Produção textual"}).status_code == 403

    created = client.post("/curriculo/assuntos/novo", data={"materia_id": "mat-001", "nome": "Geometria plana"}, follow_redirects=True)
    topic = next(item for item in TOPICS if item["nome"] == "Geometria plana")
    assert created.status_code == 200
    assert topic["materia_id"] == "mat-001"
    assert "Editar" in created.get_data(as_text=True)
    assert "data-topic-delete-dialog" in created.get_data(as_text=True)

    edited = client.post(f"/curriculo/assuntos/{topic['id']}/editar", data={"nome": "Geometria básica"}, follow_redirects=True)
    assert edited.status_code == 200
    assert topic["nome"] == "Geometria básica"

    deleted = client.post(f"/curriculo/assuntos/{topic['id']}/excluir", follow_redirects=True)
    assert deleted.status_code == 200
    assert topic not in TOPICS
    assert "Assunto Geometria básica excluído" in deleted.get_data(as_text=True)


def test_used_topic_cannot_be_deleted(client):
    from app.data.curriculum import find_topic

    login_as(client, "teacher")
    response = client.post("/curriculo/assuntos/ass-001/excluir", follow_redirects=True)
    assert response.status_code == 200
    assert find_topic("ass-001") is not None
    assert "vinculado a questões ou materiais" in response.get_data(as_text=True)


def test_test_assessment_has_balanced_math_questions(client):
    from app.data.assessments import find_assessment
    from app.data.questions import find_question

    assessment = find_assessment("sim-2026-001")
    operations = [find_question(question_id)["operacao"] for question_id in assessment["question_ids"]]
    assert assessment["titulo"] == "Simulado teste - Operações primárias"
    assert len(operations) == 8
    assert all(operations.count(operation) == 2 for operation in {"Soma", "Subtração", "Multiplicação", "Divisão"})


def test_school_coordinator_requests_assessment_instead_of_scheduling(client):
    from app.data.assessments import ASSESSMENT_REQUESTS

    login_as(client, "school_coordinator")
    assert client.post("/simulados/sim-2026-001/agendar", data={"data": "20/10/2026"}).status_code == 403

    form = client.get("/simulados/solicitar")
    content = form.get_data(as_text=True)
    assert form.status_code == 200
    assert "Anos participantes" in content
    assert "Professores responsáveis" in content
    assert "Rafael Lima" in content
    assert "Renata Gomes" not in content

    response = client.post("/simulados/solicitar", data={
        "serie_ids": ["ser-002", "ser-003"],
        "materia_ids": ["mat-001", "mat-002"],
        "professor_mat-001": "pro-001",
        "professor_mat-002": "pro-002",
        "quantidade_mat-001": "3",
        "quantidade_mat-002": "2",
        "prazo": "2026-10-10",
        "observacoes": "Priorizar os conteúdos do segundo bimestre.",
    }, follow_redirects=True)
    assessment_request = ASSESSMENT_REQUESTS[0]
    assert response.status_code == 200
    assert assessment_request["instituicao_id"] == "inst-001"
    assert assessment_request["serie_ids"] == ["ser-002", "ser-003"]
    assert assessment_request["atribuicoes"] == [
        {"materia_id": "mat-001", "professor_id": "pro-001", "quantidade_questoes": 3, "entregas": []},
        {"materia_id": "mat-002", "professor_id": "pro-002", "quantidade_questoes": 2, "entregas": []},
    ]
    assert "Priorizar os conteúdos" in response.get_data(as_text=True)

    login_as(client, "institute_coordinator")
    institute_view = client.get("/simulados").get_data(as_text=True)
    assert "Solicitações dos colégios" in institute_view
    assert "Escola Horizonte" in institute_view


def test_assessment_request_rejects_teacher_outside_subject_or_school(client):
    login_as(client, "school_coordinator")
    response = client.post("/simulados/solicitar", data={
        "serie_ids": "ser-003",
        "materia_ids": "mat-001",
        "professor_mat-001": "pro-004",
        "quantidade_mat-001": "5",
    })
    assert response.status_code == 400
    assert "professor habilitado" in response.get_data(as_text=True)


def test_institute_coordinator_can_publish_assessment(client):
    from app.data.assessments import find_assessment

    login_as(client, "institute_coordinator")
    response = client.post("/simulados/sim-2026-001/publicar", follow_redirects=True)
    assert response.status_code == 200
    assert find_assessment("sim-2026-001")["status"] == "Publicado"
    assert "publicado e salvo no banco de dados" in response.get_data(as_text=True)


def test_user_filters_support_municipality_and_institution(client):
    login_as(client, "it_admin")
    by_municipality = client.get("/academico/professores?municipio_id=mun-002")
    by_institution = client.get("/academico/professores?instituicao_id=inst-001")
    municipality_content = by_municipality.get_data(as_text=True)
    institution_content = by_institution.get_data(as_text=True)
    assert "Diego Rocha" in municipality_content
    assert "Rafael Lima" not in municipality_content
    assert "Rafael Lima" in institution_content
    assert "Diego Rocha" not in institution_content


@pytest.mark.parametrize("field,value", [
    ("cpf", "201.234.567-89"),
    ("email", "RAFAEL.LIMA@ifp.edu.br"),
])
def test_duplicate_cpf_or_email_blocks_new_user(client, field, value):
    from app.data.academic import DATA

    login_as(client, "school_coordinator")
    before = len(DATA["professores"])
    data = {
        "nome": "Professor Duplicado",
        "cpf": "29999999999",
        "email": "duplicado@ifp.edu.br",
        "disciplina_ids": "mat-001",
        "instituicao_id": "inst-002",
    }
    data[field] = value
    response = client.post("/academico/professores/novo", data=data)
    assert response.status_code == 400
    assert "já cadastrado" in response.get_data(as_text=True)
    assert len(DATA["professores"]) == before


def test_school_coordinator_creates_teacher_only_in_own_institution(client):
    from app.data.academic import DATA

    login_as(client, "school_coordinator")
    response = client.post("/academico/professores/novo", data={
        "nome": "Marta Freire",
        "cpf": "29999999999",
        "email": "marta.freire@ifp.edu.br",
        "disciplina_ids": ["mat-001", "mat-002"],
        "instituicao_id": "inst-002",
    }, follow_redirects=True)
    teacher = next(item for item in DATA["professores"] if item["email"] == "marta.freire@ifp.edu.br")
    assert response.status_code == 200
    assert teacher["instituicao_id"] == "inst-001"
    assert teacher["disciplina_ids"] == ["mat-001", "mat-002"]


def test_curriculum_scope_follows_coordinator_role(client):
    from app.data.curriculum import SUBJECTS

    login_as(client, "school_coordinator")
    client.post("/curriculo/materias/nova", data={"nome": "Robótica", "escopo": "global", "instituicao_id": "inst-002"})
    school_subject = next(item for item in SUBJECTS if item["nome"] == "Robótica")
    assert school_subject["escopo"] == "instituicao"
    assert school_subject["instituicao_id"] == "inst-001"

    login_as(client, "institute_coordinator")
    client.post("/curriculo/materias/nova", data={"nome": "Geografia", "escopo": "instituicao", "instituicao_id": "inst-002"})
    global_subject = next(item for item in SUBJECTS if item["nome"] == "Geografia")
    assert global_subject["escopo"] == "global"
    assert global_subject["instituicao_id"] == ""


def test_question_bank_requires_subject_then_topic(client):
    login_as(client, "institute_coordinator")
    initial = client.get("/questoes")
    selected = client.get("/questoes?materia_id=mat-001&assunto_id=ass-001")
    assert "Selecione matéria e assunto" in initial.get_data(as_text=True)
    assert "Qual é o resultado de 27 + 15?" in selected.get_data(as_text=True)


def test_it_cannot_access_coordinator_content_modules(client):
    login_as(client, "it_admin")
    assert client.get("/questoes").status_code == 403
    assert client.get("/simulados").status_code == 403
    assert client.get("/curriculo").status_code == 403


def test_teacher_creates_question_only_for_own_institution(client):
    from app.data.questions import QUESTIONS

    login_as(client, "teacher")
    response = client.post("/questoes/nova", data={
        "materia_id": "mat-001", "assunto_id": "ass-001", "instituicao_id": "inst-002",
        "operacao": "Soma", "dificuldade": "Fácil", "enunciado": "Quanto é 6 + 4?",
        "alternativa_a": "8", "alternativa_b": "9", "alternativa_c": "10", "alternativa_d": "11",
        "gabarito": "C", "explicacao": "6 + 4 = 10.",
    }, follow_redirects=True)
    question = next(item for item in QUESTIONS if item["enunciado"] == "Quanto é 6 + 4?")
    assert response.status_code == 200
    assert question["instituicao_id"] == "inst-001"
    assert question["autor_id"] == "pro-001"


@pytest.mark.parametrize("profile", ["school_coordinator", "institute_coordinator"])
def test_coordinators_cannot_create_or_edit_questions(client, profile):
    login_as(client, profile)
    assert client.get("/questoes/nova").status_code == 403
    assert client.get("/questoes/que-001/editar").status_code == 403


def test_coordinator_requests_revision_and_teacher_receives_it(client):
    from app.data.questions import find_question

    login_as(client, "school_coordinator")
    detail = client.get("/questoes/que-001").get_data(as_text=True)
    assert "Solicitar revisão" in detail
    assert "Editar questão" not in detail

    response = client.post("/questoes/que-001/solicitar-revisao", data={
        "observacao": "Revise a clareza do enunciado e confirme o gabarito."
    }, follow_redirects=True)
    question = find_question("que-001")
    assert response.status_code == 200
    assert question["revisao_status"] == "Pendente"
    assert "Revise a clareza" in response.get_data(as_text=True)

    login_as(client, "teacher")
    teacher_view = client.get("/questoes/que-001").get_data(as_text=True)
    assert "Iniciar revisão" in teacher_view
    assert "Revise a clareza" in teacher_view


def test_school_coordinator_cannot_change_global_subject(client):
    login_as(client, "school_coordinator")
    response = client.post("/curriculo/assuntos/novo", data={"materia_id": "mat-001", "nome": "Álgebra"})
    assert response.status_code == 403


def test_school_coordinator_cannot_manage_topics(client):
    login_as(client, "school_coordinator")
    listing = client.get("/curriculo").get_data(as_text=True)
    assert "Adicionar matéria" in listing
    assert "Adicionar assunto" not in listing
    assert "data-topic-delete" not in listing
    assert client.get("/curriculo/assuntos/novo").status_code == 403
    assert client.get("/curriculo/assuntos/ass-001/editar").status_code == 403
    assert client.post("/curriculo/assuntos/ass-001/excluir").status_code == 403


def test_cpf_is_kept_private_in_lists_and_details(client):
    login_as(client, "institute_coordinator")
    listing = client.get("/academico/professores").get_data(as_text=True)
    detail = client.get("/academico/professores/pro-001").get_data(as_text=True)
    assert "20123456789" not in listing
    assert "20123456789" not in detail


def test_institute_coordinator_transfers_teacher(client):
    from app.data.academic import find

    login_as(client, "institute_coordinator")
    response = client.post("/academico/professores/pro-005/transferir", data={"instituicao_id": "inst-002"}, follow_redirects=True)
    assert response.status_code == 200
    assert find("professores", "pro-005")["instituicao_id"] == "inst-002"
    assert find("professores", "pro-005")["turma_ids"] == []
    assert "foi transferido" in response.get_data(as_text=True)


def test_school_coordinator_cannot_transfer_teacher(client):
    login_as(client, "school_coordinator")
    response = client.post("/academico/professores/pro-001/transferir", data={"instituicao_id": "inst-002"})
    assert response.status_code == 403


def test_student_dashboard_shows_assessments_and_review(client):
    login_as(client, "student")
    response = client.get("/inicio")
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Meus simulados" in content
    assert "Materiais de revisão" in content
    assert 'class="role-student"' in content
    assert "student-home-hero" in content
    assert "O que você quer fazer?" in content


def test_student_assessment_interface_shows_clear_actions_and_progress(client):
    login_as(client, "student")
    listing = client.get("/aluno/simulados").get_data(as_text=True)
    test_page = client.get("/aluno/simulados/sim-2026-001/responder").get_data(as_text=True)
    assert "student-assessment-card__action" in listing
    assert "Ver simulado" in listing
    assert "data-assessment-progress" in test_page
    assert "data-answered-count" in test_page
    assert 'aria-valuemax="8"' in test_page


def test_student_sees_only_safe_assessment_view(client):
    login_as(client, "student")
    listing = client.get("/aluno/simulados")
    test_page = client.get("/aluno/simulados/sim-2026-001/responder")
    content = test_page.get_data(as_text=True)
    assert listing.status_code == 200
    assert "Simulado teste - Operações primárias" in listing.get_data(as_text=True)
    assert test_page.status_code == 200
    assert "Qual é o resultado de 27 + 15?" in content
    assert "Gabarito" not in content
    assert "Resolução esperada" not in content


def test_student_can_submit_assessment_and_receive_result(client):
    login_as(client, "student")
    response = client.post("/aluno/simulados/sim-2026-001/responder", data={
        "resposta_que-001": "B",
        "resposta_que-003": "B",
        "resposta_que-005": "A",
        "resposta_que-007": "B",
        "resposta_que-009": "C",
        "resposta_que-011": "C",
        "resposta_que-013": "B",
        "resposta_que-015": "C",
    })
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "8 de 8 respostas corretas" in content
    assert "Revisar assuntos" in content


def test_student_cannot_submit_assessment_with_blank_answers(client):
    login_as(client, "student")
    response = client.post("/aluno/simulados/sim-2026-001/responder", data={
        "resposta_que-001": "B",
        "resposta_que-003": "B",
    })
    content = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Existem questões em branco" in content
    assert "Questão 3" in content
    assert "Questão 8" in content
    assert 'resposta_que-001" value="B" checked' in content
    assert "Resultado do simulado" not in content


def test_student_review_contains_primary_operations(client):
    login_as(client, "student")
    response = client.get("/aluno/revisao")
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Operações primárias" in content
    assert "Soma" in content
    assert "Subtração" in content
    assert "Multiplicação" in content
    assert "Divisão" in content


def test_review_materials_are_grouped_by_subject_and_topic(client):
    from app.data.materials import add_material

    with client.application.app_context():
        add_material({
            "titulo": "Leitura guiada",
            "descricao": "Roteiro de interpretação de texto.",
            "texto": "Leia o texto e identifique a ideia principal.",
            "professor_id": "pro-002",
            "materia_id": "mat-002",
            "assunto_id": "ass-003",
            "turma_ids": ["tur-001"],
            "anexo": None,
        })

    login_as(client, "student")
    content = client.get("/aluno/revisao").get_data(as_text=True)
    assert 'id="materia-mat-001"' in content
    assert 'id="materia-mat-002"' in content
    assert 'id="assunto-ass-001-titulo"' in content
    assert 'id="assunto-ass-003-titulo"' in content
    assert "Guia de operações primárias" in content
    assert "Leitura guiada" in content


def test_material_form_explains_subject_and_topic_classification(client):
    login_as(client, "teacher")
    content = client.get("/materiais/novo").get_data(as_text=True)
    assert "Organização na biblioteca" in content
    assert "Gerenciar meus assuntos" in content
    assert 'data-subject-select required' in content
    assert 'data-topic-select required' in content


def test_teacher_publishes_review_material_for_linked_class(client):
    login_as(client, "teacher")
    response = client.post("/materiais/novo", data={
        "titulo": "Exercícios para sexta-feira",
        "descricao": "Lista curta para reforçar as quatro operações.",
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "turma_ids": ["tur-001"],
        "texto": "Resolva cinco exercícios de cada operação.",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Exercícios para sexta-feira" in response.get_data(as_text=True)

    login_as(client, "student")
    student_view = client.get("/aluno/revisao").get_data(as_text=True)
    assert "Exercícios para sexta-feira" in student_view
    assert "Resolva cinco exercícios" in student_view


def test_teacher_can_attach_allowed_review_file(client):
    from app.data.materials import MATERIAL_POSTS
    from app.extensions import db

    login_as(client, "teacher")
    response = client.post("/materiais/novo", data={
        "titulo": "Slides de revisão",
        "descricao": "Apresentação usada durante a aula.",
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "turma_ids": "tur-001",
        "texto": "",
        "anexo": (BytesIO(b"conteudo demonstrativo"), "revisao.pptx"),
    }, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    material = next(item for item in MATERIAL_POSTS if item["titulo"] == "Slides de revisão")
    assert material["anexo"]["extensao"] == "PPTX"

    login_as(client, "student")
    attachment = client.get(f"/materiais/{material['id']}/anexo")
    assert attachment.status_code == 200
    assert attachment.data == b"conteudo demonstrativo"


def test_review_material_rejects_invalid_file_and_other_roles(client):
    login_as(client, "teacher")
    invalid = client.post("/materiais/novo", data={
        "titulo": "Arquivo inválido",
        "descricao": "Este formato não deve ser aceito.",
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "turma_ids": "tur-001",
        "anexo": (BytesIO(b"arquivo"), "programa.exe"),
    }, content_type="multipart/form-data")
    assert invalid.status_code == 400
    assert "PDF, PNG, PPT ou PPTX" in invalid.get_data(as_text=True)

    login_as(client, "student")
    assert client.get("/materiais/novo").status_code == 403


def test_teacher_edits_and_deletes_own_review_material(client):
    from app.data.materials import MATERIAL_POSTS

    login_as(client, "teacher")
    created = client.post("/materiais/novo", data={
        "titulo": "Material temporário",
        "descricao": "Texto antes da edição.",
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "turma_ids": "tur-001",
        "texto": "Conteúdo inicial.",
    })
    assert created.status_code == 302
    material = next(item for item in MATERIAL_POSTS if item["titulo"] == "Material temporário")

    edited = client.post(f"/materiais/{material['id']}/editar", data={
        "titulo": "Material atualizado",
        "descricao": "Texto depois da edição.",
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "turma_ids": ["tur-001", "tur-002"],
        "texto": "Conteúdo revisado.",
    }, follow_redirects=True)
    assert edited.status_code == 200
    assert material["titulo"] == "Material atualizado"
    assert material["turma_ids"] == ["tur-001", "tur-002"]
    assert "data-material-delete-dialog" in edited.get_data(as_text=True)

    deleted = client.post(f"/materiais/{material['id']}/excluir", follow_redirects=True)
    assert deleted.status_code == 200
    assert material not in MATERIAL_POSTS
    assert "Publicação excluída" in deleted.get_data(as_text=True)


def test_it_user_list_supports_order_and_filters(client):
    login_as(client, "it_admin")
    response = client.get("/usuarios?ordem=za&municipio_id=mun-001&instituicao_id=inst-001&cargo=teacher")
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert content.index("Rafael Lima") < content.index("Camila Mendes")
    assert "Ana Clara Souza" not in content
    assert "Helena Martins" not in content


def test_it_can_add_and_deactivate_user(client):
    from app.data.users import USER_ACCOUNTS

    login_as(client, "it_admin")
    response = client.post("/usuarios/novo", data={
        "nome": "Clara Monteiro",
        "cpf": "499.999.999-90",
        "email": "clara.monteiro@ifp.edu.br",
        "cargo": "teacher",
        "municipio_id": "mun-002",
        "instituicao_id": "inst-003",
    }, follow_redirects=True)
    assert response.status_code == 200
    user = next(item for item in USER_ACCOUNTS if item["email"] == "clara.monteiro@ifp.edu.br")
    assert user["municipio_id"] == "mun-002"
    assert "Clara Monteiro" in response.get_data(as_text=True)

    toggled = client.post(f"/usuarios/{user['id']}/status", follow_redirects=True)
    assert toggled.status_code == 200
    assert user["status"] == "Inativo"
    assert "agora está inativo" in toggled.get_data(as_text=True)


def test_user_management_is_it_only_and_keeps_identity_unique(client):
    login_as(client, "teacher")
    assert client.get("/usuarios").status_code == 403

    login_as(client, "it_admin")
    duplicate = client.post("/usuarios/novo", data={
        "nome": "Outro Rafael",
        "cpf": "201.234.567-89",
        "email": "outro.rafael@ifp.edu.br",
        "cargo": "teacher",
        "municipio_id": "mun-001",
        "instituicao_id": "inst-001",
    })
    assert duplicate.status_code == 400
    assert "já cadastrado" in duplicate.get_data(as_text=True)

    listing = client.get("/usuarios").get_data(as_text=True)
    assert "data-user-status-dialog" in listing
    assert "site-dialog--danger" in listing


def test_database_layer_persists_administrative_foundations():
    from app.extensions import db
    from app.models import Institution, Municipality, UserAccount

    app = create_app(TestConfig)
    client = app.test_client()
    login_as(client, "it_admin")
    response = client.post("/usuarios/novo", data={
        "nome": "Usuário Persistente",
        "cpf": "48888888880",
        "email": "persistente@ifp.edu.br",
        "cargo": "institute_coordinator",
        "municipio_id": "",
        "instituicao_id": "",
    })
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Municipality, "mun-001").name == "Fortaleza"
        assert db.session.get(Institution, "inst-001").municipality_id == "mun-001"
        persisted = UserAccount.query.filter_by(email="persistente@ifp.edu.br").one()
        assert persisted.name == "Usuário Persistente"
        assert persisted.role == "institute_coordinator"

    status = app.test_cli_runner().invoke(args=["db-status"])
    assert status.exit_code == 0
    assert "conectado e respondendo" in status.output


def test_it_navigation_hides_internal_component_catalog(client):
    login_as(client, "it_admin")
    content = client.get("/inicio").get_data(as_text=True)
    assert "Usuários" in content
    assert ">Componentes<" not in content


def test_question_editor_supports_bold_text_and_image_for_student(client):
    login_as(client, "teacher")
    response = client.post("/questoes/que-001/editar", data={
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "instituicao_id": "inst-001",
        "operacao": "Soma",
        "dificuldade": "Fácil",
        "enunciado": "Qual é o **resultado** de 27 + 15?",
        "alternativa_a": "32",
        "alternativa_b": "**42**",
        "alternativa_c": "52",
        "alternativa_d": "41",
        "gabarito": "B",
        "explicacao": "O resultado é **42**.",
        "imagem": (BytesIO(b"imagem demonstrativa"), "operacao.png"),
    }, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert "<strong>resultado</strong>" in response.get_data(as_text=True)

    login_as(client, "student")
    assessment = client.get("/aluno/simulados/sim-2026-001/responder")
    content = assessment.get_data(as_text=True)
    assert assessment.status_code == 200
    assert "<strong>resultado</strong>" in content
    assert "<strong>42</strong>" in content
    assert "/questoes/que-001/imagem" in content
    image = client.get("/questoes/que-001/imagem")
    assert image.status_code == 200
    assert image.data == b"imagem demonstrativa"


def test_question_image_size_limit_and_vertical_student_options(client):
    login_as(client, "teacher")
    response = client.post("/questoes/que-001/editar", data={
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "instituicao_id": "inst-001",
        "operacao": "Soma",
        "dificuldade": "Fácil",
        "enunciado": "Questão com imagem grande",
        "alternativa_a": "A",
        "alternativa_b": "B",
        "alternativa_c": "C",
        "alternativa_d": "D",
        "gabarito": "A",
        "imagem": (BytesIO(b"x" * (2 * 1024 * 1024 + 1)), "grande.png"),
    }, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "no máximo 2 MB" in response.get_data(as_text=True)

    css = client.get("/static/css/question-editor.css").get_data(as_text=True)
    assert ".student-answer-list { grid-template-columns: 1fr; }" in css
    assert "grid-template-columns: 32px minmax(0, 1fr)" in css
    assert ".student-question legend > .student-question__text" in css
    assert "color: var(--text-primary)" in css


def test_question_bold_markup_escapes_html(client):
    login_as(client, "teacher")
    response = client.post("/questoes/que-001/editar", data={
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "instituicao_id": "inst-001",
        "operacao": "Soma",
        "dificuldade": "Fácil",
        "enunciado": "**Importante** <script>alert(1)</script>",
        "alternativa_a": "1",
        "alternativa_b": "2",
        "alternativa_c": "3",
        "alternativa_d": "4",
        "gabarito": "A",
    }, follow_redirects=True)
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<strong>Importante</strong>" in content
    assert "<script>alert(1)</script>" not in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content


def test_student_assessment_has_persistent_countdown_timer(client):
    login_as(client, "student")
    response = client.get("/aluno/simulados/sim-2026-001/responder")
    content = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "data-assessment-timer" in content
    assert 'data-duration-minutes="40"' in content
    assert "Tempo restante" in content

    css = client.get("/static/css/question-editor.css").get_data(as_text=True)
    assert ".assessment-timer" in css
    assert "border-radius: 999px" in css
    assert "background: var(--brand-navy-700)" in css


def test_open_question_accepts_typed_answer_and_waits_for_review(client):
    from app.data.assessments import find_assessment
    from app.data.questions import QUESTIONS

    login_as(client, "teacher")
    created = client.post("/questoes/nova", data={
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "instituicao_id": "inst-001",
        "tipo": "aberta",
        "operacao": "Geral",
        "dificuldade": "Média",
        "enunciado": "Explique como identificar a operação adequada.",
        "resposta_esperada": "O aluno deve relacionar o contexto às quatro operações.",
        "explicacao": "Resposta avaliada pela coordenação.",
    }, follow_redirects=True)
    assert created.status_code == 200
    question = next(item for item in QUESTIONS if item["enunciado"] == "Explique como identificar a operação adequada.")
    assert question["tipo"] == "aberta"
    assert question["alternativas"] == {}
    assessment = find_assessment("sim-2026-001")
    assessment["question_ids"].append(question["id"])

    login_as(client, "student")
    page = client.get("/aluno/simulados/sim-2026-001/responder")
    content = page.get_data(as_text=True)
    assert f'name="resposta_{question["id"]}"' in content
    assert "Digite sua resposta" in content

    answers = {
        "resposta_que-001": "B", "resposta_que-003": "B", "resposta_que-005": "A", "resposta_que-007": "B",
        "resposta_que-009": "C", "resposta_que-011": "C", "resposta_que-013": "B", "resposta_que-015": "C",
    }
    incomplete = client.post("/aluno/simulados/sim-2026-001/responder", data=answers)
    assert incomplete.status_code == 400
    assert "Questão 9" in incomplete.get_data(as_text=True)

    answers[f"resposta_{question['id']}"] = "A situação informa se devemos juntar, retirar, repetir ou repartir."
    completed = client.post("/aluno/simulados/sim-2026-001/responder", data=answers)
    completed_content = completed.get_data(as_text=True)
    assert completed.status_code == 200
    assert "1 resposta aguardando correção" in completed_content
    assert "A situação informa se devemos juntar" in completed_content


def test_assessment_page_includes_copy_print_and_focus_deterrents(client):
    login_as(client, "student")
    page = client.get("/aluno/simulados/sim-2026-001/responder").get_data(as_text=True)
    assert "data-protected-assessment" in page
    assert "data-assessment-protection-dialog" in page
    assert "data-assessment-privacy-screen" in page

    script = client.get("/static/js/app.js").get_data(as_text=True)
    assert '["copy", "cut", "paste", "contextmenu", "dragstart"]' in script
    assert 'event.key === "PrintScreen"' in script
    assert 'window.addEventListener("blur"' in script

    css = client.get("/static/css/question-editor.css").get_data(as_text=True)
    assert "@media print" in css
    assert "Impressão bloqueada durante o simulado" in css


def test_requested_assessment_flows_from_teacher_to_student_notification(client):
    from app.data.assessments import ASSESSMENT_REQUESTS, find_assessment
    from app.data.notifications import notifications_for_student

    login_as(client, "school_coordinator")
    created = client.post("/simulados/solicitar", data={
        "serie_ids": "ser-003",
        "materia_ids": "mat-001",
        "professor_mat-001": "pro-001",
        "quantidade_mat-001": "1",
        "prazo": "2026-10-20",
        "observacoes": "Enviar uma questão sobre operações primárias.",
    })
    assert created.status_code == 302
    assessment_request = ASSESSMENT_REQUESTS[0]
    request_id = assessment_request["id"]
    blocked = client.post(f"/simulados/solicitacoes/{request_id}/agendar", data={
        "titulo": "Simulado de fluxo", "data": "2026-10-25", "duracao": "35",
    }, follow_redirects=True)
    assert "Aprove todas as questões" in blocked.get_data(as_text=True)

    login_as(client, "teacher")
    inbox = client.get("/simulados/solicitacoes-professor").get_data(as_text=True)
    assert "Solicitações de questões" in inbox
    assert "2026-10-20" in inbox
    submitted = client.post(f"/simulados/solicitacoes/{request_id}/responder", data={
        "bank_question_ids": "que-002",
    }, follow_redirects=True)
    assert "Questões enviadas" in submitted.get_data(as_text=True)

    login_as(client, "school_coordinator")
    review = client.post(
        f"/simulados/solicitacoes/{request_id}/questoes/que-002/solicitar-revisao",
        data={"observacao": "Inclua uma orientação mais clara no enunciado."},
        follow_redirects=True,
    )
    assert "Revisão solicitada" in review.get_data(as_text=True)

    login_as(client, "teacher")
    revised = client.post("/questoes/que-002/editar", data={
        "materia_id": "mat-001", "assunto_id": "ass-001", "instituicao_id": "inst-001",
        "tipo": "objetiva", "operacao": "Soma", "dificuldade": "Média",
        "enunciado": "Calcule 138 + 246 e marque a alternativa correta.",
        "alternativa_a": "374", "alternativa_b": "384", "alternativa_c": "394", "alternativa_d": "284",
        "gabarito": "B", "explicacao": "138 + 246 = 384.",
    })
    assert revised.status_code == 302
    assert assessment_request["atribuicoes"][0]["entregas"][0]["status"] == "Reenviada"

    login_as(client, "school_coordinator")
    approved = client.post(
        f"/simulados/solicitacoes/{request_id}/questoes/que-002/aprovar",
        follow_redirects=True,
    )
    assert "Pronto para agendar" in approved.get_data(as_text=True)
    scheduled = client.post(f"/simulados/solicitacoes/{request_id}/agendar", data={
        "titulo": "Simulado de fluxo", "data": "2026-10-25", "duracao": "35",
    }, follow_redirects=True)
    assert "alunos participantes foram notificados" in scheduled.get_data(as_text=True)
    assessment = find_assessment(assessment_request["assessment_id"])
    assert assessment["question_ids"] == ["que-002"]
    assert assessment["serie_ids"] == ["ser-003"]

    login_as(client, "student")
    notifications = client.get("/aluno/notificacoes").get_data(as_text=True)
    assert "Novo simulado agendado" in notifications
    assert "Simulado de fluxo" in notifications
    with client.application.app_context():
        assert notifications_for_student("alu-001")[0]["lida"] is True
    assert "Simulado de fluxo" in client.get("/aluno/simulados").get_data(as_text=True)


def test_new_question_is_saved_only_in_bank_even_with_stale_request_data(client):
    from app.data.assessments import ASSESSMENT_REQUESTS

    login_as(client, "school_coordinator")
    client.post("/simulados/solicitar", data={
        "serie_ids": "ser-003", "materia_ids": "mat-001", "professor_mat-001": "pro-001",
        "quantidade_mat-001": "1",
        "prazo": "2026-10-22",
    })
    assessment_request = ASSESSMENT_REQUESTS[0]
    login_as(client, "teacher")
    response = client.post("/questoes/nova", data={
        "solicitacao_id": assessment_request["id"], "materia_id": "mat-001", "assunto_id": "ass-001",
        "instituicao_id": "inst-001", "tipo": "aberta", "operacao": "Geral", "dificuldade": "Média",
        "enunciado": "Explique uma estratégia para dividir 144 por 12.",
        "resposta_esperada": "Explicar uma decomposição ou relação inversa.",
        "explicacao": "Há diferentes estratégias válidas.",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Questão salva no banco de dados" in response.get_data(as_text=True)
    assert assessment_request["atribuicoes"][0]["entregas"] == []


def test_teacher_must_send_exact_requested_question_count(client):
    from app.data.assessments import ASSESSMENT_REQUESTS
    from app.data.questions import QUESTIONS

    login_as(client, "school_coordinator")
    client.post("/simulados/solicitar", data={
        "serie_ids": "ser-003", "materia_ids": "mat-001", "professor_mat-001": "pro-001",
        "quantidade_mat-001": "2", "prazo": "2026-10-22",
    })
    assessment_request = ASSESSMENT_REQUESTS[0]
    assignment = assessment_request["atribuicoes"][0]
    request_url = f"/simulados/solicitacoes/{assessment_request['id']}/responder?materia_id=mat-001"
    question_ids = [
        item["id"] for item in QUESTIONS
        if item.get("autor_id") == "pro-001" and item.get("materia_id") == "mat-001"
    ][:3]
    assert len(question_ids) == 3

    login_as(client, "teacher")
    page = client.get(request_url).get_data(as_text=True)
    assert "Criar nova questão" not in page
    assert 'data-required-count="2"' in page
    assert "0 de 2 selecionadas" in page
    assert "data-question-selection-dialog" in page

    too_few = client.post(request_url, data={
        "materia_id": "mat-001", "bank_question_ids": question_ids[:1],
    })
    assert too_few.status_code == 400
    assert "Selecione exatamente 2" in too_few.get_data(as_text=True)
    assert assignment["entregas"] == []

    too_many = client.post(request_url, data={
        "materia_id": "mat-001", "bank_question_ids": question_ids,
    })
    assert too_many.status_code == 400
    assert "Selecione exatamente 2" in too_many.get_data(as_text=True)
    assert assignment["entregas"] == []

    exact = client.post(request_url, data={
        "materia_id": "mat-001", "bank_question_ids": question_ids[:2],
    }, follow_redirects=True)
    assert exact.status_code == 200
    assert "Questões enviadas" in exact.get_data(as_text=True)
    assert len(assignment["entregas"]) == 2


def test_question_revision_has_history_states_filter_approval_and_notifications(client):
    from app.data.questions import find_question
    from app.models import QuestionReviewEvent

    login_as(client, "school_coordinator")
    requested = client.post("/questoes/que-004/solicitar-revisao", data={
        "observacao": "Explique melhor o cálculo intermediário.",
    })
    assert requested.status_code == 302
    assert find_question("que-004")["revisao_status"] == "Pendente"

    login_as(client, "teacher")
    dashboard = client.get("/inicio").get_data(as_text=True)
    notices = client.get("/notificacoes").get_data(as_text=True)
    assert "Revisões pendentes" in dashboard
    assert "Revisão de questão solicitada" in notices
    started = client.post("/questoes/que-004/iniciar-revisao")
    assert started.status_code == 302
    assert find_question("que-004")["revisao_status"] == "Em revisão"
    revised = client.post("/questoes/que-004/editar", data={
        "materia_id": "mat-001", "assunto_id": "ass-001", "instituicao_id": "inst-001",
        "tipo": "objetiva", "operacao": "Soma", "dificuldade": "Difícil",
        "enunciado": "Determine a soma de 1.275 e 938 mostrando o cálculo.",
        "alternativa_a": "2.103", "alternativa_b": "2.113", "alternativa_c": "2.203", "alternativa_d": "2.213",
        "gabarito": "D", "explicacao": "1.275 + 938 = 2.213.",
    })
    assert revised.status_code == 302
    assert find_question("que-004")["revisao_status"] == "Revisada"

    login_as(client, "school_coordinator")
    filtered = client.get("/questoes?materia_id=mat-001&assunto_id=ass-001&revisao=Revisada").get_data(as_text=True)
    assert "Determine a soma" in filtered
    approved = client.post("/questoes/que-004/aprovar-revisao", follow_redirects=True)
    assert approved.status_code == 200
    assert find_question("que-004")["revisao_status"] == "Aprovada"
    assert "Histórico da revisão" in approved.get_data(as_text=True)
    with client.application.app_context():
        states = [item.status for item in QuestionReviewEvent.query.filter_by(question_id="que-004").order_by(QuestionReviewEvent.created_at).all()]
        assert states == ["Pendente", "Em revisão", "Revisada", "Aprovada"]


def test_attempt_recovers_answers_blocks_second_submission_and_open_answer_is_graded(client):
    from app.data.assessments import add_assessment
    from app.data.questions import add_question, find_question
    from app.models import AssessmentAttempt, AttemptAnswer

    open_question = add_question({
        "disciplina": "Matemática", "assunto": "Operações primárias", "materia_id": "mat-001", "assunto_id": "ass-001",
        "operacao": "Geral", "dificuldade": "Média", "enunciado": "Explique por que 12 × 3 resulta em 36.",
        "tipo": "aberta", "alternativas": {}, "gabarito": "", "resposta_esperada": "Relacionar três grupos de doze.",
        "explicacao": "Resposta discursiva.", "autor": "Rafael Lima", "autor_id": "pro-001", "instituicao_id": "inst-001",
        "revisao_status": "", "revisao_observacao": "", "imagem": None,
    })
    assessment = add_assessment({
        "titulo": "Simulado persistente", "disciplina": "Matemática", "assunto": "Operações primárias",
        "modalidade": "Remoto", "publico": "9º ano", "duracao": 30, "data": "30/10/2026", "status": "Publicado",
        "question_ids": ["que-001", open_question["id"]], "instituicao_ids": ["inst-001"], "serie_ids": ["ser-003"],
        "descricao": "Teste da tentativa persistente.", "tentativa_unica": True,
    })
    login_as(client, "student")
    objective_answer = find_question("que-001")["gabarito"]
    started = client.get(f"/aluno/simulados/{assessment['id']}/responder")
    assert started.status_code == 200
    saved = client.post(f"/aluno/simulados/{assessment['id']}/salvar", data={
        "resposta_que-001": objective_answer, f"resposta_{open_question['id']}": "São três grupos com doze elementos.",
    })
    assert saved.get_json()["saved"] is True
    recovered = client.get(f"/aluno/simulados/{assessment['id']}/responder").get_data(as_text=True)
    assert "São três grupos com doze elementos." in recovered
    delivered = client.post(f"/aluno/simulados/{assessment['id']}/responder", data={
        "resposta_que-001": objective_answer, f"resposta_{open_question['id']}": "São três grupos com doze elementos.",
    })
    assert "Correção pendente" in delivered.get_data(as_text=True)
    second = client.post(f"/aluno/simulados/{assessment['id']}/responder", data={
        "resposta_que-001": "A", f"resposta_{open_question['id']}": "Outra resposta.",
    })
    assert second.status_code == 302

    with client.application.app_context():
        attempt = AssessmentAttempt.query.filter_by(assessment_id=assessment["id"], student_id="alu-001").one()
        answer = AttemptAnswer.query.filter_by(attempt_id=attempt.id, question_id=open_question["id"]).one()
        assert attempt.started_at is not None and attempt.submitted_at is not None
        assert attempt.remaining_seconds <= attempt.duration_seconds
        attempt_id, answer_id = attempt.id, answer.id

    login_as(client, "teacher")
    queue = client.get("/simulados/correcoes").get_data(as_text=True)
    assert "Simulado persistente" in queue
    assert "Solicitações de correção" in queue
    assert "Histórico de correções" in queue
    assert 'id="correcoes-pendentes"' in queue
    corrected = client.post(f"/simulados/correcoes/{attempt_id}", data={
        f"nota_{answer_id}": "0.8", f"conceito_{answer_id}": "Muito bom",
        f"comentario_{answer_id}": "A relação entre grupos foi explicada corretamente.",
    }, follow_redirects=True)
    assert "Correção salva" in corrected.get_data(as_text=True)
    assert "Nenhuma correção pendente" in corrected.get_data(as_text=True)
    assert 'id="historico-correcoes"' in corrected.get_data(as_text=True)
    assert "Ver correção" in corrected.get_data(as_text=True)
    assert "média <strong>0.8</strong> de 1" in corrected.get_data(as_text=True)

    login_as(client, "student")
    result = client.get(f"/aluno/simulados/{assessment['id']}/resultado").get_data(as_text=True)
    assert "Resultado disponível" in result
    assert "1.8 de 2 pontos" in result
    assert "Muito bom" in result
    assert "A relação entre grupos" in result


def test_material_attachment_is_persisted_removed_and_access_controlled(client):
    from pathlib import Path
    from app.data.materials import MATERIAL_POSTS
    from app.extensions import db
    from app.models import StoredFile
    from app.storage import absolute_file_path

    login_as(client, "teacher")
    created = client.post("/materiais/novo", data={
        "titulo": "Arquivo permanente", "descricao": "Material armazenado em disco.",
        "materia_id": "mat-001", "assunto_id": "ass-001", "turma_ids": "tur-001",
        "anexo": (BytesIO(b"pdf permanente"), "atividade.pdf"),
    }, content_type="multipart/form-data")
    assert created.status_code == 302
    material = next(item for item in MATERIAL_POSTS if item["titulo"] == "Arquivo permanente")
    file_id = material["anexo"]["arquivo_id"]
    with client.application.app_context():
        stored = db.session.get(StoredFile, file_id)
        path = absolute_file_path(stored)
        assert stored.original_name == "atividade.pdf"
        assert stored.extension == "PDF"
        assert stored.size == len(b"pdf permanente")
        assert path.exists()

    login_as(client, "school_coordinator")
    assert client.get(f"/materiais/{material['id']}/anexo").status_code == 403
    login_as(client, "teacher")
    deleted = client.post(f"/materiais/{material['id']}/excluir")
    assert deleted.status_code == 302
    assert not path.exists()
    with client.application.app_context():
        assert db.session.get(StoredFile, file_id) is None


def test_domain_state_survives_application_restart():
    from pathlib import Path
    from uuid import uuid4

    database_file = Path(__file__).resolve().parents[1] / "tmp" / f"ifp-persistence-{uuid4()}.sqlite"
    database_file.parent.mkdir(parents=True, exist_ok=True)
    database_path = database_file.as_posix()

    class PersistentConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{database_path}"

    first_app = create_app(PersistentConfig)
    with first_app.app_context():
        from app.data.assessments import add_assessment, add_assessment_request
        from app.data.curriculum import add_subject, add_topic
        from app.data.materials import add_material
        from app.data.questions import add_question

        subject = add_subject("Geometria integrada", "global", "", "Teste")
        topic = add_topic("Formas planas", subject["id"], "Teste")
        question = add_question({
            "materia_id": subject["id"], "assunto_id": topic["id"], "instituicao_id": "inst-001",
            "autor_id": "pro-001", "disciplina": subject["nome"], "assunto": topic["nome"],
            "operacao": "Geometria", "dificuldade": "Fácil", "enunciado": "Quantos lados tem um quadrado?",
            "tipo": "objetiva", "alternativas": {"A": "3", "B": "4", "C": "5", "D": "6"},
            "gabarito": "B", "resposta_esperada": "", "explicacao": "Um quadrado tem quatro lados.",
            "autor": "Rafael Lima", "imagem": None, "revisao_status": "", "revisao_observacao": "",
        })
        assessment = add_assessment({
            "titulo": "Persistência completa", "disciplina": subject["nome"], "assunto": topic["nome"],
            "modalidade": "Remoto", "publico": "9º ano", "duracao": 20, "data": "20/10/2026",
            "question_ids": [question["id"]], "instituicao_ids": ["inst-001"], "serie_ids": ["ser-003"],
            "descricao": "Teste após reinício.",
        })
        assessment_request = add_assessment_request({
            "titulo": "Solicitação persistente", "instituicao_id": "inst-001", "serie_ids": ["ser-003"],
            "atribuicoes": [{"materia_id": subject["id"], "professor_id": "pro-001", "entregas": []}],
            "prazo": "2026-10-20", "observacoes": "",
        })
        material = add_material({
            "titulo": "Material persistente", "descricao": "Descrição", "texto": "Conteúdo",
            "professor_id": "pro-001", "materia_id": subject["id"], "assunto_id": topic["id"],
            "turma_ids": ["tur-001"], "anexo": None,
        })
        persisted_ids = subject["id"], topic["id"], question["id"], assessment["id"], assessment_request["id"], material["id"]
        from app.extensions import db
        db.engine.dispose()

    second_app = create_app(PersistentConfig)
    with second_app.app_context():
        from app.data.assessments import find_assessment, find_assessment_request
        from app.data.curriculum import find_subject, find_topic
        from app.data.materials import find_material
        from app.data.questions import find_question

        subject_id, topic_id, question_id, assessment_id, request_id, material_id = persisted_ids
        assert find_subject(subject_id)["nome"] == "Geometria integrada"
        assert find_topic(topic_id)["nome"] == "Formas planas"
        assert find_question(question_id)["enunciado"] == "Quantos lados tem um quadrado?"
        assert find_assessment(assessment_id)["titulo"] == "Persistência completa"
        assert find_assessment_request(request_id)["titulo"] == "Solicitação persistente"
        assert find_material(material_id)["titulo"] == "Material persistente"
        from app.extensions import db
        db.engine.dispose()
    database_file.unlink(missing_ok=True)
