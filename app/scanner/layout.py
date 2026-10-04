"""One physical coordinate system for both printing and OMR (millimetres)."""

TEMPLATE_VERSION = "A4-20-v2"
PAGE_MM = (210, 297)
PIXELS_PER_MM = 8
PAGE_WIDTH = PAGE_MM[0] * PIXELS_PER_MM
PAGE_HEIGHT = PAGE_MM[1] * PIXELS_PER_MM
MARKER_SIZE_MM = 6
MARKER_CENTERS_MM = ((12, 12), (198, 12), (198, 285), (12, 285))
BUBBLE_RADIUS_MM = 3
FIRST_ROW_MM = 113
ROW_STEP_MM = 12


def question_manifest(assessment, questions):
    by_id = {question["id"]: question for question in questions}
    manifest = []
    for number, question_id in enumerate(assessment.get("question_ids", []), start=1):
        question = by_id.get(question_id)
        if not question:
            raise ValueError("Há uma questão indisponível na composição do simulado.")
        if question.get("tipo", "objetiva") != "objetiva":
            continue
        options = sorted(question.get("alternativas", {}))
        if not 2 <= len(options) <= 5 or options != list("ABCDE"[:len(options)]):
            raise ValueError("O cartão aceita questões com duas a cinco alternativas consecutivas, de A a E.")
        manifest.append({"question_id": question_id, "number": number, "options": options})
    if not manifest or len(manifest) > 20:
        raise ValueError("Selecione um simulado com 1 a 20 questões objetivas para emitir os cartões.")
    return manifest


def answer_rows(manifest):
    # Two blocks of ten, with letters outside the bubbles to avoid false ink.
    rows = []
    for index, question in enumerate(manifest):
        block = index // 10
        x_offset = block * 90
        rows.append({
            **question,
            "index": index,
            "block": block,
            "x": 24 + x_offset,
            "y": FIRST_ROW_MM + (index % 10) * ROW_STEP_MM,
            "bubbles": [
                {"letter": letter, "x": 47 + option * 12 + x_offset}
                for option, letter in enumerate(question["options"])
            ],
        })
    return rows


def pixel_point(x_mm, y_mm):
    return round(x_mm * PIXELS_PER_MM), round(y_mm * PIXELS_PER_MM)
