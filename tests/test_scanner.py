import base64
import re
from io import BytesIO
from xml.etree import ElementTree

import cv2
import numpy as np
import pypdfium2 as pdfium
import pytest

from app import create_app
from app.config import TestConfig
from app.data.answer_sheets import get_batch, list_batches, sheet_for_token
from app.scanner.layout import PAGE_HEIGHT, PAGE_WIDTH, PIXELS_PER_MM


SCAN_URL = "/cartoes-resposta/simulados/sim-2026-001"


@pytest.fixture
def scanner_client(tmp_path):
    class ScannerConfig(TestConfig):
        SCAN_ROOT = str(tmp_path / "scans")

    client = create_app(ScannerConfig).test_client()
    with client.session_transaction() as session:
        session["profile"] = "school_coordinator"
    client.get("/cartoes-resposta/")
    return client


def printed_image(client, marks=None, filters="", card_index=0):
    """Rasterize the actual SVG bubbles, markers and QR, not assumed coordinates."""
    response = client.get(SCAN_URL + "/imprimir" + filters)
    assert response.status_code == 200
    svgs = re.findall(r'<svg class="answer-sheet-art".*?</svg>', response.get_data(as_text=True), re.S)
    root = ElementTree.fromstring(svgs[card_index])
    image = np.full((PAGE_HEIGHT, PAGE_WIDTH, 3), 255, dtype=np.uint8)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    scale = PIXELS_PER_MM
    for rectangle in root.findall("svg:rect", namespace):
        if rectangle.get("class") != "registration-marker":
            continue
        x, y, w, h = [round(float(rectangle.get(key)) * scale) for key in ("x", "y", "width", "height")]
        image[y:y + h, x:x + w] = 0
    qr = root.find("svg:image", namespace)
    encoded = base64.b64decode(qr.get("href").split(",", 1)[1])
    qr_image = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_COLOR)
    x, y, w, h = [round(float(qr.get(key)) * scale) for key in ("x", "y", "width", "height")]
    image[y:y + h, x:x + w] = cv2.resize(qr_image, (w, h), interpolation=cv2.INTER_NEAREST)
    for circle in root.findall("svg:circle", namespace):
        if circle.get("class") != "answer-bubble":
            continue
        number, letter = circle.get("data-question"), circle.get("data-option")
        x, y, r = [round(float(circle.get(key)) * scale) for key in ("cx", "cy", "r")]
        cv2.circle(image, (x, y), r, (0, 0, 0), 3, cv2.LINE_AA)
        # None = all B; {} = genuinely blank card; tuples control weak/erased ink.
        choice = "B" if marks is None else marks.get(number, "")
        brightness = 0
        if isinstance(choice, tuple):
            choice, brightness = choice
        if letter in choice:
            cv2.circle(image, (x, y), r - 3, (brightness,) * 3, -1, cv2.LINE_AA)
    return image


