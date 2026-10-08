"""Conservative OMR: a doubtful page never becomes an accepted reading."""
from itertools import product
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium
import zxingcpp

from .layout import (
    BUBBLE_RADIUS_MM, MARKER_CENTERS_MM, MARKER_SIZE_MM, PAGE_HEIGHT, PAGE_WIDTH,
    PIXELS_PER_MM, answer_rows, pixel_point,
)


def validate_upload(uploaded, maximum_bytes):
    filename = uploaded.filename or "digitalizacao"
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise ValueError("Envie um arquivo PDF, PNG, JPG ou JPEG.")
    data = uploaded.read(maximum_bytes + 1)
    if not data:
        raise ValueError("O arquivo enviado está vazio.")
    if len(data) > maximum_bytes:
        raise ValueError(f"O arquivo deve ter no máximo {maximum_bytes // (1024 * 1024)} MB.")
    if extension == ".pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("O conteúdo enviado não é um PDF válido.")
    return data, extension


def _decode_image(data, maximum_pixels):
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Não foi possível ler a imagem enviada.")
    if image.shape[0] * image.shape[1] > maximum_pixels:
        raise ValueError("A imagem excede o limite de resolução. Digitalize em 300 dpi.")
    return image


def iter_upload_pages(data, extension, maximum_pages, maximum_pixels):
    """Render one PDF page at a time; never keep a whole batch in RAM."""
    if extension != ".pdf":
        yield 1, _decode_image(data, maximum_pixels)
        return
    try:
        document = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        raise ValueError("O PDF está corrompido, protegido ou não pode ser aberto.") from exc
    try:
        if not 1 <= len(document) <= maximum_pages:
            raise ValueError(f"Envie um PDF com 1 a {maximum_pages} páginas por lote.")
        for index in range(len(document)):
            page = document[index]
            bitmap = None
            try:
                width, height = page.get_size()
                scale = min(3.0, (maximum_pixels / max(1, width * height)) ** 0.5)
                bitmap = page.render(scale=scale, rev_byteorder=False)
                image = bitmap.to_numpy().copy()
                if image.ndim == 2:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                elif image.shape[2] == 4:
                    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                yield index + 1, image
            finally:
                if bitmap is not None:
                    bitmap.close()
                page.close()
    finally:
        document.close()


def _read_barcode(image):
    variants = [image]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    variants.append(cv2.createCLAHE(clipLimit=2, tileGridSize=(8, 8)).apply(gray))
    for variant in variants:
        barcodes = zxingcpp.read_barcodes(variant, formats=zxingcpp.BarcodeFormat.QRCode)
        valid = [barcode for barcode in barcodes if barcode.valid and barcode.text.startswith("IFP1.")]
        if len(valid) > 1:
            return None, "Mais de um QR de cartão na mesma página. Envie uma folha por página."
        if valid:
            return valid[0], ""
    return None, "QR Code não reconhecido. Confira a resolução e o enquadramento."


def read_qr(image):
    barcode, _ = _read_barcode(image)
    return barcode.text if barcode else None


def _upright(image, barcode):
    # ZXing reports the direction of the printed QR. A4 borders are not needed.
    turns = {0: 0, 90: 1, 180: 2, -90: 3, 270: 3}.get(barcode.orientation)
    if turns is None:
        return image
    return np.rot90(image, turns).copy() if turns else image


