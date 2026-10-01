from flask import redirect, render_template, url_for

from . import core_bp
from ..auth.security import current_profile, login_required, roles_required
from ..data.academic import DATA
from ..data.questions import QUESTIONS
from ..data.assessments import ASSESSMENTS, ASSESSMENT_REQUESTS
from ..data.demo import component_examples
from ..data.materials import MATERIAL_POSTS
from ..data.users import list_users
from ..data.notifications import mark_profile_notifications_read, notifications_for_profile
from ..data.attempts import attempts_with_pending_answers


@core_bp.get("/")
def index():
    return redirect(url_for("core.dashboard") if current_profile() else url_for("auth.login"))


@core_bp.get("/inicio")
@login_required
def dashboard():
    profile = current_profile()
    role = profile["key"]
    if role == "student":
        student = next(item for item in DATA["alunos"] if item["id"] == profile["student_id"])
        school_class = next(item for item in DATA["turmas"] if item["id"] == student["turma_id"])
        available_assessments = [item for item in ASSESSMENTS if item["status"] in {"Publicado", "Agendado"} and student["instituicao_id"] in item.get("instituicao_ids", []) and (not item.get("serie_ids") or school_class["serie_id"] in item["serie_ids"])]
        student_materials = [item for item in MATERIAL_POSTS if student["turma_id"] in item["turma_ids"]]
        summary = [("Meus simulados", str(len(available_assessments)), "student_area.assessments", {}), ("Materiais de revisão", str(len(student_materials)), "student_area.review", {}), ("Meu cadastro", "Dados acadêmicos", "academic.detail", {"entity": "alunos", "item_id": profile["student_id"]})]
    elif role == "teacher":
        teacher_materials = [item for item in MATERIAL_POSTS if item["professor_id"] == profile["teacher_id"]]
        teacher_questions = [item for item in QUESTIONS if item.get("autor_id") == profile["teacher_id"]]
        teacher_requests = [item for item in ASSESSMENT_REQUESTS if any(assignment["professor_id"] == profile["teacher_id"] for assignment in item.get("atribuicoes", []))]
        pending_corrections = attempts_with_pending_answers(profile["teacher_id"])
        pending_reviews = [item for item in teacher_questions if item.get("revisao_status") in {"Pendente", "Em revisão"}]
        summary = [("Revisões pendentes", str(len(pending_reviews)), "questions.list_questions", {"materia_id": "mat-001", "assunto_id": "ass-001", "revisao": "aguardando"}), ("Solicitações de questões", str(len(teacher_requests)), "assessments.teacher_requests", {}), ("Correções abertas", str(len(pending_corrections)), "assessments.corrections", {}), ("Banco de questões", str(len(teacher_questions)), "questions.list_questions", {}), ("Materiais de revisão", str(len(teacher_materials)), "materials.index", {})]
    elif role == "school_coordinator":
        institution_id = profile["institution_id"]
        school_requests = [item for item in ASSESSMENT_REQUESTS if item["instituicao_id"] == institution_id]
        summary = [("Desempenho da escola", "Relatório", "reports.index", {}), ("Turmas", str(len([item for item in DATA["turmas"] if item["instituicao_id"] == institution_id])), "academic.list_entities", {"entity": "turmas"}), ("Alunos", str(len([item for item in DATA["alunos"] if item["instituicao_id"] == institution_id])), "academic.list_entities", {"entity": "alunos"}), ("Solicitar simulado", str(len(school_requests)), "assessments.list_assessments", {})]
    elif role == "institute_coordinator":
        summary = [("Relatório das escolas", str(len(DATA["instituicoes"])), "reports.index", {}), ("Instituições", str(len(DATA["instituicoes"])), "academic.list_entities", {"entity": "instituicoes"}), ("Banco de questões", str(len(QUESTIONS)), "questions.list_questions", {}), ("Simulados", str(len(ASSESSMENTS)), "assessments.list_assessments", {})]
    else:
        summary = [
            ("Usuários", str(len(list_users())), "users.index", {}),
            ("Instituições", str(len(DATA["instituicoes"])), "academic.list_entities", {"entity": "instituicoes"}),
            ("Banco de questões", str(len(QUESTIONS)), "questions.list_questions", {}),
            ("Simulados", str(len(ASSESSMENTS)), "assessments.list_assessments", {}),
            ("Materiais de revisão", str(len(MATERIAL_POSTS)), "materials.index", {}),
        ]
    return render_template("dashboard/index.html", page_title=f"Olá, {profile['name'].split()[0]}", page_description=profile["description"], summary=summary, active_navigation="inicio")


@core_bp.get("/notificacoes")
@login_required
def notifications():
    profile = current_profile()
    records = notifications_for_profile(profile)
    mark_profile_notifications_read(profile)
    return render_template(
        "student/notifications.html", page_title="Notificações",
        notifications=records, active_navigation="notificacoes",
    )


@core_bp.get("/componentes")
@roles_required("it_admin")
def components():
    return render_template(
        "foundation/components.html",
        page_title="Referência de componentes",
        page_description=(
            "Variações visuais, mensagens e controles reutilizáveis da interface."
        ),
        examples=component_examples,
        active_navigation="componentes",
    )
