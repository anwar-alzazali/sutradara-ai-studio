"""Latar = PRESET SUASANA (resep A2): sedikit preset yang dipakai ulang, dipetakan ke busur emosi.

Setiap preset menggambar lapis BELAKANG (langit, benda langit, gunung/kota) dan tanah. Kabut jarak jauh untuk
NPC tersedia lewat `kabut_jauh(preset)`, digambar SETELAH NPC jauh dan SEBELUM tokoh dekat.
"""
from __future__ import annotations

import random

PRESET = {
    # nama: (gradien langit, warna gunung jauh, warna gunung dekat, gradien tanah, warna kabut jauh)
    "senja": (["#1b1530", "#3b2547", "#a5546a", "#e59a6b"], "#4a2c4a", "#3a2440", ["#5a3a3e", "#1d1420"], "#a5546a"),
    "dhuha": (["#8fb4cf", "#c8d4d8", "#d9c7a0", "#c9a46e"], "#b58f66", "#a07c58", ["#c49a62", "#6e4a2c"], "#d9c7a0"),
    "malam": (["#070a18", "#101634", "#1c2244", "#2a2f55"], "#141a2c", "#10152a", ["#1a1e33", "#0b0d18"], "#2a2f55"),
    "malam_merah": (["#120d1c", "#2b1a2e", "#5a2a2a", "#5a2a2a"], "#2a1828", "#221420", ["#1e1420", "#140d16"], "#5a2a2a"),
    "fajar": (["#2c2a52", "#6b5a8a", "#e8a27a", "#ffd9a0"], "#5a4a6a", "#463a58", ["#4a3a48", "#221a26"], "#e8a27a"),
}


def langit(preset: str, *, matahari: tuple[float, float] | None = None, bintang: int = 60, seed: int = 3) -> str:
    if preset not in PRESET:
        raise ValueError(f"preset tak dikenal: {preset} (pilihan: {', '.join(PRESET)})")
    g, gj, gd, tn, _ = PRESET[preset]
    rnd = random.Random(seed)
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in zip((0, .45, .72, .86), g))
    s = [f'<defs><linearGradient id="l_{preset}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>'
         f'<linearGradient id="t_{preset}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{tn[0]}"/><stop offset="1" stop-color="{tn[1]}"/></linearGradient>'
         '<radialGradient id="surya"><stop offset="0" stop-color="#ffe2b0" stop-opacity=".95"/><stop offset=".25" stop-color="#ffb27a" stop-opacity=".6"/>'
         '<stop offset="1" stop-color="#ff8a6a" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="1080" height="1920" fill="url(#l_{preset})"/>']
    if matahari:
        s.append(f'<circle cx="{matahari[0]}" cy="{matahari[1]}" r="420" fill="url(#surya)"/>')
    if preset != "dhuha":
        for _ in range(bintang):
            s.append(f'<circle cx="{rnd.uniform(0, 1080):.0f}" cy="{rnd.uniform(0, 650):.0f}" r="{rnd.uniform(.8, 2.2):.1f}" '
                     f'fill="#fff" opacity="{rnd.uniform(.25, .7):.2f}"/>')
    return "\n".join(s)


def gunung(preset: str) -> str:
    _, gj, gd, _, _ = PRESET[preset]
    return (f'<path d="M-40 1180 L180 900 L330 1040 L520 820 L760 1060 L900 960 L1120 1140 L1120 1260 L-40 1260Z" fill="{gj}" opacity=".85"/>'
            f'<path d="M-40 1220 L120 1080 L300 1170 L470 1050 L640 1160 L860 1070 L1120 1200 L1120 1300 L-40 1300Z" fill="{gd}"/>')


def kota(preset: str, seed: int = 21) -> str:
    rnd = random.Random(seed)
    _, gj, _, tn, _ = PRESET[preset]
    s = []
    for k in range(9):
        x = -20 + k * 130 + rnd.uniform(-20, 20); w = rnd.uniform(90, 150); h = rnd.uniform(110, 230)
        s.append(f'<rect x="{x:.0f}" y="{1180 - h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{gj}" opacity=".8"/>')
        for j in range(2):
            s.append(f'<rect x="{x + 18 + j * 40:.0f}" y="{1180 - h + 30:.0f}" width="18" height="26" fill="{tn[1]}" opacity=".6"/>')
    return "\n".join(s)


def tanah(preset: str, y: float = 1250) -> str:
    return f'<rect y="{y}" width="1080" height="{1920 - y}" fill="url(#t_{preset})"/>'


def kabut_jauh(preset: str, y0: float = 1100, y1: float = 1290, kuat: float = .38) -> str:
    return f'<rect x="0" y="{y0}" width="1080" height="{y1 - y0}" fill="{PRESET[preset][4]}" opacity="{kuat}"/>'


def batu_depan(warna: str = "#120c16") -> str:
    """Lapis DEPAN kabur di pojok bawah (resep B4)."""
    return (f'<path d="M-60 1920 L-60 1700 Q 40 1610 170 1680 Q 260 1730 290 1920Z" fill="{warna}" filter="url(#kabur)"/>'
            f'<path d="M1140 1920 L1140 1660 Q 1020 1600 900 1700 Q 850 1760 860 1920Z" fill="{warna}" filter="url(#kabur)"/>')
