"""Gera favicons e ícones do app a partir da logo em templates/macros/brand.html.

Uso: python scripts/gerar_icones.py
Requer Google Chrome ou Microsoft Edge instalado (rasteriza o SVG em modo headless).
Defina IFP_BROWSER com o caminho do executável se ele não for encontrado.
"""

import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

import cv2
from jinja2 import Environment, FileSystemLoader
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "app" / "templates"
IMAGES = PROJECT_ROOT / "app" / "static" / "images"
LOGO_BROWN = "#522304"
RENDER_SIZE = 1024
FAVICON_MARK_SCALE = 1.18
BROWSER_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)


def svg_source(background, mark_scale):
    macros = Environment(loader=FileSystemLoader(TEMPLATES)).get_template("macros/brand.html").module
    # Arquivos estáticos não dependem da propriedade CSS "color" do contexto.
    return str(macros.brand_logo_file(background, mark_scale)).replace("currentColor", LOGO_BROWN) + "\n"


def find_browser():
    configured = os.environ.get("IFP_BROWSER")
    if configured:
        return configured
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    sys.exit("Chrome ou Edge não encontrado. Defina IFP_BROWSER com o caminho do navegador.")


def rasterize(browser, svg, workdir):
    """Return a premultiplied RGBA float image rendered at RENDER_SIZE."""
    sized = svg.replace('viewBox="0 0 150 150"', f'viewBox="0 0 150 150" width="{RENDER_SIZE}" height="{RENDER_SIZE}"', 1)
    source = workdir / "logo.svg"
    target = workdir / "logo.png"
    source.write_text(sized, encoding="utf-8")
    subprocess.run([
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
        "--default-background-color=00000000", f"--window-size={RENDER_SIZE},{RENDER_SIZE}",
        f"--screenshot={target}", source.as_uri(),
    ], check=True, capture_output=True)
    image = cv2.imread(str(target), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    if image.shape[2] == 3:  # fully opaque renders come back without an alpha channel
        image = np.dstack([image, np.ones(image.shape[:2], np.float32)])
    image[:, :, :3] *= image[:, :, 3:]
    return image


def png_bytes(premultiplied, size):
    image = cv2.resize(premultiplied, (size, size), interpolation=cv2.INTER_AREA)
    alpha = image[:, :, 3:]
    image[:, :, :3] = np.divide(image[:, :, :3], alpha, out=np.zeros_like(image[:, :, :3]), where=alpha > 0)
    ok, encoded = cv2.imencode(".png", np.clip(image * 255 + .5, 0, 255).astype(np.uint8))
    assert ok
    return encoded.tobytes()


def ico_bytes(images):
    """Pack PNG images into a .ico container (supported by every current browser)."""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, payload = b"", b""
    for size, data in images:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset + len(payload))
        payload += data
    return header + entries + payload


def main():
    browser = find_browser()
    IMAGES.mkdir(parents=True, exist_ok=True)
    logo = svg_source("circle", 1)
    favicon = svg_source("circle", FAVICON_MARK_SCALE)
    (IMAGES / "logo-ifp.svg").write_text(logo, encoding="utf-8")
    (IMAGES / "favicon.svg").write_text(favicon, encoding="utf-8")
    with tempfile.TemporaryDirectory() as folder:
        workdir = Path(folder)
        circle = rasterize(browser, logo, workdir)
        small = rasterize(browser, favicon, workdir)
        square = rasterize(browser, svg_source("square", 1), workdir)
    outputs = {
        "favicon.ico": ico_bytes([(size, png_bytes(small, size)) for size in (16, 32, 48)]),
        "apple-touch-icon.png": png_bytes(square, 180),
        "icon-192.png": png_bytes(circle, 192),
        "icon-512.png": png_bytes(circle, 512),
        "icon-maskable-512.png": png_bytes(square, 512),
    }
    for name, data in outputs.items():
        (IMAGES / name).write_bytes(data)
    print("Ícones gerados em", IMAGES.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
