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


def find_sheets(assessment_id, student_id=None):
    if _database_active():
        from ..models import AnswerSheet

        query = AnswerSheet.query.filter_by(assessment_id=assessment_id)
        if student_id is not None:
            query = query.filter_by(student_id=student_id)
        return [_sheet_record(item) for item in query.all()]
    return [deepcopy(item) for item in _demo_store()["sheets"]
            if item["assessment_id"] == assessment_id
            and (student_id is None or item["student_id"] == student_id)]


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


def _page_record(model):
    return {
        "id": model.id, "page_number": model.page_number, "answer_sheet_id": model.answer_sheet_id,
        "student_id": model.student_id, "status": model.status, "image_path": model.image_path,
        "detected_answers": dict(model.detected_answers or {}), "confidence": model.confidence,
        "issue": model.issue, "analysis": deepcopy(model.analysis or {}),
    }


def _batch_record(model):
    return {
        "id": model.id, "assessment_id": model.assessment_id, "original_name": model.original_name,
        "status": model.status, "page_count": model.page_count,
        "processed_count": model.processed_count, "review_count": model.review_count,
        "failed_count": model.failed_count, "scope": deepcopy(model.scope or {}),
        "error_message": model.error_message or "", "created_by_role": model.created_by_role,
        "created_by_id": model.created_by_id,
        "created_at": model.created_at.strftime("%d/%m/%Y às %H:%M"),
        "pages": [_page_record(page) for page in sorted(model.pages, key=lambda item: item.page_number)],
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


def batch_status_values(statuses, error_message=""):
    values = {
        "page_count": len(statuses),
        "processed_count": sum(statuses.count(status) for status in ("Lido", "Conferido", "Lançado")),
        "review_count": statuses.count("Revisão"), "failed_count": statuses.count("Falha"),
        "error_message": error_message[:300],
    }
    values["status"] = (
        "Falha no processamento" if error_message else
        "Revisão necessária" if values["review_count"] or values["failed_count"] else
        "Resultados lançados" if "Lançado" in statuses and not any(status in {"Lido", "Conferido"} for status in statuses)
        else "Concluído"
    )
    return values


def finish_batch(batch_id, error_message=""):
    batch = get_batch(batch_id)
    values = batch_status_values([page["status"] for page in batch["pages"]], error_message)
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


STALE_PAGE = "Esta página mudou enquanto você decidia. Atualize a prévia e refaça a escolha."
REVIEWABLE_STATES = ("Lido", "Revisão", "Conferido")


def _transition_page(batch_id, page_id, expected_statuses, build):
    """Lock the page and its batch, refuse a stale decision and recount the batch in one transaction.

    `build` receives the page as it is inside the lock, so nothing read before the
    lock can overwrite a decision another reviewer saved in the meantime.
    """
    if _database_active():
        from ..extensions import db
        from ..models import AnswerScanBatch, AnswerScanPage

        try:
            batch_model = AnswerScanBatch.query.filter_by(id=batch_id).populate_existing().with_for_update().one_or_none()
            model = (AnswerScanPage.query.filter_by(id=page_id, batch_id=batch_id)
                     .populate_existing().with_for_update().one_or_none())
            if not batch_model or not model:
                raise ValueError("Página não encontrada.")
            if model.status == "Lançado" or model.status not in expected_statuses:
                raise ValueError(STALE_PAGE)
            for key, value in build(_page_record(model)).items():
                setattr(model, key, value)
            statuses = [page.status for page in AnswerScanPage.query.filter_by(batch_id=batch_id).all()]
            for key, value in batch_status_values(statuses, batch_model.error_message or "").items():
                setattr(batch_model, key, value)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return get_batch(batch_id)
    stored_batch = next((item for item in _demo_store()["batches"] if item["id"] == batch_id), None)
    stored_page = next((item for item in (stored_batch or {}).get("pages", []) if item["id"] == page_id), None)
    if not stored_page:
        raise ValueError("Página não encontrada.")
    if stored_page["status"] == "Lançado" or stored_page["status"] not in expected_statuses:
        raise ValueError(STALE_PAGE)
    stored_page.update(deepcopy(build(deepcopy(stored_page))))
    statuses = [item["status"] for item in stored_batch["pages"]]
    stored_batch.update(batch_status_values(statuses, stored_batch.get("error_message", "")))
    return get_batch(batch_id)


def decide_page(batch_id, page_id, status, analysis, issue, expected_status):
    """Persist a review decision while keeping the original scan and its audit history."""
    def build(_page):
        return {"status": status, "analysis": deepcopy(analysis), "issue": (issue or "")[:300]}

    return _transition_page(batch_id, page_id, {expected_status}, build)


def review_page(batch_id, page_id, answers, profile):
    def build(page):
        analysis = page["analysis"]
        analysis.setdefault("original_answers", dict(page["detected_answers"]))
        analysis.setdefault("reviews", []).append({
            "answers": answers, "reviewer": profile.get("account_id", "global"),
            "at": datetime.now(UTC).isoformat(),
        })
        return {"detected_answers": dict(answers), "analysis": analysis, "status": "Conferido"}

    return _transition_page(batch_id, page_id, set(REVIEWABLE_STATES), build)


def identify_page(batch_id, page_id, sheet, answers, confidence, analysis, overlay_path, profile):
    def build(_page):
        updated_analysis = deepcopy(analysis)
        updated_analysis["overlay_path"] = overlay_path
        updated_analysis["original_answers"] = dict(answers)
        updated_analysis["manual_identification"] = {
            "student_id": sheet["student_id"], "sheet_id": sheet["id"],
            "reviewer": profile.get("account_id", "global"), "at": datetime.now(UTC).isoformat(),
        }
        return {
            "answer_sheet_id": sheet["id"], "student_id": sheet["student_id"],
            "status": "Revisão", "detected_answers": dict(answers), "confidence": confidence,
            "issue": "QR ilegível; estudante identificado manualmente. Confira todas as respostas.",
            "analysis": updated_analysis,
        }

    return _transition_page(batch_id, page_id, {"Falha"}, build)


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
