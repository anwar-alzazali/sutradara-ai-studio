"""Makhluk ghaib.

Aturan (docs/PANDUAN_GAYA.md):
- Wujud TIDAK dijelaskan dalil sahih (Dabbatul Ard, jin, dsb.) -> `kabut_tanpa_wujud`: gumpalan gelap bergulung,
  tanpa garis tepi tubuh, mata, kepala, atau ukuran yang jelas. Warna tanah gelap + pendar keemasan redup,
  BUKAN hitam pekat "jahat", dan tidak simetris dengan pilar nur.
- Wujud dijelaskan dalil -> digambar sesuai dalil saja (mis. `dajjal.sosok`, Ya'juj Ma'juj = manusia biasa).
"""
from __future__ import annotations

import math
import random


def kabut_tanpa_wujud(x: float, y: float, *, tinggi: float = 820, seed: int = 21, t: float = 0.0, keluar: float = 1.0) -> str:
    """Kabut tanah gelap keluar dari titik (x, y), menjulang setinggi `tinggi`.
    `keluar` 0..1 = seberapa jauh kabut sudah keluar (keadaan, bisa di-keyframe); `t` = waktu global untuk gerak bergulung."""
    rnd = random.Random(seed)
    s = ['<g class="kabut-tanpa-wujud"><defs>'
         '<radialGradient id="kpendar"><stop offset="0" stop-color="#ffcf7a" stop-opacity=".55"/><stop offset="1" stop-color="#ffcf7a" stop-opacity="0"/></radialGradient>'
         '<radialGradient id="kgumpal"><stop offset="0" stop-color="#2a1c14" stop-opacity=".95"/><stop offset=".6" stop-color="#3b2818" stop-opacity=".75"/>'
         '<stop offset="1" stop-color="#4a3420" stop-opacity="0"/></radialGradient></defs>',
         f'<ellipse cx="{x}" cy="{y - tinggi * .4:.0f}" rx="380" ry="{tinggi * .58:.0f}" fill="url(#kpendar)" filter="url(#b60)"/>']
    keluar = max(0.0, min(1.0, keluar))
    for k in range(46):
        h = k / 45
        if h > keluar:
            break
        jx, jy, jr = rnd.uniform(-40, 40), rnd.uniform(-30, 30), rnd.uniform(-20, 30)
        cx = x + math.sin(k * 1.7 + t * 0.7) * 60 * (1 + h * 3) + jx
        cy = y - h * tinggi + jy - 25 * math.sin(t * 0.9 + k)
        r = (70 + h * 170 + jr) * (1 + 0.06 * math.sin(t * 1.4 + k * 0.5))
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#kgumpal)" '
                 f'opacity="{0.55 - h * 0.25:.2f}" filter="url(#b28)"/>')
    for i in range(40):  # bara redup naik pelan
        bx, cepat = rnd.gauss(0, 120), rnd.uniform(20, 60)
        jalan = tinggi * .8 * keluar
        by = y - 180 - ((rnd.uniform(0, 1) * jalan + t * cepat) % max(jalan, 1))
        s.append(f'<circle cx="{x + bx + 14 * math.sin(t + i):.1f}" cy="{by:.1f}" r="{rnd.uniform(2, 6):.1f}" '
                 f'fill="#ffcf7a" opacity="{rnd.uniform(.25, .7):.2f}"/>')
    s.append("</g>")
    return "\n".join(s)


def retakan(x: float, y: float) -> str:
    """Retakan tanah dengan lubang gelap di tengah (titik keluarnya kabut)."""
    return ('<g stroke="#2a1a10" stroke-width="10" fill="none" stroke-linecap="round">'
            f'<path d="M{x} {y} l-70 50 l-40 90 l-70 50"/><path d="M{x} {y} l80 60 l20 80 l100 70"/>'
            f'<path d="M{x} {y} l-20 -80 l40 -50"/><path d="M{x - 70} {y + 50} l-70 -20"/><path d="M{x + 100} {y + 140} l80 -20"/></g>'
            f'<ellipse cx="{x}" cy="{y + 10}" rx="140" ry="40" fill="#1a100a"/>')