def upload_image(client, image, fields=None):
    _, encoded = cv2.imencode(".png", image)
    with client.session_transaction() as session:
        token = session["scanner_csrf"]
    data = {"scan_file": (BytesIO(encoded.tobytes()), "scan.png"), "csrf_token": token, **(fields or {})}
    response = client.post(SCAN_URL + "/enviar", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    with client.application.app_context():
        return list_batches()[0]


def test_actual_printed_coordinates_identify_student_and_all_responses(scanner_client):
    batch = upload_image(scanner_client, printed_image(scanner_client))
    page = batch["pages"][0]
    assert page["student_id"] == "alu-001"
    assert page["status"] == "Lido"
    assert page["detected_answers"] == {str(number): "B" for number in range(1, 9)}
    assert page["confidence"] >= .80
    assert page["analysis"]["quality"]["aligned"]


@pytest.mark.parametrize("turns", [1, 2, 3])
def test_rotated_cards_keep_their_question_order(scanner_client, turns):
    marks = {str(number): "ABCD"[(number - 1) % 4] for number in range(1, 9)}
    image = np.rot90(printed_image(scanner_client, marks), turns).copy()
    page = upload_image(scanner_client, image)["pages"][0]
    assert page["status"] == "Lido"
    assert page["detected_answers"] == marks


@pytest.mark.parametrize("distortion", ["perspective", "margins", "shadows"])
def test_scanner_distortions_are_aligned_before_reading(scanner_client, distortion):
    image = printed_image(scanner_client)
    if distortion == "perspective":
        source = np.float32([[0, 0], [PAGE_WIDTH - 1, 0], [PAGE_WIDTH - 1, PAGE_HEIGHT - 1], [0, PAGE_HEIGHT - 1]])
        target = np.float32([[120, 80], [PAGE_WIDTH - 140, 30], [PAGE_WIDTH - 40, PAGE_HEIGHT - 60], [30, PAGE_HEIGHT - 180]])
        image = cv2.warpPerspective(image, cv2.getPerspectiveTransform(source, target), (PAGE_WIDTH, PAGE_HEIGHT), borderValue=(225, 225, 225))
    elif distortion == "margins":
        image = cv2.copyMakeBorder(image, 160, 130, 100, 80, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    else:
        shade = np.linspace(.58, 1.0, image.shape[1], dtype=np.float32)[None, :, None]
        image = np.uint8(image.astype(np.float32) * shade)
    page = upload_image(scanner_client, image)["pages"][0]
    assert page["status"] == "Lido"
    assert set(page["detected_answers"].values()) == {"B"}


@pytest.mark.parametrize("marks,state", [({}, "em_branco"), ({"1": "AB"}, "multipla"), ({"1": ("B", 180)}, "duvidosa"), ({"1": ("B", 222)}, "duvidosa")])
def test_blank_double_faint_and_erased_marks_are_never_accepted(scanner_client, marks, state):
    choices = {str(number): "B" for number in range(1, 9)}
    choices.update(marks)
    if not marks:
        choices = {}
    page = upload_image(scanner_client, printed_image(scanner_client, choices))["pages"][0]
    assert page["status"] == "Revisão"
    assert page["analysis"]["questions"]["1"]["state"] == state
    assert page["confidence"] < .80


def test_missing_corner_does_not_fall_back_to_guessing_coordinates(scanner_client):
    image = printed_image(scanner_client)
    image[-160:, :160] = 255
    page = upload_image(scanner_client, image)["pages"][0]
    assert page["status"] == "Revisão"
    assert not page["analysis"]["quality"]["aligned"]
    assert page["detected_answers"] == {}


def test_low_resolution_is_flagged_even_when_the_qr_is_readable(scanner_client):
    image = printed_image(scanner_client)
    image = cv2.resize(image, (630, 891), interpolation=cv2.INTER_AREA)
    page = upload_image(scanner_client, image)["pages"][0]
    assert page["status"] != "Lido"


def test_scope_filters_print_only_the_selected_year_and_class(scanner_client):
    response = scanner_client.get(SCAN_URL + "/imprimir?series_name=9%C2%BA%20ano&school_year=2026&class_id=tur-002")
    content = response.get_data(as_text=True)
    assert "Mariana Costa" in content
    assert "Ana Clara Souza" not in content
    assert "Sofia Ribeiro" not in content


def test_cards_outside_selected_series_are_separated(scanner_client):
    page = upload_image(scanner_client, printed_image(scanner_client), {"series_name": "8º ano"})["pages"][0]
    assert page["status"] == "Falha"
    assert not page["student_id"]
    assert "série/ano" in page["issue"]


def test_school_cannot_print_or_read_another_schools_batch(scanner_client):
    batch = upload_image(scanner_client, printed_image(scanner_client))
    with scanner_client.session_transaction() as session:
        session["profile"] = "institute_coordinator"
    other_image = printed_image(scanner_client, filters="?institution_id=inst-003")
    with scanner_client.session_transaction() as session:
        session["profile"] = "school_coordinator"
    page = upload_image(scanner_client, other_image)["pages"][0]
    assert page["status"] == "Falha"
    assert not page["student_id"]
    with scanner_client.application.app_context():
        from app.data.answer_sheets import create_batch

        other_batch = create_batch("sim-2026-001", "other.pdf", {"key": "institute_coordinator", "account_id": "usr-006"}, {"institution_id": "inst-003"})
    assert scanner_client.get(f"/cartoes-resposta/lotes/{other_batch['id']}").status_code == 404
    assert scanner_client.get(f"/cartoes-resposta/lotes/{batch['id']}").status_code == 200


def test_manual_review_keeps_original_reading_and_reviewer(scanner_client):
    marks = {str(number): "B" for number in range(1, 9)}
    marks["1"] = "AB"
    batch = upload_image(scanner_client, printed_image(scanner_client, marks))
    page = batch["pages"][0]
    route = f"/cartoes-resposta/lotes/{batch['id']}/paginas/{page['id']}/revisar"
    assert scanner_client.get(route).status_code == 200
    with scanner_client.session_transaction() as session:
        csrf = session["scanner_csrf"]
    data = {"csrf_token": csrf, "confirm_review": "yes", **{f"answer_{n}": "B" for n in range(1, 9)}}
    response = scanner_client.post(route, data=data, follow_redirects=True)
    assert response.status_code == 200
    with scanner_client.application.app_context():
        reviewed = get_batch(batch["id"])["pages"][0]
    assert reviewed["status"] == "Conferido"
    assert reviewed["detected_answers"]["1"] == "B"
    assert reviewed["analysis"]["original_answers"]["1"] == ""
    assert reviewed["analysis"]["reviews"][0]["reviewer"] == "usr-005"


def test_qr_garbage_is_rejected_without_throwing(scanner_client):
    with scanner_client.application.app_context():
        assert sheet_for_token("IFP1.á.abcdef") is None
        assert sheet_for_token("IFP1.11111111-1111-1111-1111-111111111111.é") is None


def test_invalid_upload_does_not_leave_a_processing_batch(scanner_client):
    with scanner_client.session_transaction() as session:
        csrf = session["scanner_csrf"]
    response = scanner_client.post(SCAN_URL + "/enviar", data={"csrf_token": csrf, "scan_file": (BytesIO(b"not-a-pdf"), "fake.pdf")}, follow_redirects=True)
    assert response.status_code == 200
    with scanner_client.application.app_context():
        assert not list_batches()


def pdf_from_images(images):
    document = pdfium.PdfDocument.new()
    try:
        for image in images:
            page = document.new_page(595.276, 841.89)
            _, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 98])
            image_object = pdfium.PdfImage.new(document)
            image_object.load_jpeg(BytesIO(encoded.tobytes()), inline=True)
            image_object.set_matrix(pdfium.PdfMatrix(595.276, 0, 0, 841.89, 0, 0))
            page.insert_obj(image_object)
            page.gen_content()
            page.close()
        output = BytesIO()
        document.save(output)
        return output.getvalue()
    finally:
        document.close()


