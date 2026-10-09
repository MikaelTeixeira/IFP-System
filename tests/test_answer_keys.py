"""A published grade keeps the key and the questions it was graded with."""
import re

import pytest
from sqlalchemy import inspect

from app import create_app
from app.config import TestConfig
from app.data.assessments import find_assessment
from app.data.questions import find_question
from app.data.reports import _load_scores_by_student
from app.data.attempts import rectify_attempt, regrade_question
from app.database import _add_missing_columns
from app.extensions import db
from app.models import AssessmentAttempt, AttemptAnswer, AttemptCorrection, Notification


ASSESSMENT_ID = "sim-2026-001"
STUDENT_ID = "alu-001"


@pytest.fixture()
def client():
    return create_app(TestConfig).test_client()


def login_as(client, profile):
    with client.session_transaction() as session:
        session["profile"] = profile


def submit_all_correct(client):
    questions = [find_question(question_id) for question_id in find_assessment(ASSESSMENT_ID)["question_ids"]]
    assert all(question.get("tipo", "objetiva") == "objetiva" for question in questions)
    login_as(client, "student")
    response = client.post(f"/aluno/simulados/{ASSESSMENT_ID}/responder",
                           data={f"resposta_{question['id']}": question["gabarito"] for question in questions})
    assert response.status_code == 200
    return questions, [question["gabarito"] for question in questions]


def test_online_result_keeps_its_key_and_scale_after_the_assessment_changes(client):
    questions, keys = submit_all_correct(client)
    with client.application.app_context():
        attempt = AssessmentAttempt.query.filter_by(assessment_id=ASSESSMENT_ID, student_id=STUDENT_ID).one()
        assert {answer.question_id: answer.answer_key for answer in attempt.answers} == {
            question["id"]: key for question, key in zip(questions, keys)}
        assert _load_scores_by_student()[STUDENT_ID] == [10.0]

    # The key of question 1 is corrected and a question is added after the grade was published.
    questions[0]["gabarito"] = next(letter for letter in "ABCD" if letter != keys[0])
    find_assessment(ASSESSMENT_ID)["question_ids"].append("que-002")

    page = client.get(f"/aluno/simulados/{ASSESSMENT_ID}/resultado").get_data(as_text=True)
    assert f"{len(keys)} de {len(keys)} respostas corretas" in page
    assert re.findall(r"Resposta correta: <b>([A-E])</b>", page) == keys
    assert "result-item is-wrong" not in page
    with client.application.app_context():
        assert _load_scores_by_student()[STUDENT_ID] == [10.0]


def test_editing_a_graded_question_warns_that_published_grades_keep_their_key(client):
    login_as(client, "it_admin")
    assert "já foi corrigida" not in client.get("/questoes/que-001/editar").get_data(as_text=True)
    submit_all_correct(client)
    login_as(client, "it_admin")
    form = client.get("/questoes/que-001/editar").get_data(as_text=True)
    assert "Esta questão já foi corrigida em 1 resposta." in form
    assert 'aria-describedby="gabarito-aviso"' in form


@pytest.mark.parametrize("stored,correct,answer,current,expected", [
    ("C", False, "B", "B", "C"),   # the stored key always wins
    (None, True, "B", "D", "B"),   # legacy right answer: it was its own key
    (None, False, "B", "C", "C"),  # legacy wrong answer: the current key still disagrees
    (None, False, "B", "B", None), # legacy wrong answer that the current key would accept
    (None, False, "", "C", "C"),   # blank answer
])
def test_graded_key_never_contradicts_the_stored_grade(stored, correct, answer, current, expected):
    record = AttemptAnswer(answer_key=stored, is_correct=correct, answer_text=answer, is_open=False)
    assert record.graded_key(current) == expected
    assert AttemptAnswer(is_open=True, answer_text="texto").graded_key(current) is None


def test_existing_database_gains_the_answer_key_column_once(client):
    with client.application.app_context():
        columns = lambda: {column["name"] for column in inspect(db.engine).get_columns("respostas")}
        db.session.execute(db.text("ALTER TABLE respostas DROP COLUMN gabarito"))
        db.session.commit()
        assert "gabarito" not in columns()
        _add_missing_columns()
        _add_missing_columns()
        assert "gabarito" in columns()


def form_token(client):
    with client.session_transaction() as session:
        return session["form_csrf"]


