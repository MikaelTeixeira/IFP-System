from datetime import UTC, datetime
from uuid import uuid4

from flask import current_app, url_for

from ..extensions import db
from ..models import AssessmentAttempt, AttemptAnswer, AttemptCorrection, Notification, Student
from .questions import find_question


PUBLISHED_STATES = ("Resultado disponível", "Correção pendente")


class AttemptExpiredError(Exception):
    pass


class AttemptClosedError(Exception):
    """The attempt left "Em andamento" (e.g. replaced by a paper result) while the student was answering."""


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


def lock_students(student_ids):
    """Lock student rows in id order before any write to their results.

    Paper publication, online submission, open-answer grading and rectification all
    take these locks first, so they never interleave on the same student's result.
    """
    ids = sorted(set(student_ids))
    if ids:
        Student.query.filter(Student.id.in_(ids)).order_by(Student.id).with_for_update().all()


def _lock_open_attempt(attempt):
    """Without the lock a student could finish an attempt the paper publication has
    just archived, leaving two active results for the same assessment."""
    lock_students([attempt.student_id])
    db.session.refresh(attempt)
    if attempt.status != "Em andamento":
        db.session.rollback()
        raise AttemptClosedError("Este simulado já foi encerrado para você.")


def _write_answers(attempt, questions, values):
    _lock_open_attempt(attempt)
    if remaining_seconds(attempt) <= 0:
        attempt.remaining_seconds = 0
        db.session.commit()
        raise AttemptExpiredError("O tempo do simulado foi encerrado.")
    existing = {item.question_id: item for item in attempt.answers}
    for question in questions:
        value = values.get(f"resposta_{question['id']}", "").strip()
        answer = existing.get(question["id"])
        if not answer:
            answer = AttemptAnswer(
                id=str(uuid4()), question_id=question["id"], is_open=question.get("tipo") == "aberta",
            )
            attempt.answers.append(answer)
        answer.answer_text = value
    attempt.remaining_seconds = remaining_seconds(attempt)
    return {item.question_id: item.answer_text for item in attempt.answers}


def save_answers(attempt, questions, values):
    answers = _write_answers(attempt, questions, values)
    db.session.commit()
    return answers


def submit_attempt(attempt, questions, values):
    """Save and grade in the same locked transaction, so the attempt cannot be replaced in between."""
    answers = _write_answers(attempt, questions, values)
    missing = [index for index, question in enumerate(questions, start=1) if not answers.get(question["id"], "").strip()]
    if missing:
        db.session.commit()
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
            answer.answer_key = question.get("gabarito")
            answer.is_correct = answer.answer_text == answer.answer_key
            objective_score += int(answer.is_correct)
    attempt.objective_score = objective_score
    attempt.remaining_seconds = remaining_seconds(attempt)
    attempt.submitted_at = utcnow()
    attempt.status = "Correção pendente" if has_open else "Resultado disponível"
    attempt.final_score = None if has_open else float(objective_score)
    db.session.commit()
    return []


def graded_answer_count(question_id):
    """Objective answers already graded with this question's key in a result that still counts."""
    if not question_id or not current_app.config.get("DATABASE_ENABLED"):
        return 0
    return (AttemptAnswer.query.join(AssessmentAttempt)
            .filter(AttemptAnswer.question_id == question_id, AttemptAnswer.is_open.is_(False),
                    AttemptAnswer.is_correct.isnot(None), AssessmentAttempt.status != "Substituída")
            .count())


def _score_text(scores):
    value = scores["final"] if scores["final"] is not None else scores["objective"]
    return f"{value:g}"


