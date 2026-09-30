from uuid import uuid4

from ..extensions import db
from ..models import Notification


def add_role_notification(recipient_role, recipient_id, title, message, url, kind="general"):
    record = Notification(
        id=str(uuid4()), recipient_role=recipient_role, recipient_id=recipient_id,
        title=title, message=message, url=url, kind=kind,
    )
    db.session.add(record)
    db.session.commit()
    return record


def add_notification(student_id, title, message, url, kind="assessment"):
    return add_role_notification("student", student_id, title, message, url, kind)


def _record_dict(record):
    return {
        "id": record.id, "titulo": record.title, "mensagem": record.message,
        "url": record.url, "tipo": record.kind, "lida": record.is_read,
        "criada_em": record.created_at.strftime("%d/%m/%Y às %H:%M"),
    }


def notifications_for_recipient(role, recipient_id):
    records = Notification.query.filter_by(recipient_role=role, recipient_id=recipient_id).order_by(Notification.created_at.desc()).all()
    return [_record_dict(item) for item in records]


def notifications_for_student(student_id):
    return notifications_for_recipient("student", student_id)


def profile_recipient(profile):
    if profile["key"] == "student":
        return "student", profile["student_id"]
    if profile["key"] == "teacher":
        return "teacher", profile["teacher_id"]
    if profile["key"] == "school_coordinator":
        return "school_coordinator", profile["institution_id"]
    if profile["key"] == "institute_coordinator":
        return "institute_coordinator", "global"
    return profile["key"], "global"


def notifications_for_profile(profile):
    role, recipient_id = profile_recipient(profile)
    return notifications_for_recipient(role, recipient_id)


def unread_count(profile):
    role, recipient_id = profile_recipient(profile)
    return Notification.query.filter_by(recipient_role=role, recipient_id=recipient_id, is_read=False).count()


def mark_profile_notifications_read(profile):
    role, recipient_id = profile_recipient(profile)
    Notification.query.filter_by(recipient_role=role, recipient_id=recipient_id, is_read=False).update({"is_read": True})
    db.session.commit()