def test_changed_key_regrades_published_results_with_history(client):
    questions, keys = submit_all_correct(client)
    question = questions[0]
    new_key = next(letter for letter in "ABCD" if letter != keys[0])
    question["gabarito"] = new_key
    url = f"/questoes/{question['id']}"

    login_as(client, "teacher")
    assert client.post(url + "/recorrigir", data={"confirm_regrade": "yes"}).status_code == 403
    login_as(client, "institute_coordinator")
    detail = client.get(url).get_data(as_text=True)
    assert "1 resultado publicado usa outro gabarito" in detail
    assert client.post(url + "/recorrigir", data={"confirm_regrade": "yes", "reason": "Gabarito corrigido."}).status_code == 400
    reason = "O gabarito estava trocado na questão."
    response = client.post(url + "/recorrigir", data={"csrf_token": form_token(client), "confirm_regrade": "yes", "reason": reason},
                           follow_redirects=True)
    page = response.get_data(as_text=True)
    assert f"1 resultado(s) recorrigido(s) com o gabarito {new_key}. 1 nota(s) mudaram" in page
    assert "usa outro gabarito" not in page

    with client.application.app_context():
        attempt = AssessmentAttempt.query.filter_by(assessment_id=ASSESSMENT_ID, student_id=STUDENT_ID).one()
        assert (attempt.objective_score, attempt.final_score) == (len(keys) - 1, len(keys) - 1)
        answer = next(item for item in attempt.answers if item.question_id == question["id"])
        assert (answer.answer_text, answer.answer_key, answer.is_correct) == (keys[0], new_key, False)
        correction = AttemptCorrection.query.filter_by(attempt_id=attempt.id).one()
        assert correction.kind == "gabarito" and correction.reason == reason
        assert correction.details["changes"][0]["key"] == [keys[0], new_key]
        assert Notification.query.filter_by(recipient_id=STUDENT_ID, kind="result_rectified").count() == 1

    login_as(client, "student")
    result = client.get(f"/aluno/simulados/{ASSESSMENT_ID}/resultado").get_data(as_text=True)
    assert "Seu resultado foi revisado" in result
    assert f"nota {len(keys)} → {len(keys) - 1} · {reason}" in result
    assert re.findall(r"Resposta correta: <b>([A-E])</b>", result) == [new_key, *keys[1:]]


def test_regrade_only_touches_the_students_in_scope(client):
    questions, keys = submit_all_correct(client)
    questions[0]["gabarito"] = next(letter for letter in "ABCD" if letter != keys[0])
    with client.application.test_request_context():
        assert regrade_question(questions[0], "Gabarito corrigido.", {"key": "it_admin"}, student_ids={"alu-006"}) == []
        attempt = AssessmentAttempt.query.filter_by(assessment_id=ASSESSMENT_ID, student_id=STUDENT_ID).one()
        assert attempt.final_score == len(keys)
        assert AttemptCorrection.query.count() == 0


def test_rectification_keeps_open_grades_and_refuses_archived_results(client):
    with client.application.test_request_context():
        attempt = AssessmentAttempt(id="mixed", assessment_id=ASSESSMENT_ID, student_id=STUDENT_ID, status="Resultado disponível",
                                    duration_seconds=60, remaining_seconds=0, objective_score=1, final_score=1.5)
        attempt.answers = [
            AttemptAnswer(id="mixed-1", question_id="que-001", answer_text="A", answer_key="A", is_open=False, is_correct=True),
            AttemptAnswer(id="mixed-2", question_id="que-aberta", answer_text="texto", is_open=True, grade=.5),
        ]
        db.session.add(attempt)
        db.session.commit()
        correction = rectify_attempt("mixed", "gabarito", "Gabarito corrigido.", {"key": "it_admin"}, keys={"que-001": "B"})
        db.session.commit()
        assert correction.details["objective"] == [1, 0] and correction.details["final"] == [1.5, .5]
        assert rectify_attempt("mixed", "gabarito", "Gabarito corrigido.", {"key": "it_admin"}, keys={"que-001": "B"}) is None
        with pytest.raises(ValueError, match="não faz parte"):
            rectify_attempt("mixed", "gabarito", "Gabarito corrigido.", {"key": "it_admin"}, keys={"que-999": "B"})
        db.session.get(AssessmentAttempt, "mixed").status = "Substituída"
        db.session.commit()
        with pytest.raises(ValueError, match="não está publicado"):
            rectify_attempt("mixed", "gabarito", "Gabarito corrigido.", {"key": "it_admin"}, keys={"que-001": "A"})