def test_pdf_batch_reads_each_student_and_flags_duplicate_pages(scanner_client):
    first = printed_image(scanner_client)
    second = printed_image(scanner_client, card_index=1)
    data = pdf_from_images([first, second, first])
    with scanner_client.session_transaction() as session:
        csrf = session["scanner_csrf"]
    response = scanner_client.post(SCAN_URL + "/enviar", data={
        "csrf_token": csrf, "scan_file": (BytesIO(data), "batch.pdf"),
    }, follow_redirects=True)
    assert response.status_code == 200
    with scanner_client.application.app_context():
        batch = list_batches()[0]
    assert batch["page_count"] == 3
    assert batch["processed_count"] == 2
    assert batch["pages"][0]["student_id"] == "alu-001"
    assert batch["pages"][1]["student_id"] == "alu-002"
    assert batch["pages"][2]["status"] == "Falha"
    assert "duplicado" in batch["pages"][2]["issue"]


def test_blur_never_becomes_a_high_confidence_reading(scanner_client):
    image = cv2.GaussianBlur(printed_image(scanner_client), (31, 31), 7)
    page = upload_image(scanner_client, image)["pages"][0]
    assert page["status"] != "Lido"


def test_questions_keep_original_order_after_assessment_changes(scanner_client):
    from app.data.assessments import find_assessment

    image = printed_image(scanner_client)
    with scanner_client.application.app_context():
        assessment = find_assessment("sim-2026-001")
        original_order = assessment["question_ids"][:]
        assessment["question_ids"] = original_order[::-1]
    try:
        page = upload_image(scanner_client, image)["pages"][0]
        assert page["status"] == "Revisão"
        assert page["analysis"]["manifest"][0]["question_id"] == original_order[0]
        assert "mudou após a emissão" in page["issue"]
    finally:
        assessment["question_ids"] = original_order


