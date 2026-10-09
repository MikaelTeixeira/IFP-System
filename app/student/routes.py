from flask import abort, jsonify, redirect, render_template, request, url_for

from . import student_bp
from ..auth.security import current_profile, roles_required
from ..data.academic import DATA, find
from ..data.assessments import ASSESSMENTS, find_assessment
from ..data.curriculum import subject_name, topic_name
from ..data.materials import MATERIAL_POSTS, group_materials
from ..data.questions import find_question
from ..data.notifications import mark_profile_notifications_read, notifications_for_student
from ..data.notifications import add_role_notification
from ..data.attempts import AttemptClosedError, AttemptExpiredError, answers_map, corrections_for, find_attempt, get_or_create_attempt, remaining_seconds, save_answers, submit_attempt


def student_record():
    return find("alunos", current_profile()["student_id"])


def available_assessments():
    student = student_record()
    school_class = find("turmas", student["turma_id"])
    return [
        item for item in ASSESSMENTS
        if item["status"] in {"Publicado", "Agendado"}
        and student["instituicao_id"] in item.get("instituicao_ids", [])
        and (not item.get("serie_ids") or school_class["serie_id"] in item["serie_ids"])
    ]


@student_bp.get("/notificacoes")
@roles_required("student")
def notifications():
    records = notifications_for_student(current_profile()["student_id"])
    mark_profile_notifications_read(current_profile())
    return render_template(
        "student/notifications.html",
        page_title="Notificações",
        notifications=records,
        active_navigation="notificacoes",
    )


def assessment_or_404(assessment_id):
    assessment = find_assessment(assessment_id)
    if not assessment:
        abort(404)
    if assessment not in available_assessments():
        abort(403)
    return assessment


@student_bp.get("/simulados")
@roles_required("student")
def assessments():
    student_id = current_profile()["student_id"]
    records = available_assessments()
    return render_template(
        "student/assessments.html",
        page_title="Meus simulados",
        assessments=records,
        attempt_statuses={item["id"]: (find_attempt(item["id"], student_id).status if find_attempt(item["id"], student_id) else "Não iniciado") for item in records},
        active_navigation="meus-simulados",
    )


@student_bp.get("/simulados/<assessment_id>")
@roles_required("student")
def assessment_detail(assessment_id):
    assessment = assessment_or_404(assessment_id)
    attempt = find_attempt(assessment_id, current_profile()["student_id"])
    return render_template(
        "student/assessment_detail.html",
        page_title=assessment["titulo"],
        assessment=assessment,
        attempt=attempt,
        active_navigation="meus-simulados",
    )


@student_bp.route("/simulados/<assessment_id>/responder", methods=["GET", "POST"])
@roles_required("student")
def take_assessment(assessment_id):
    assessment = assessment_or_404(assessment_id)
    questions = [find_question(question_id) for question_id in assessment["question_ids"] if find_question(question_id)]
    attempt = get_or_create_attempt(assessment, current_profile()["student_id"])
    if attempt.status != "Em andamento" and request.method == "GET":
        return redirect(url_for("student_area.assessment_result", assessment_id=assessment_id))
    answers = answers_map(attempt)
    if request.method == "POST":
        if attempt.status != "Em andamento" and assessment.get("tentativa_unica", True):
            return redirect(url_for("student_area.assessment_result", assessment_id=assessment_id))
        try:
            missing_numbers = submit_attempt(attempt, questions, request.form)
        except AttemptClosedError:
            return redirect(url_for("student_area.assessment_result", assessment_id=assessment_id))
        except AttemptExpiredError:
            return render_template(
                "student/take_assessment.html", page_title=assessment["titulo"], assessment=assessment,
                questions=questions, answers=answers_map(attempt), remaining_seconds=0, missing_numbers=[],
                time_expired=True, active_navigation="meus-simulados",
            ), 409
        answers = answers_map(attempt)
        if missing_numbers:
            return render_template(
                "student/take_assessment.html",
                page_title=assessment["titulo"],
                assessment=assessment,
                questions=questions,
                answers=answers,
                remaining_seconds=remaining_seconds(attempt),
                missing_numbers=missing_numbers,
                active_navigation="meus-simulados",
            ), 400
        teacher_ids = {question["autor_id"] for question in questions if question.get("tipo") == "aberta" and question.get("autor_id")}
        for teacher_id in teacher_ids:
            add_role_notification("teacher", teacher_id, "Resposta aberta aguardando correção", assessment["titulo"], url_for("assessments.corrections"), "open_answer")
        return render_attempt_result(assessment, attempt)
    return render_template(
        "student/take_assessment.html",
        page_title=assessment["titulo"],
        assessment=assessment,
        questions=questions,
        answers=answers,
        remaining_seconds=remaining_seconds(attempt),
        missing_numbers=[],
        active_navigation="meus-simulados",
    )


