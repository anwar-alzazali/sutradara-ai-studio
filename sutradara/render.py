"""Perender: SVG -> PNG lewat Chromium headless (Playwright). Satu peramban dipakai untuk banyak gambar.

Chromium: memakai Chromium bawaan Playwright (`python -m playwright install chromium`). Bila tidak ada, set
variabel lingkungan CHROME_PATH ke peramban Chrome/Chromium yang terpasang.
"""
from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .gaya import dasar


@contextmanager
def peramban():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        jalur = os.environ.get("CHROME_PATH")
        try:
            b = p.chromium.launch(executable_path=jalur) if jalur else p.chromium.launch()
        except Exception:
            cadangan = next((c for c in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser") if Path(c).exists()), None)
            if not cadangan:
                raise
            b = p.chromium.launch(executable_path=cadangan)
        pg = b.new_page(viewport={"width": dasar.LEBAR, "height": dasar.TINGGI})
        try:
            yield pg
        finally:
            b.close()


def png(svg: str, keluar: Path, halaman=None) -> Path:
    """Render satu SVG ke PNG 1080x1920."""
    keluar = Path(keluar); keluar.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(dasar.html(svg)); html = Path(f.name)
    try:
        if halaman is None:
            with peramban() as pg:
                pg.goto(html.as_uri()); pg.wait_for_timeout(300); pg.screenshot(path=str(keluar))
        else:
            halaman.goto(html.as_uri()); halaman.wait_for_timeout(300); halaman.screenshot(path=str(keluar))
    finally:
        html.unlink(missing_ok=True)
    return keluar
