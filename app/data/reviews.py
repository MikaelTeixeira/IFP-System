from uuid import uuid4

from ..auth.security import current_profile
from ..extensions import db
from ..models import QuestionReviewEvent


def actor_identity(profile=None):
    profile = profile or current_profile()
    if profile["key"] == "teacher":
        actor_id = profile["teacher_id"]
    elif profile["key"] == "school_coordinator":
        actor_id = profile["institution_id"]
    else:
        actor_id = "global"
    return actor_id


def add_review_event(question_id, status, note="", request_id=None, profile=None):
    profile = profile or current_profile()
    event = QuestionReviewEvent(
        id=str(uuid4()), question_id=question_id, request_id=request_id,
        status=status, note=note or None, actor_role=profile["key"],
        actor_id=actor_identity(profile), actor_name=profile["name"],
    )
    db.session.add(event)
    db.session.commit()
    return event


def review_history(question_id):
    return QuestionReviewEvent.query.filter_by(question_id=question_id).order_by(QuestionReviewEvent.created_at.desc()).all()
