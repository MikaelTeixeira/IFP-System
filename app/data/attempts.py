from datetime import UTC, datetime
from uuid import uuid4

from ..extensions import db
from ..models import AssessmentAttempt, AttemptAnswer
from .questions import find_question


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def find_attempt(assessment_id, student_id):
    return AssessmentAttempt.query.filter_by(assessment_id=assessment_id, student_id=student_id).order_by(AssessmentAttempt.started_at.desc()).first()


def get_or_create_attempt(assessment, student_id):
    attempt = find_attempt(assessment["id"], student_id)
    if attempt and (attempt.status == "Em andamento" or assessment.get("tentativa_unica", True)):
        return attempt
    duration_seconds = int(assessment.get("duracao", 40)) * 60
    attempt = AssessmentAttempt(
        id=str(uuid4()), assessment_id=assessment["id"], student_id=student_id,
        duration_seconds=duration_seconds, remaining_seconds=duration_seconds,
    )
    db.session.add(attempt)
    db.session.commit()
    return attempt


def remaining_seconds(attempt):
    if attempt.status != "Em andamento":
        return attempt.remaining_seconds
    elapsed = max(0, int((utcnow() - attempt.started_at).total_seconds()))
    return max(0, attempt.duration_seconds - elapsed)


def save_answers(attempt, questions, values):
    existing = {item.question_id: item for item in attempt.answers}
    for question in questions:
        value = values.get(f"resposta_{question['id']}", "").strip()
        answer = existing.get(question["id"])
        if not answer:
            answer = AttemptAnswer(
                id=str(uuid4()), attempt_id=attempt.id, question_id=question["id"],
                is_open=question.get("tipo") == "aberta",
            )
            db.session.add(answer)
        answer.answer_text = value
    attempt.remaining_seconds = remaining_seconds(attempt)
    db.session.commit()
    return {item.question_id: item.answer_text for item in attempt.answers}


def submit_attempt(attempt, questions, values):
    answers = save_answers(attempt, questions, values)
    missing = [index for index, question in enumerate(questions, start=1) if not answers.get(question["id"], "").strip()]
    if missing:
        return missing
    objective_score = 0
    has_open = False
    by_question = {item.question_id: item for item in attempt.answers}
    for question in questions:
        answer = by_question[question["id"]]
        if question.get("tipo") == "aberta":
            has_open = True
            answer.is_correct = None
        else:
            answer.is_correct = answer.answer_text == question.get("gabarito")
            objective_score += int(answer.is_correct)
    attempt.objective_score = objective_score
    attempt.remaining_seconds = remaining_seconds(attempt)
    attempt.submitted_at = utcnow()
    attempt.status = "Correção pendente" if has_open else "Resultado disponível"
    attempt.final_score = None if has_open else float(objective_score)
    db.session.commit()
    return []


def answers_map(attempt):
    return {item.question_id: item.answer_text for item in attempt.answers}


def attempts_with_pending_answers(teacher_id):
    attempts = []
    for attempt in AssessmentAttempt.query.filter_by(status="Correção pendente").order_by(AssessmentAttempt.submitted_at).all():
        pending = [answer for answer in attempt.answers if answer.is_open and answer.grade is None and (find_question(answer.question_id) or {}).get("autor_id") == teacher_id]
        if pending:
            attempts.append((attempt, pending))
    return attempts


def grade_open_answers(attempt, teacher_id, values):
    graded = 0
    for answer in attempt.answers:
        question = find_question(answer.question_id)
        if not answer.is_open or not question or question.get("autor_id") != teacher_id:
            continue
        raw_grade = values.get(f"nota_{answer.id}", "").strip().replace(",", ".")
        if not raw_grade:
            continue
        grade = float(raw_grade)
        if grade < 0 or grade > 1:
            raise ValueError("A nota de cada questão deve estar entre 0 e 1.")
        answer.grade = grade
        answer.concept = values.get(f"conceito_{answer.id}", "").strip() or None
        answer.feedback = values.get(f"comentario_{answer.id}", "").strip() or None
        answer.graded_at = utcnow()
        answer.grader_id = teacher_id
        graded += 1
    pending = [item for item in attempt.answers if item.is_open and item.grade is None]
    if not pending:
        attempt.final_score = float(attempt.objective_score) + sum(item.grade or 0 for item in attempt.answers if item.is_open)
        attempt.status = "Resultado disponível"
    db.session.commit()
    return graded, not pending
