import hashlib
import hmac
from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID, uuid4

from flask import current_app

def _database_active():
    return current_app.config.get("DATABASE_ENABLED", False)


def _demo_store():
    return current_app.extensions.setdefault("answer_scanner", {"sheets": [], "batches": []})


def _signature(sheet_id):
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(secret, sheet_id.encode("ascii"), hashlib.sha256).hexdigest()[:24]


def token_for_sheet(sheet_id):
    return f"IFP1.{sheet_id}.{_signature(sheet_id)}"


def _sheet_record(model):
    return {
        "id": model.id, "assessment_id": model.assessment_id, "student_id": model.student_id,
        "template_version": model.template_version, "snapshot": deepcopy(model.snapshot or {}),
        "status": model.status, "token": token_for_sheet(model.id),
    }


def issue_sheet(assessment_id, student_id, snapshot):
    """Keep the question order and academic audience fixed to the issued paper."""
    from ..scanner.layout import TEMPLATE_VERSION

    if _database_active():
        from ..extensions import db
        from ..models import AnswerSheet

        candidates = AnswerSheet.query.filter_by(
            assessment_id=assessment_id, student_id=student_id, template_version=TEMPLATE_VERSION,
        ).all()
        model = next((item for item in candidates if item.snapshot == snapshot), None)
        if not model:
            sheet_id = str(uuid4())
            model = AnswerSheet(
                id=sheet_id, assessment_id=assessment_id, student_id=student_id,
                template_version=TEMPLATE_VERSION, snapshot=deepcopy(snapshot),
                token_digest=hashlib.sha256(token_for_sheet(sheet_id).encode("ascii")).hexdigest(),
            )
            db.session.add(model)
            db.session.commit()
        return _sheet_record(model)
    sheets = _demo_store()["sheets"]
    record = next((item for item in sheets if item["assessment_id"] == assessment_id
                   and item["student_id"] == student_id and item["snapshot"] == snapshot), None)
    if not record:
        sheet_id = str(uuid4())
        record = {
            "id": sheet_id, "assessment_id": assessment_id, "student_id": student_id,
            "template_version": TEMPLATE_VERSION, "snapshot": deepcopy(snapshot),
            "status": "Emitido", "token": token_for_sheet(sheet_id),
        }
        sheets.append(record)
    return deepcopy(record)


def get_sheet(sheet_id):
    if _database_active():
        from ..extensions import db
        from ..models import AnswerSheet

        model = db.session.get(AnswerSheet, sheet_id)
        return _sheet_record(model) if model else None
    return next((deepcopy(item) for item in _demo_store()["sheets"] if item["id"] == sheet_id), None)


def sheet_for_token(token):
    parts = (token or "").split(".")
    if len(parts) != 3 or parts[0] != "IFP1":
        return None
    try:
        if str(UUID(parts[1])) != parts[1] or not parts[2].isascii():
            return None
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(parts[2], _signature(parts[1])):
        return None
    sheet = get_sheet(parts[1])
    if _database_active() and sheet:
        from ..extensions import db
        from ..models import AnswerSheet

        model = db.session.get(AnswerSheet, parts[1])
        digest = hashlib.sha256(token.encode("ascii")).hexdigest()
        if not hmac.compare_digest(model.token_digest, digest):
            return None
    return sheet


def _batch_record(model):
    return {
        "id": model.id, "assessment_id": model.assessment_id, "original_name": model.original_name,
        "status": model.status, "page_count": model.page_count,
        "processed_count": model.processed_count, "review_count": model.review_count,
        "failed_count": model.failed_count, "scope": deepcopy(model.scope or {}),
        "error_message": model.error_message or "", "created_by_role": model.created_by_role,
        "created_by_id": model.created_by_id,
        "created_at": model.created_at.strftime("%d/%m/%Y às %H:%M"),
        "pages": [{
            "id": page.id, "page_number": page.page_number, "answer_sheet_id": page.answer_sheet_id,
            "student_id": page.student_id, "status": page.status, "image_path": page.image_path,
            "detected_answers": dict(page.detected_answers or {}), "confidence": page.confidence,
            "issue": page.issue, "analysis": deepcopy(page.analysis or {}),
        } for page in sorted(model.pages, key=lambda item: item.page_number)],
    }


