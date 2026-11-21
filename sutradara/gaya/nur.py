"""Penanda kehadiran nabi: PILAR CAHAYA, bukan sosok.

Pilar putih tebal setinggi tokoh, sudut membulat penuh (kapsul) TANPA lekuk kepala, bahu, atau tangan,
ditambah pendar besar, semburan sinar halus, butiran cahaya, dan genangan cahaya di tanah.
Cahaya ini juga "jatuh" ke arah tokoh di sekitarnya (sinar=True) sehingga kehadiran terasa lewat reaksi orang.
"""
from __future__ import annotations

import math
import random


def pilar(x: float, y: float, *, tinggi: float = 400, lebar: float = 118, pendar_rx: float = 155, pendar_ry: float = 190, nama: str | None = None,
          sinar_ke: str | None = "kanan", seed: int = 7, t: float = 0.0) -> str:
    """Pilar cahaya dengan dasar di (x, y). `nama` tampil kecil di bawah (mis. 'Nabi Nuh a.s.').
    `t` = waktu global (detik): butiran melayang naik, sinar berdenyut pelan, pendar bernapas."""
    rnd = random.Random(seed)
    top = y - tinggi
    s = ['<g class="nur">',
         f'<ellipse cx="{x}" cy="{y}" rx="170" ry="36" fill="url(#genangan)" filter="url(#b10)" opacity=".32"/>',
         f'<ellipse cx="{x}" cy="{y - tinggi / 2}" rx="{pendar_rx + 8 * math.sin(t * 1.3):.1f}" ry="{pendar_ry + 10 * math.sin(t * 1.3):.1f}" fill="url(#pendar)" filter="url(#b28)" opacity=".42"/>']
    cx, cy = x, y - tinggi * 0.55
    for i in range(28):  # semburan sinar halus
        a = -math.pi / 2 + (i / 27 - .5) * math.pi * 1.9 + rnd.uniform(-.05, .05)
        L = rnd.uniform(240, 520)
        s.append(f'<line x1="{cx}" y1="{cy:.0f}" x2="{cx + math.cos(a) * L:.0f}" y2="{cy + math.sin(a) * L:.0f}" '
                 f'stroke="#fff6dd" stroke-width="{rnd.uniform(3, 9):.1f}" stroke-linecap="round" '
                 f'opacity="{rnd.uniform(.08, .22) * (0.7 + 0.3 * math.sin(t * 1.7 + i)):.3f}" filter="url(#b10)"/>')
    if sinar_ke == "kanan":
        s.append(f'<path d="M{x + 40} {y - 260} L1080 {y - 420} L1080 {y + 40} L{x + 40} {y - 60}Z" fill="url(#sinar)" opacity=".35" filter="url(#b28)"/>')
    elif sinar_ke == "kiri":
        s.append(f'<path d="M{x - 40} {y - 260} L0 {y - 420} L0 {y + 40} L{x - 40} {y - 60}Z" fill="url(#sinar)" opacity=".35" '
                 f'filter="url(#b28)" transform="translate({2 * x},0) scale(-1,1)"/>')
    w = lebar
    s += [f'<rect x="{x - w / 2 - 40}" y="{top - 40}" width="{w + 80}" height="{tinggi + 60}" rx="{(w + 80) / 2}" fill="#fff4dc" opacity=".45" filter="url(#b28)"/>',
          f'<rect x="{x - w / 2 - 10}" y="{top - 10}" width="{w + 20}" height="{tinggi + 16}" rx="{(w + 20) / 2}" fill="#fffaf0" opacity=".85" filter="url(#b10)"/>',
          f'<rect x="{x - w / 2 + 8}" y="{top + 10}" width="{w - 16}" height="{tinggi - 14}" rx="{(w - 16) / 2}" fill="#ffffff" filter="url(#b4)"/>']
    for i in range(70):  # butiran cahaya: melayang naik pelan, berputar ulang dari bawah
        bx, by = rnd.gauss(0, 150), rnd.gauss(0, 230)
        cepat, r, op = rnd.uniform(18, 45), rnd.uniform(1.5, 5), rnd.uniform(.3, .9)
        naik = ((by + 460 - t * cepat) % 920) - 460  # bergerak ke atas, ulang tiap 920 px
        goyang = 10 * math.sin(t * 0.9 + i)
        s.append(f'<circle cx="{x + bx + goyang:.1f}" cy="{y - tinggi * .5 + naik:.1f}" r="{r:.1f}" '
                 f'fill="#fffbe8" opacity="{op * (0.6 + 0.4 * math.sin(t * 2.3 + i * 0.7)):.2f}"/>')
    if nama:
        s.append(f'<text x="{x}" y="{y + 70}" text-anchor="middle" font-size="34" font-weight="700" fill="#fff6dd">{nama}</text>')
    s.append("</g>")
    return "\n".join(s)
