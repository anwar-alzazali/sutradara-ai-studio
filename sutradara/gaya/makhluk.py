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


def kabut_tanpa_wujud(x: float, y: float, *, tinggi: float = 820, seed: int = 21) -> str:
    """Kabut tanah gelap keluar dari titik (x, y) (mis. retakan bumi), menjulang setinggi `tinggi`."""
    rnd = random.Random(seed)
    s = ['<g class="kabut-tanpa-wujud"><defs>'
         '<radialGradient id="kpendar"><stop offset="0" stop-color="#ffcf7a" stop-opacity=".55"/><stop offset="1" stop-color="#ffcf7a" stop-opacity="0"/></radialGradient>'
         '<radialGradient id="kgumpal"><stop offset="0" stop-color="#2a1c14" stop-opacity=".95"/><stop offset=".6" stop-color="#3b2818" stop-opacity=".75"/>'
         '<stop offset="1" stop-color="#4a3420" stop-opacity="0"/></radialGradient></defs>',
         f'<ellipse cx="{x}" cy="{y - tinggi * .4:.0f}" rx="380" ry="{tinggi * .58:.0f}" fill="url(#kpendar)" filter="url(#b60)"/>']
    for k in range(46):
        t = k / 45
        cx = x + math.sin(k * 1.7) * 60 * (1 + t * 3) + rnd.uniform(-40, 40)
        cy = y - t * tinggi + rnd.uniform(-30, 30)
        s.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{70 + t * 170 + rnd.uniform(-20, 30):.0f}" fill="url(#kgumpal)" '
                 f'opacity="{0.55 - t * 0.25:.2f}" filter="url(#b28)"/>')
    for _ in range(40):
        s.append(f'<circle cx="{x + rnd.gauss(0, 120):.0f}" cy="{y - 180 - rnd.uniform(0, tinggi * .8):.0f}" r="{rnd.uniform(2, 6):.1f}" '
                 f'fill="#ffcf7a" opacity="{rnd.uniform(.25, .7):.2f}"/>')
    s.append("</g>")
    return "\n".join(s)


def retakan(x: float, y: float) -> str:
    """Retakan tanah dengan lubang gelap di tengah (titik keluarnya kabut)."""
    return ('<g stroke="#2a1a10" stroke-width="10" fill="none" stroke-linecap="round">'
            f'<path d="M{x} {y} l-70 50 l-40 90 l-70 50"/><path d="M{x} {y} l80 60 l20 80 l100 70"/>'
            f'<path d="M{x} {y} l-20 -80 l40 -50"/><path d="M{x - 70} {y + 50} l-70 -20"/><path d="M{x + 100} {y + 140} l80 -20"/></g>'
            f'<ellipse cx="{x}" cy="{y + 10}" rx="140" ry="40" fill="#1a100a"/>')