def create_batch(assessment_id, original_name, profile, scope):
    batch_id = str(uuid4())
    if _database_active():
        from ..extensions import db
        from ..models import AnswerScanBatch

        model = AnswerScanBatch(
            id=batch_id, assessment_id=assessment_id, original_name=original_name[:255],
            created_by_role=profile["key"], created_by_id=profile.get("account_id", "global"), scope=scope,
        )
        db.session.add(model)
        db.session.commit()
        return _batch_record(model)
    record = {
        "id": batch_id, "assessment_id": assessment_id, "original_name": original_name[:255],
        "status": "Processando", "page_count": 0, "processed_count": 0, "review_count": 0,
        "failed_count": 0, "scope": deepcopy(scope), "error_message": "",
        "created_by_role": profile["key"], "created_by_id": profile.get("account_id", "global"),
        "created_at": datetime.now(UTC).strftime("%d/%m/%Y às %H:%M"), "pages": [],
    }
    _demo_store()["batches"].insert(0, record)
    return deepcopy(record)


def add_batch_page(batch_id, values):
    page_id = str(uuid4())
    if _database_active():
        from ..extensions import db
        from ..models import AnswerScanPage

        db.session.add(AnswerScanPage(id=page_id, batch_id=batch_id, **values))
        db.session.commit()
    else:
        batch = next(item for item in _demo_store()["batches"] if item["id"] == batch_id)
        batch["pages"].append({"id": page_id, **deepcopy(values)})
    return page_id


def finish_batch(batch_id, error_message=""):
    batch = get_batch(batch_id)
    statuses = [page["status"] for page in batch["pages"]]
    values = {
        "page_count": len(statuses), "processed_count": statuses.count("Lido") + statuses.count("Conferido"),
        "review_count": statuses.count("Revisão"), "failed_count": statuses.count("Falha"),
        "error_message": error_message[:300],
    }
    values["status"] = (
        "Falha no processamento" if error_message else
        "Revisão necessária" if values["review_count"] or values["failed_count"] else "Concluído"
    )
    if _database_active():
        from ..extensions import db
        from ..models import AnswerScanBatch

        model = db.session.get(AnswerScanBatch, batch_id)
        for key, value in values.items():
            setattr(model, key, value)
        db.session.commit()
    else:
        next(item for item in _demo_store()["batches"] if item["id"] == batch_id).update(values)
    return get_batch(batch_id)


def review_page(batch_id, page_id, answers, profile):
    batch = get_batch(batch_id)
    page = next(item for item in batch["pages"] if item["id"] == page_id)
    analysis = deepcopy(page.get("analysis", {}))
    analysis.setdefault("original_answers", dict(page["detected_answers"]))
    analysis.setdefault("reviews", []).append({
        "answers": answers, "reviewer": profile.get("account_id", "global"),
        "at": datetime.now(UTC).isoformat(),
    })
    if _database_active():
        from ..extensions import db
        from ..models import AnswerScanPage

        model = db.session.get(AnswerScanPage, page_id)
        model.detected_answers = answers
        model.analysis = analysis
        model.status = "Conferido"
        db.session.commit()
    else:
        stored_batch = next(item for item in _demo_store()["batches"] if item["id"] == batch_id)
        stored_page = next(item for item in stored_batch["pages"] if item["id"] == page_id)
        stored_page.update({"detected_answers": answers, "analysis": analysis, "status": "Conferido"})
    return finish_batch(batch_id, batch.get("error_message", ""))


def get_batch(batch_id):
    if _database_active():
        from ..extensions import db
        from ..models import AnswerScanBatch

        model = db.session.get(AnswerScanBatch, batch_id)
        return _batch_record(model) if model else None
    return next((deepcopy(item) for item in _demo_store()["batches"] if item["id"] == batch_id), None)


def list_batches():
    if _database_active():
        from ..models import AnswerScanBatch

        return [_batch_record(item) for item in AnswerScanBatch.query.order_by(AnswerScanBatch.created_at.desc()).all()]
    return deepcopy(_demo_store()["batches"])