def rectify_attempt(attempt_id, kind, reason, profile, answers=None, keys=None):
    """Correct a published result in place; the previous values stay in an AttemptCorrection.

    `answers` fixes what was read on a card and `keys` the key an answer is graded
    against, both by question id. Returns None when nothing would change. The caller
    commits, so the correction joins its transaction.
    """
    reason = " ".join((reason or "").split())
    if len(reason) < 5:
        raise ValueError("Explique o motivo da retificação.")
    answers, keys = answers or {}, keys or {}
    attempt = db.session.get(AssessmentAttempt, attempt_id)
    if attempt:
        lock_students([attempt.student_id])
        attempt = AssessmentAttempt.query.filter_by(id=attempt_id).populate_existing().one()
    if not attempt or attempt.status not in PUBLISHED_STATES:
        raise ValueError("Este resultado não está publicado e não pode ser retificado.")
    graded = {answer.question_id: answer for answer in attempt.answers if not answer.is_open}
    if set(answers) - set(graded) or set(keys) - set(graded):
        raise ValueError("A retificação cita uma questão que não faz parte deste resultado.")
    changes = []
    for question_id in sorted(set(answers) | set(keys)):
        answer = graded[question_id]
        used_key = answer.graded_key((find_question(question_id) or {}).get("gabarito"))
        text, key = answers.get(question_id, answer.answer_text), keys.get(question_id, used_key)
        if not key:
            raise ValueError("O gabarito usado na correção desta questão não está registrado.")
        correct = bool(text) and text == key
        if (text, key, correct) == (answer.answer_text, used_key, answer.is_correct):
            continue
        changes.append({"question_id": question_id, "answer": [answer.answer_text, text],
                        "key": [used_key, key], "correct": [answer.is_correct, correct]})
        answer.answer_text, answer.answer_key, answer.is_correct = text, key, correct
    if not changes:
        return None
    before = {"objective": attempt.objective_score, "final": attempt.final_score}
    attempt.objective_score = float(sum(bool(answer.is_correct) for answer in graded.values()))
    if attempt.status == "Resultado disponível":
        attempt.final_score = attempt.objective_score + sum(
            answer.grade or 0 for answer in attempt.answers if answer.is_open)
    after = {"objective": attempt.objective_score, "final": attempt.final_score}
    correction = AttemptCorrection(
        id=str(uuid4()), attempt_id=attempt.id, kind=kind, reason=reason[:500],
        details={"changes": changes, "objective": [before["objective"], after["objective"]],
                 "final": [before["final"], after["final"]]},
        actor_role=profile["key"], actor_id=profile.get("account_id", "global"),
    )
    db.session.add(correction)
    if before != after:
        from .assessments import find_assessment

        title = (find_assessment(attempt.assessment_id) or {}).get("titulo", "Simulado")
        db.session.add(Notification(
            id=str(uuid4()), recipient_role="student", recipient_id=attempt.student_id,
            kind="result_rectified", title="Resultado revisado",
            message=f"{title}: nota {_score_text(before)} → {_score_text(after)}. Motivo: {reason}",
            url=url_for("student_area.assessment_result", assessment_id=attempt.assessment_id),
        ))
    return correction


def answers_graded_with_other_key(question, student_ids=None):
    """Published answers of an objective question graded with a key other than its current one."""
    if not current_app.config.get("DATABASE_ENABLED") or question.get("tipo") == "aberta":
        return []
    key = question.get("gabarito")
    query = (AttemptAnswer.query.join(AssessmentAttempt)
             .filter(AttemptAnswer.question_id == question["id"], AttemptAnswer.is_open.is_(False),
                     AssessmentAttempt.status.in_(PUBLISHED_STATES)))
    if student_ids is not None:
        query = query.filter(AssessmentAttempt.student_id.in_(list(student_ids)))
    return [answer for answer in query.all() if answer.graded_key(key) != key]


def regrade_question(question, reason, profile, student_ids=None):
    """Regrade, with the question's current key, every published answer graded with another one."""
    try:
        stale = answers_graded_with_other_key(question, student_ids)
        lock_students(answer.attempt.student_id for answer in stale)
        corrections = [
            rectify_attempt(attempt_id, "gabarito", reason, profile, keys={question["id"]: question["gabarito"]})
            for attempt_id in sorted({answer.attempt_id for answer in stale})
        ]
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return [item for item in corrections if item]


def corrections_for(attempt_id):
    return (AttemptCorrection.query.filter_by(attempt_id=attempt_id)
            .order_by(AttemptCorrection.created_at).all())


def answers_map(attempt):
    return {item.question_id: item.answer_text for item in attempt.answers}


def attempts_with_pending_answers(teacher_id):
    attempts = []
    for attempt in AssessmentAttempt.query.filter_by(status="Correção pendente").order_by(AssessmentAttempt.submitted_at).all():
        pending = [answer for answer in attempt.answers if answer.is_open and answer.grade is None and (find_question(answer.question_id) or {}).get("autor_id") == teacher_id]
        if pending:
            attempts.append((attempt, pending))
    return attempts


def attempts_with_graded_answers(teacher_id):
    attempts = []
    for attempt in AssessmentAttempt.query.order_by(AssessmentAttempt.submitted_at.desc()).all():
        graded = [
            answer for answer in attempt.answers
            if answer.is_open and answer.grade is not None and answer.grader_id == teacher_id
        ]
        if graded:
            attempts.append((attempt, graded))
    attempts.sort(
        key=lambda item: max(
            (answer.graded_at for answer in item[1] if answer.graded_at),
            default=item[0].submitted_at or item[0].started_at,
        ),
        reverse=True,
    )
    return attempts


def grade_open_answers(attempt, teacher_id, values):
    # The final score adds the objective score, which a rectification may change meanwhile.
    lock_students([attempt.student_id])
    db.session.refresh(attempt)
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
