from copy import deepcopy
from datetime import datetime

from flask import current_app, has_app_context


ALLOWED_ATTACHMENT_EXTENSIONS = {"pdf", "png", "ppt", "pptx"}

MATERIAL_POSTS = [
    {
        "id": "rev-001",
        "titulo": "Guia de operações primárias",
        "descricao": "Resumo de preparação para o simulado de Matemática.",
        "texto": (
            "Soma: junte as quantidades e alinhe unidades, dezenas e centenas. Exemplo: 27 + 15 = 42.\n\n"
            "Subtração: calcule a diferença entre duas quantidades. Exemplo: 63 - 28 = 35.\n\n"
            "Multiplicação: represente parcelas iguais. Exemplo: 7 × 8 = 56.\n\n"
            "Divisão: distribua uma quantidade em grupos iguais. Exemplo: 72 ÷ 8 = 9."
        ),
        "professor_id": "pro-001",
        "materia_id": "mat-001",
        "assunto_id": "ass-001",
        "turma_ids": ["tur-001", "tur-002"],
        "publicado_em": "29/09/2026 às 09:00",
        "anexo": None,
    }
]

INITIAL_MATERIAL_POSTS = deepcopy(MATERIAL_POSTS)


def _database_active():
    return has_app_context() and current_app.config.get("DATABASE_ENABLED", False)


def persist_material(material):
    if not _database_active():
        return material
    from ..extensions import db
    from ..models import MaterialPost

    db.session.merge(MaterialPost(
        id=material["id"], title=material["titulo"], description=material["descricao"],
        text=material.get("texto", ""), teacher_id=material["professor_id"],
        subject_id=material["materia_id"], topic_id=material["assunto_id"],
        class_ids=list(material.get("turma_ids", [])), published_at=material["publicado_em"],
        attachment=material.get("anexo"),
    ))
    db.session.commit()
    return material


def find_material(material_id):
    return next((item for item in MATERIAL_POSTS if item["id"] == material_id), None)


def group_materials(materials):
    """Organize materiais enriquecidos pela hierarquia matéria → assunto."""
    subject_groups = {}
    for material in materials:
        subject_id = material.get("materia_id", "")
        topic_id = material.get("assunto_id", "")
        subject = subject_groups.setdefault(subject_id, {
            "id": subject_id,
            "nome": material.get("materia", "Matéria não informada"),
            "quantidade": 0,
            "assuntos": {},
        })
        topic = subject["assuntos"].setdefault(topic_id, {
            "id": topic_id,
            "nome": material.get("assunto", "Assunto não informado"),
            "materiais": [],
        })
        topic["materiais"].append(material)
        subject["quantidade"] += 1

    groups = []
    for subject in sorted(subject_groups.values(), key=lambda item: item["nome"].casefold()):
        subject["assuntos"] = sorted(subject["assuntos"].values(), key=lambda item: item["nome"].casefold())
        groups.append(subject)
    return groups


def add_material(values):
    sequence = max([int(item["id"].split("-")[-1]) for item in MATERIAL_POSTS] or [0]) + 1
    material = {
        "id": f"rev-{sequence:03d}",
        "publicado_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        **values,
    }
    MATERIAL_POSTS.insert(0, material)
    return persist_material(material)


def update_material(material_id, values):
    material = find_material(material_id)
    if material:
        material.update(values)
        persist_material(material)
    return material


def delete_material(material_id):
    material = find_material(material_id)
    if material:
        MATERIAL_POSTS.remove(material)
        if _database_active():
            from ..extensions import db
            from ..models import MaterialPost

            model = db.session.get(MaterialPost, material_id)
            if model:
                db.session.delete(model)
                db.session.commit()
    return material


def attachment_extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