def test_jpeg_over_original_global_limit_reaches_scanner_validation(scanner_client):
    # A 17 MB file used to hit Flask's global 16 MB cap despite the UI's 50 MB promise.
    scanner_client.application.config["SCAN_UPLOAD_MAX_BYTES"] = 18 * 1024 * 1024
    with scanner_client.session_transaction() as session:
        csrf = session["scanner_csrf"]
    response = scanner_client.post(SCAN_URL + "/enviar", data={
        "csrf_token": csrf, "scan_file": (BytesIO(b"x" * (17 * 1024 * 1024)), "broken.jpg"),
    }, follow_redirects=True)
    assert response.status_code == 200
    with scanner_client.application.app_context():
        batch = list_batches()[0]
    assert batch["status"] == "Falha no processamento"


def test_scan_upload_and_manual_review_require_form_token(scanner_client):
    response = scanner_client.post(SCAN_URL + "/enviar", data={"scan_file": (BytesIO(b"x"), "x.jpg")})
    assert response.status_code == 400


def test_upload_without_previously_issued_token_rejects_placeholder(scanner_client):
    with scanner_client.session_transaction() as session:
        session.pop("scanner_csrf")
    response = scanner_client.post(SCAN_URL + "/enviar", data={"csrf_token": "missing"})
    assert response.status_code == 400


def test_twenty_questions_in_two_columns_with_variable_options(scanner_client, monkeypatch):
    from app.data.assessments import find_assessment
    from app.scanner import routes

    questions = [{"id": f"full-{number}", "tipo": "objetiva",
                  "alternativas": {letter: letter for letter in "ABCDE"[:2 + number % 4]}}
                 for number in range(1, 21)]
    monkeypatch.setattr(routes, "QUESTIONS", questions)
    with scanner_client.application.app_context():
        assessment = find_assessment("sim-2026-001")
        monkeypatch.setitem(assessment, "question_ids", [question["id"] for question in questions])
    marks = {str(number): list(question["alternativas"])[-1] for number, question in enumerate(questions, 1)}
    page = upload_image(scanner_client, printed_image(scanner_client, marks))["pages"][0]
    assert page["status"] == "Lido"
    assert page["detected_answers"] == marks


def test_dissertative_questions_keep_original_numbering():
    from app.scanner.layout import question_manifest

    questions = [{"id": "first", "alternativas": {"A": "yes", "B": "no"}},
                 {"id": "open", "tipo": "discursiva"},
                 {"id": "last", "alternativas": {"A": "yes", "B": "no"}}]
    manifest = question_manifest({"question_ids": ["first", "open", "last"]}, questions)
    assert [question["number"] for question in manifest] == [1, 3]


def test_shifted_bubbles_are_flagged_instead_of_guessed(scanner_client):
    image = printed_image(scanner_client)
    # Keep QR and corners intact but move the answer area away from its grid.
    area = image[850:1850, 150:1550].copy()
    image[850:1850, 150:1550] = 255
    image[850:1850, 180:1580] = area
    page = upload_image(scanner_client, image)["pages"][0]
    assert page["status"] == "Revisão"
    assert page["analysis"]["questions"]["1"]["state"] == "desalinhada"


def test_demo_mode_can_process_and_review_without_a_database(tmp_path):
    class DemoConfig(TestConfig):
        DATABASE_ENABLED = False
        SCAN_ROOT = str(tmp_path)

    client = create_app(DemoConfig).test_client()
    with client.session_transaction() as session:
        session["profile"] = "school_coordinator"
    client.get("/cartoes-resposta/")
    page = upload_image(client, printed_image(client))["pages"][0]
    assert page["status"] == "Lido"
