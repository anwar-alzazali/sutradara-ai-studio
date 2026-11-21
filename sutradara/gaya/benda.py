"""Benda adegan. Benda yang menjadi VISUAL INTI (resep A1) wajib punya parameter keadaan 0..1."""
from __future__ import annotations

import math
import random


def bahtera(x: float, y: float, s: float = 1.0, *, jadi: float = 0.6) -> str:
    """Kapal Nabi Nuh di darat. jadi=0 rangka awal, 1 = lambung tertutup penuh. (x, y) = ujung kiri lunas."""
    jadi = max(0.0, min(1.0, jadi))
    g = [f'<g class="bahtera" transform="translate({x},{y}) scale({s})">',
         '<path d="M0 0 Q 260 120 540 0 L 520 -30 Q 260 80 20 -30Z" fill="#6b4630"/>']
    n = 11
    for i in range(n):
        xx = 40 + i * 46; h = 150 + 40 * math.sin(i / (n - 1) * math.pi)
        g.append(f'<path d="M{xx} {-20 + 30 * math.sin(i / 10 * math.pi):.0f} Q {xx - 10} {-h * .6:.0f} {xx + 6} {-h:.0f}" '
                 f'fill="none" stroke="#7a5236" stroke-width="12" stroke-linecap="round"/>')
    papan = int(round(jadi * 7))
    for j in range(papan):  # papan lambung dipasang dari bawah ke atas
        yy = -30 - j * 18
        g.append(f'<path d="M30 {yy} Q 270 {yy + 70 - j * 6} 510 {yy}" fill="none" stroke="#8a6040" stroke-width="16"/>')
    g.append('<path d="M40 -150 Q 270 -205 500 -150" fill="none" stroke="#5a3a26" stroke-width="8"/>')
    if jadi < 1:
        g.append('<g stroke="#4a3020" stroke-width="7"><line x1="560" y1="0" x2="600" y2="-190"/><line x1="600" y1="0" x2="640" y2="-190"/>'
                 + "".join(f'<line x1="{564 + i * 8}" y1="{-i * 38}" x2="{604 + i * 8}" y2="{-i * 38}"/>' for i in range(1, 5)) + "</g>")
    g.append("</g>")
    return "\n".join(g)


def lapak(x: float, y: float, warna: str = "#b8452e") -> str:
    """Lapak pasar bertenda. (x, y) = pojok kiri atas meja."""
    buah = "".join(f'<circle cx="{x + 30 + j * 45}" cy="{y + 55}" r="16" fill="{c}"/>'
                   for j, c in enumerate(["#e0a040", "#c05030", "#7a9a40", "#e0c060"]))
    return (f'<rect x="{x}" y="{y}" width="200" height="140" fill="#8a5a34"/><path d="M{x - 20} {y} L{x + 100} {y - 70} L{x + 220} {y}Z" fill="{warna}"/>'
            f'<path d="M{x - 20} {y} h240" stroke="#f0e0c0" stroke-width="8" stroke-dasharray="24 16"/>{buah}')


def sungai(jenis: str, *, sisi: str, seed: int = 33, t: float = 0.0) -> str:
    """Sungai dari kaki bukit tengah ke depan. jenis: 'air' | 'api'; sisi: 'kiri' | 'kanan'."""
    rnd = random.Random(seed)
    kiri = ("M470 1250 Q 380 1400 220 1520 Q 120 1600 -20 1640 L -20 1820 Q 160 1760 300 1640 Q 430 1520 520 1260Z")
    kanan = ("M610 1250 Q 700 1400 860 1520 Q 960 1600 1100 1640 L 1100 1820 Q 920 1760 780 1640 Q 650 1520 560 1260Z")
    d = kiri if sisi == "kiri" else kanan
    if jenis == "air":
        return (f'<defs><linearGradient id="sair" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bfe8ff"/><stop offset="1" stop-color="#4aa0d0"/></linearGradient></defs>'
                f'<path d="{d}" fill="url(#sair)" opacity=".95"/>'
                f'<ellipse cx="{200 if sisi == "kiri" else 880}" cy="1560" rx="260" ry="120" fill="#bfe8ff" opacity="{.22 + .08 * math.sin(t * 2):.3f}" filter="url(#b60)"/>'
                + "".join(f'<path d="M{(60 + k * 70 + t * 40) % 500 + (0 if sisi == "kiri" else 560):.0f} {1540 + k * 18} q 20 -6 40 0" stroke="#e8f8ff" stroke-width="3" fill="none" opacity=".5"/>' for k in range(6)))
    s = ['<defs><linearGradient id="sapi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a"/><stop offset=".5" stop-color="#ff7a2a"/>'
         '<stop offset="1" stop-color="#b8301a"/></linearGradient></defs>', f'<path d="{d}" fill="url(#sapi)"/>']
    for k in range(26):
        t_ = k / 25
        x = (600 + t_ * 480) if sisi == "kanan" else (480 - t_ * 480)
        x += rnd.uniform(-20, 20); y = 1270 + t_ * 420 + rnd.uniform(-10, 30); h = rnd.uniform(50, 120) * (0.75 + 0.3 * math.sin(t * 9 + k * 1.9))
        s.append(f'<path d="M{x - 18:.0f} {y:.0f} Q {x - 6:.0f} {y - h * .6:.0f} {x:.0f} {y - h:.0f} Q {x + 8:.0f} {y - h * .5:.0f} {x + 18:.0f} {y:.0f}Z" fill="#ffb24a" opacity=".85"/>')
    s.append(f'<ellipse cx="{880 if sisi == "kanan" else 200}" cy="1560" rx="300" ry="160" fill="#ff7a2a" opacity=".3" filter="url(#b60)"/>')
    return "\n".join(s)