@student_bp.post("/simulados/<assessment_id>/salvar")
@roles_required("student")
def save_assessment(assessment_id):
    assessment = assessment_or_404(assessment_id)
    attempt = get_or_create_attempt(assessment, current_profile()["student_id"])
    if attempt.status != "Em andamento":
        return jsonify({"saved": False, "status": attempt.status}), 409
    questions = [find_question(question_id) for question_id in assessment["question_ids"] if find_question(question_id)]
    try:
        save_answers(attempt, questions, request.form)
    except AttemptClosedError:
        return jsonify({"saved": False, "status": attempt.status}), 409
    except AttemptExpiredError:
        return jsonify({"saved": False, "status": "Tempo encerrado", "remaining_seconds": 0}), 409
    return jsonify({"saved": True, "remaining_seconds": remaining_seconds(attempt)})


def render_attempt_result(assessment, attempt):
    records = {item.question_id: item for item in attempt.answers}
    # A result shows the questions it was graded on, even if the assessment changed afterwards.
    order = {question_id: index for index, question_id in enumerate(assessment["question_ids"])}
    graded_ids = sorted(records, key=lambda question_id: (order.get(question_id, len(order)), question_id))
    questions = [find_question(question_id) for question_id in graded_ids or assessment["question_ids"]]
    questions = [question for question in questions if question]
    graded_keys = {
        question["id"]: records[question["id"]].graded_key(question.get("gabarito"))
        if question["id"] in records else question.get("gabarito")
        for question in questions
    }
    return render_template(
        "student/assessment_result.html", page_title="Resultado do simulado",
        assessment=assessment, attempt=attempt, questions=questions, graded_keys=graded_keys,
        corrections=corrections_for(attempt.id),
        answer_records=records, answers={key: item.answer_text for key, item in records.items()},
        correct=int(attempt.objective_score),
        objective_count=sum(item.get("tipo", "objetiva") == "objetiva" for item in questions),
        open_count=sum(item.get("tipo") == "aberta" for item in questions),
        active_navigation="meus-simulados",
    )


@student_bp.get("/simulados/<assessment_id>/resultado")
@roles_required("student")
def assessment_result(assessment_id):
    assessment = assessment_or_404(assessment_id)
    attempt = find_attempt(assessment_id, current_profile()["student_id"])
    if not attempt or attempt.status == "Em andamento":
        return redirect(url_for("student_area.take_assessment", assessment_id=assessment_id))
    return render_attempt_result(assessment, attempt)


@student_bp.get("/revisao")
@roles_required("student")
def review():
    student = student_record()
    materials = []
    for material in MATERIAL_POSTS:
        if student["turma_id"] not in material["turma_ids"]:
            continue
        item = dict(material)
        teacher = find("professores", material["professor_id"])
        item["professor"] = teacher["nome"] if teacher else "Professor"
        item["materia"] = subject_name(material["materia_id"])
        item["assunto"] = topic_name(material["assunto_id"])
        materials.append(item)
    return render_template(
        "student/review.html",
        page_title="Materiais de revisão",
        materials=materials,
        material_groups=group_materials(materials),
        active_navigation="revisao",
    )
