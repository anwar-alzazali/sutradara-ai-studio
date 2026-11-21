"""Dasar gaya visual: ukuran kanvas, font, filter & gradien bersama.

Semua gambar adalah SVG 1080x1920 (9:16). Modul gaya lain hanya menghasilkan potongan SVG (string);
penyusunan jadi satu adegan ada di `sutradara.adegan`.
"""
from __future__ import annotations

from pathlib import Path

LEBAR, TINGGI = 1080, 1920
AKAR = Path(__file__).resolve().parents[2]
FONT = {
    "Nunito": AKAR / "aset/font/nunito-latin-wght-normal.woff2",
    "Amiri": AKAR / "aset/font/amiri-quran-arabic-400-normal.woff2",
}

# palet teks (punya arti, lihat docs/PANDUAN_GAYA.md)
KUNING, PUTIH, MERAH = "#ffd27a", "#ffffff", "#ff6a4a"


def _filter(id_: str, kabur: float) -> str:
    # wilayah filter diperlebar supaya pendar tidak terpotong jadi kotak
    return (f'<filter id="{id_}" x="-100%" y="-100%" width="300%" height="300%">'
            f'<feGaussianBlur stdDeviation="{kabur}"/></filter>')


def defs() -> str:
    """Definisi bersama: filter kabur (b4/b10/b28/b60/kabur) dan gradien cahaya nur."""
    return ("<defs>"
            + _filter("b4", 4) + _filter("b10", 10) + _filter("b28", 28) + _filter("b60", 60) + _filter("kabur", 14)
            + '<radialGradient id="pendar"><stop offset="0" stop-color="#fffaf0" stop-opacity=".9"/>'
              '<stop offset=".35" stop-color="#fff1d0" stop-opacity=".45"/><stop offset="1" stop-color="#ffe7b8" stop-opacity="0"/></radialGradient>'
            + '<radialGradient id="genangan"><stop offset="0" stop-color="#fff3d8" stop-opacity=".75"/>'
              '<stop offset="1" stop-color="#ffd9a0" stop-opacity="0"/></radialGradient>'
            + '<linearGradient id="sinar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff6e0" stop-opacity=".5"/>'
              '<stop offset="1" stop-color="#fff6e0" stop-opacity="0"/></linearGradient>'
            + '<linearGradient id="sisiKiri" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff"/>'
              '<stop offset=".45" stop-color="#fff" stop-opacity=".35"/><stop offset=".6" stop-color="#000"/></linearGradient>'
            + '<radialGradient id="anggur" cx=".38" cy=".35"><stop offset="0" stop-color="#f1efe2"/>'
              '<stop offset=".6" stop-color="#d3d2c0"/><stop offset="1" stop-color="#a9a690"/></radialGradient>'
            + "</defs>")


def dokumen(isi: str) -> str:
    """Bungkus potongan SVG menjadi satu SVG utuh 1080x1920."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{LEBAR}" height="{TINGGI}" '
            f'viewBox="0 0 {LEBAR} {TINGGI}" font-family="Nunito">{defs()}{isi}</svg>')


def html(svg: str) -> str:
    """Halaman HTML berisi SVG dengan font lokal (dipakai perender Chromium)."""
    ff = "".join(f"@font-face{{font-family:{n};src:url('{p.as_uri()}') format('woff2');font-weight:200 1000}}"
                 for n, p in FONT.items())
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{ff}html,body{{margin:0;background:#000}}</style></head><body>{svg}</body></html>"
