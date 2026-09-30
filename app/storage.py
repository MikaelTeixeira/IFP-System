from pathlib import Path
from uuid import uuid4

from flask import current_app

from .extensions import db
from .models import StoredFile


def save_uploaded_file(uploaded, owner_type, owner_id, allowed_extensions, maximum_bytes):
    original_name = uploaded.filename or "arquivo"
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in allowed_extensions:
        raise ValueError("Formato de arquivo não permitido.")
    data = uploaded.read(maximum_bytes + 1)
    if len(data) > maximum_bytes:
        raise ValueError(f"O arquivo deve ter no máximo {maximum_bytes // (1024 * 1024)} MB.")
    file_id = str(uuid4())
    relative_path = Path(owner_type) / f"{file_id}.{extension}"
    absolute_path = Path(current_app.config["UPLOAD_ROOT"]) / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(data)
    record = StoredFile(
        id=file_id,
        owner_type=owner_type,
        owner_id=owner_id,
        path=relative_path.as_posix(),
        original_name=original_name,
        mime_type=uploaded.mimetype or "application/octet-stream",
        extension=extension.upper(),
        size=len(data),
    )
    db.session.add(record)
    db.session.commit()
    return file_metadata(record)


def file_metadata(record):
    return {
        "arquivo_id": record.id,
        "nome": record.original_name,
        "tipo": record.mime_type,
        "extensao": record.extension,
        "tamanho": record.size,
        "caminho": record.path,
    }


def stored_file(file_id):
    return db.session.get(StoredFile, file_id)


def absolute_file_path(record):
    root = Path(current_app.config["UPLOAD_ROOT"]).resolve()
    path = (root / record.path).resolve()
    if root not in path.parents:
        raise ValueError("Caminho de arquivo inválido.")
    return path


def delete_stored_file(file_id):
    record = stored_file(file_id)
    if not record:
        return
    path = absolute_file_path(record)
    if path.exists():
        path.unlink()
    db.session.delete(record)
    db.session.commit()
