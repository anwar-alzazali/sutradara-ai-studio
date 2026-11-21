"""Bentuk cahaya malaikat: berkas turun dari atas tanpa tubuh atau siluet.

Berbeda dari pilar nabi: tidak ada kapsul vertikal, lekuk tubuh, atau pusat cahaya
berbentuk manusia. Bentuk ini hanya berkas/sinar tanpa wujud.
"""
from __future__ import annotations

import math
import random


def berkas(x: float, y: float, *, tinggi: float = 1500, lebar: float = 260,
           t: float = 0.0, seed: int = 17) -> str:
    """Berkas cahaya dari atas ke titik (x, y), tanpa representasi tubuh."""
    if tinggi <= 0 or lebar <= 0:
        raise ValueError("tinggi dan lebar berkas harus positif")
    if tinggi < y:
        raise ValueError("berkas malaikat harus mencapai tepi atas bingkai; tinggi minimal sama dengan koordinat y")
    rnd = random.Random(seed)
    atas = 0.0
    pulse = 0.94 + 0.06 * math.sin(t * 1.4)
    bagian = [
        '<g class="cahaya-malaikat">',
        f'<path d="M{x - lebar * .12:.1f} {atas:.1f} L{x + lebar * .12:.1f} {atas:.1f} '
        f'L{x + lebar * .5:.1f} {y:.1f} L{x - lebar * .5:.1f} {y:.1f}Z" '
        f'fill="#fff5d8" opacity="{.12 * pulse:.3f}"/>',
        f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{lebar * .48:.1f}" ry="24" '
        f'fill="#fff1c7" opacity=".22"/>',
    ]
    # Sinar berasal dari batas atas bingkai; tidak membentuk kontur manusia.
    for i in range(19):
        u = (i / 18) - .5
        drift = math.sin(t * .7 + i) * 8
        end_x = x + u * lebar * 1.8 + drift
        bagian.append(
            f'<path d="M{x + u * lebar * .18:.1f} {atas:.1f} '
            f'L{end_x:.1f} {y:.1f}" stroke="#fff9e9" '
            f'stroke-width="{rnd.uniform(2, 7):.1f}" opacity="{rnd.uniform(.08, .2):.3f}" '
            'stroke-linecap="round"/>'
        )
    for i in range(24):
        px = x + rnd.uniform(-lebar * .42, lebar * .42)
        py = rnd.uniform(atas, y)
        radius = rnd.uniform(1.2, 3.4)
        opacity = rnd.uniform(.18, .55) * (.75 + .25 * math.sin(t * 2 + i))
        bagian.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{radius:.1f}" '
            f'fill="#fffbea" opacity="{opacity:.3f}"/>'
        )
    bagian.append("</g>")
    return "\n".join(bagian)
