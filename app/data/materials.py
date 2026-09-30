from datetime import datetime


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


def find_material(material_id):
    return next((item for item in MATERIAL_POSTS if item["id"] == material_id), None)


def add_material(values):
    sequence = max([int(item["id"].split("-")[-1]) for item in MATERIAL_POSTS] or [0]) + 1
    material = {
        "id": f"rev-{sequence:03d}",
        "publicado_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        **values,
    }
    MATERIAL_POSTS.insert(0, material)
    return material


def update_material(material_id, values):
    material = find_material(material_id)
    if material:
        material.update(values)
    return material


def delete_material(material_id):
    material = find_material(material_id)
    if material:
        MATERIAL_POSTS.remove(material)
    return material


def attachment_extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