def _marker_candidates(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 71, 15)
    area = gray.size
    height, width = gray.shape
    candidates = []
    for binary in (otsu, adaptive):
        contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            contour_area = cv2.contourArea(contour)
            if not area * 0.00008 <= contour_area <= area * 0.008:
                continue
            polygon = cv2.approxPolyDP(contour, .035 * cv2.arcLength(contour, True), True)
            if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                continue
            (cx, cy), (rw, rh), _ = cv2.minAreaRect(contour)
            if not rw or not rh or not .65 <= rw / rh <= 1.55:
                continue
            if contour_area / (rw * rh) < .82:
                continue
            if not ((cx < width * .32 or cx > width * .68)
                    and (cy < height * .32 or cy > height * .68)):
                continue
            mask = np.zeros(binary.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            if np.mean(binary[mask > 0] > 0) < .90:
                continue
            if any(np.linalg.norm(np.array([cx, cy]) - item[0]) < min(rw, rh) * .5 for item in candidates):
                continue
            candidates.append((np.array([cx, cy], dtype=np.float32), contour_area))
    return candidates


def _alignment(image):
    height, width = image.shape[:2]
    candidates = _marker_candidates(image)
    corners = ((0, 0), (width, 0), (width, height), (0, height))
    groups = []
    for cx, cy in corners:
        group = [candidate for candidate in candidates
                 if (candidate[0][0] < width * .5) == (cx == 0)
                 and (candidate[0][1] < height * .5) == (cy == 0)]
        group.sort(key=lambda item: np.linalg.norm(item[0] - np.array([cx, cy])))
        groups.append(group[:3])
    if any(not group for group in groups):
        return None
    target = np.array([pixel_point(*point) for point in MARKER_CENTERS_MM], dtype=np.float32)
    for selection in product(*groups):
        points = np.array([item[0] for item in selection], dtype=np.float32)
        areas = np.array([item[1] for item in selection])
        if max(areas) / min(areas) > 2.8 or not cv2.isContourConvex(points.reshape(-1, 1, 2)):
            continue
        span_x = (np.linalg.norm(points[1] - points[0]) + np.linalg.norm(points[2] - points[3])) / 2
        span_y = (np.linalg.norm(points[3] - points[0]) + np.linalg.norm(points[2] - points[1])) / 2
        if span_x < width * .45 or span_y < height * .45 or not .45 < span_x / span_y < .95:
            continue
        expected_area = (span_x * MARKER_SIZE_MM / 186) * (span_y * MARKER_SIZE_MM / 273)
        if not np.all((areas / expected_area > .45) & (areas / expected_area < 1.85)):
            continue
        matrix = cv2.getPerspectiveTransform(points, target)
        normalized = cv2.warpPerspective(image, matrix, (PAGE_WIDTH, PAGE_HEIGHT),
                                         flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
        return normalized, round(float(min(span_x / 186, span_y / 273)), 2)
    return None


def prepare_page(image):
    barcode, qr_issue = _read_barcode(image)
    token = barcode.text if barcode else None
    upright = _upright(image, barcode) if barcode else image
    # Work at a bounded size while keeping enough detail for the fiducials.
    if max(upright.shape[:2]) > 3000:
        factor = 3000 / max(upright.shape[:2])
        upright = cv2.resize(upright, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA)
    aligned = _alignment(upright) if barcode else None
    quality = {"aligned": bool(aligned), "issues": [qr_issue] if qr_issue else []}
    if aligned is None:
        quality["issues"].append("Não foi possível localizar os quatro marcadores. Digitalize novamente sem cortar os cantos.")
        preview = upright
    else:
        preview, pixels_per_mm = aligned
        quality["source_pixels_per_mm"] = pixels_per_mm
        if pixels_per_mm < 3.5:
            quality["issues"].append("Resolução insuficiente para aceitar a leitura automaticamente.")
        region = cv2.cvtColor(preview[800:1900, 150:1550], cv2.COLOR_BGR2GRAY)
        sharpness = float(cv2.Laplacian(region, cv2.CV_64F).var())
        quality["sharpness"] = round(sharpness, 2)
        if sharpness < 30:
            quality["issues"].append("Imagem desfocada. Confira as marcações ou digitalize novamente.")
    return token, preview, quality


def analyze_answers(image, manifest):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Closing estimates the paper brightness without black outlines/fills.
    paper = cv2.morphologyEx(gray, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (81, 81)))
    contrast = np.clip((paper.astype(np.float32) - gray) / np.maximum(paper, 1), 0, 1)
    answers, diagnostics, issues = {}, {}, []
    radius = BUBBLE_RADIUS_MM * PIXELS_PER_MM
    yy, xx = np.mgrid[-40:41, -40:41]
    distance = np.sqrt(xx * xx + yy * yy)
    inner = distance <= radius * .65
    ring = (distance >= radius - 3) & (distance <= radius + 2)
    for row in answer_rows(manifest):
        readings = {}
        for bubble in row["bubbles"]:
            x, y = pixel_point(bubble["x"], row["y"])
            best = None
            # Refine the centre by a few pixels after geometric correction.
            for dx, dy in product((-3, 0, 3), repeat=2):
                patch = contrast[y + dy - 40:y + dy + 41, x + dx - 40:x + dx + 41]
                if patch.shape != ring.shape:
                    continue
                ring_ink = float(np.mean(patch[ring] > .22))
                if best is None or ring_ink > best[0]:
                    best = (ring_ink, patch, x + dx, y + dy)
            if best is None:
                readings[bubble["letter"]] = {"fill": 0, "darkness": 0, "ring": 0, "x": x, "y": y}
                continue
            ring_ink, patch, refined_x, refined_y = best
            readings[bubble["letter"]] = {
                "fill": round(float(np.mean(patch[inner] > .22)), 3),
                "darkness": round(float(np.mean(patch[inner])), 3),
                "ring": round(ring_ink, 3), "x": refined_x, "y": refined_y,
            }
        number = str(row["number"])
        ranked = sorted(readings.items(), key=lambda item: item[1]["fill"], reverse=True)
        top_letter, top = ranked[0]
        second = ranked[1][1]
        strong = [letter for letter, value in readings.items() if value["fill"] >= .50 and value["darkness"] >= .30]
        faint = [letter for letter, value in readings.items() if value["fill"] > .09 or value["darkness"] > .07]
        ring_ok = all(value["ring"] >= .40 for value in readings.values())
        margin = top["fill"] - second["fill"]
        selected, score, state = "", 0.0, "em_branco"
        if not ring_ok:
            state = "desalinhada"
        elif len(strong) > 1:
            state = "multipla"
        elif len(strong) == 1 and second["fill"] <= .09 and margin >= .40 and top["fill"] >= .65:
            selected = top_letter
            state = "marcada"
            score = min(1.0, .55 + margin * .30 + top["darkness"] * .15)
        elif faint:
            state = "duvidosa"
            selected = top_letter if len(strong) == 1 else ""
            score = min(.69, max(0, margin))
        messages = {
            "em_branco": "sem marcação", "multipla": "mais de uma alternativa preenchida",
            "duvidosa": "marca fraca, rasura ou alternativas próximas",
            "desalinhada": "bolhas não localizadas com segurança",
        }
        if state != "marcada":
            issues.append(f"Questão {number}: {messages[state]}.")
        answers[number] = selected
        diagnostics[number] = {
            "state": state, "confidence": round(score, 3), "options": readings,
            "question_id": row["question_id"], "options_allowed": row["options"],
        }
    # The weakest question determines whether the whole page may be accepted.
    confidence = min((item["confidence"] for item in diagnostics.values()), default=0)
    return answers, round(confidence, 3), issues, diagnostics


def annotated_page(image, diagnostics, answers):
    overlay = image.copy()
    colors = {"marcada": (70, 135, 30), "duvidosa": (0, 145, 225), "multipla": (50, 50, 215),
              "desalinhada": (50, 50, 215), "em_branco": (0, 145, 225)}
    for number, diagnostic in diagnostics.items():
        for letter, value in diagnostic["options"].items():
            color = colors[diagnostic["state"]]
            if diagnostic["state"] == "marcada" and letter != answers[number]:
                continue
            cv2.circle(overlay, (value["x"], value["y"]), 29, color, 3)
    return overlay


def save_page(root, batch_id, page_number, image, suffix="original"):
    relative = Path(batch_id) / f"page-{page_number:03d}-{suffix}.png"
    destination = Path(root) / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), image):
        raise ValueError("Não foi possível armazenar a página digitalizada.")
    return relative.as_posix()
