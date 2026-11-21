"""Kamera shot (resep B3). Kamera hanya menggerakkan DUNIA; teks layar tidak ikut bergerak.

Spesifikasi (semua opsional, angka boleh keyframe):
  "kamera": {"zoom": [[0, 1.0], [4, 1.12]], "x": 540, "y": [[0, 1000], [4, 1080]],
             "guncang": [[2.1, 36]],   # detik, kuat (px) -> getaran yang meluruh ±0,6 dtk (dampak: ombak, petir, jebol)
             "hentak":  [[0.1, 0.06]]} # detik, kuat (proporsi zoom) -> sentakan maju sekejap (kata kontras/janji)
x, y = titik dunia yang berada di tengah layar. zoom 1 = seluruh kanvas 1080x1920 terlihat.

Kosakata bernama (pakai `pola(...)` untuk menulis rencana lebih cepat):
  dorong_pelan 1.0->1.12 · dekat 1.3->1.45 · sangat_dekat 1.95->2.2 · tarik_mundur 1.25->1.0 · menjauh 1.3->1.08
"""
from __future__ import annotations

import math

POLA = {
    "dorong_pelan": (1.0, 1.12), "dekat": (1.3, 1.45), "sangat_dekat": (1.95, 2.2),
    "tarik_mundur": (1.25, 1.0), "menjauh": (1.3, 1.08), "diam": (1.0, 1.0),
}


def pola(nama: str, durasi: float, x: float = 540, y: float = 960) -> dict:
    a, b = POLA[nama]
    return {"zoom": [[0, a], [durasi, b]], "x": x, "y": y}


def _zoom_hentak(peristiwa, t: float) -> float:
    f = 1.0
    for t0, kuat in peristiwa or []:
        if t >= t0:
            f += kuat * math.exp(-(t - t0) / 0.12)
    return f


def _geser_guncang(peristiwa, t: float) -> tuple[float, float]:
    dx = dy = 0.0
    for i, (t0, kuat) in enumerate(peristiwa or []):
        u = t - t0
        if 0 <= u < 0.8:
            a = kuat * math.exp(-u / 0.22)
            dx += a * math.sin(u * 63 + i * 1.3)
            dy += a * math.cos(u * 51 + i * 2.1)
    return dx, dy


def transform(kamera: dict | None, t: float) -> str:
    """Atribut transform SVG untuk lapisan dunia. `kamera` sudah di-resolve (angka, bukan keyframe) kecuali peristiwa."""
    k = kamera or {}
    z = float(k.get("zoom", 1.0)) * _zoom_hentak(k.get("hentak"), t)
    x, y = float(k.get("x", 540)), float(k.get("y", 960))
    dx, dy = _geser_guncang(k.get("guncang"), t)
    return f"translate({540 + dx:.2f},{960 + dy:.2f}) scale({z:.4f}) translate({-x:.2f},{-y:.2f})"
