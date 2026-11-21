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
         f'<rect x="-1080" y="-1920" width="3240" height="5760" fill="url(#l_{preset})"/>']
    if matahari:
        s.append(f'<circle cx="{matahari[0]}" cy="{matahari[1]}" r="420" fill="url(#surya)"/>')
    if preset != "dhuha":
        for _ in range(bintang):
            s.append(f'<circle cx="{rnd.uniform(0, 1080):.0f}" cy="{rnd.uniform(0, 650):.0f}" r="{rnd.uniform(.8, 2.2):.1f}" '
                     f'fill="#fff" opacity="{rnd.uniform(.25, .7):.2f}"/>')
    return "\n".join(s)


def gunung(preset: str) -> str:
    _, gj, gd, _, _ = PRESET[preset]
    return (f'<path d="M-700 1260 L-400 1000 L-40 1180 L180 900 L330 1040 L520 820 L760 1060 L900 960 L1120 1140 L1400 980 L1780 1260Z" fill="{gj}" opacity=".85"/>'
            f'<path d="M-700 1300 L-380 1120 L-40 1220 L120 1080 L300 1170 L470 1050 L640 1160 L860 1070 L1120 1200 L1420 1090 L1780 1300Z" fill="{gd}"/>')


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
    return f'<rect x="-1080" y="{y}" width="3240" height="{3840 - y}" fill="url(#t_{preset})"/>'


def kabut_jauh(preset: str, y0: float = 1100, y1: float = 1290, kuat: float = .38) -> str:
    return f'<rect x="-1080" y="{y0}" width="3240" height="{y1 - y0}" fill="{PRESET[preset][4]}" opacity="{kuat}"/>'


def batu_depan(warna: str = "#120c16") -> str:
    """Siluet batu depan tajam; blur tidak aktif sebagai bawaan."""
    return (f'<path d="M-60 1920 L-60 1700 Q 40 1610 170 1680 Q 260 1730 290 1920Z" fill="{warna}" stroke="#08070c" stroke-width="8" stroke-linejoin="round"/>'
            f'<path d="M1140 1920 L1140 1660 Q 1020 1600 900 1700 Q 850 1760 860 1920Z" fill="{warna}" stroke="#08070c" stroke-width="8" stroke-linejoin="round"/>')

# Tekstur tanah disimpan sebagai geometri dunia: kamera menggerakkan seluruh pola,
# sehingga pola tidak berubah/berkedip ketika waktu frame berubah.
from functools import lru_cache
import math

PERMUKAAN_BAWAAN = {nama: "tanah_berbatu" for nama in PRESET}
PERMUKAAN_VALID = {"tanah_berbatu", "pasir", "tanah", "batu", "tanpa"}


def _campur_warna(a: str, b: str, t: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def _bentuk_bercak(rnd: random.Random, cx: float, cy: float, rx: float, ry: float, n: int = 8) -> str:
    titik = [(cx + math.cos(2 * math.pi * i / n) * rx * rnd.uniform(.72, 1.08),
              cy + math.sin(2 * math.pi * i / n) * ry * rnd.uniform(.72, 1.08)) for i in range(n)]
    d = f"M{(titik[0][0] + titik[-1][0]) / 2:.1f} {(titik[0][1] + titik[-1][1]) / 2:.1f}"
    for i, p in enumerate(titik):
        q = titik[(i + 1) % n]
        d += f" Q {p[0]:.1f} {p[1]:.1f} {(p[0] + q[0]) / 2:.1f} {(p[1] + q[1]) / 2:.1f}"
    return d + "Z"


@lru_cache(maxsize=64)
def _tekstur_tanah_cache(preset: str, y0: float, jenis: str, seed: int) -> str:
    if preset not in PRESET:
        raise ValueError(f"preset tak dikenal: {preset}")
    if jenis not in PERMUKAAN_VALID:
        raise ValueError(f"permukaan_tanah tak dikenal: {jenis} (pilihan: {', '.join(sorted(PERMUKAAN_VALID))})")
    if jenis == "tanpa":
        return ""
    rnd = random.Random(seed)
    warna_atas, warna_bawah = PRESET[preset][3]
    gelap = _campur_warna(warna_bawah, "#000000", .16)
    terang = _campur_warna(warna_atas, "#ffffff", .10)

    def skala(y: float) -> float:
        return .28 + (y - y0) / 540

    elemen = []
    # Bercak berkontras rendah memberi variasi material tanpa menjadi pola utama.
    for _ in range(30 if jenis in ("tanah_berbatu", "batu") else 24):
        y = rnd.uniform(y0 + 8, 1910)
        s = skala(y)
        x = rnd.uniform(-1080, 2160)
        warna = terang if rnd.random() < .48 else gelap
        op = rnd.uniform(.46, .64)
        elemen.append(f'<path d="{_bentuk_bercak(rnd, x, y, rnd.uniform(80, 210)*s, rnd.uniform(10, 26)*s)}" fill="{warna}" opacity="{op:.3f}"/>')

    # Guratan pasir berbentuk riak; tanah padat memakai retak/serat yang pendek.
    jumlah_guratan = 72 if jenis == "pasir" else 38
    for _ in range(jumlah_guratan):
        y = rnd.uniform(y0 + 12, 1905)
        s = skala(y)
        x = rnd.uniform(-1080, 2160)
        if jenis == "pasir":
            panjang = rnd.uniform(45, 115) * s
            elemen.append(f'<path d="M{x:.1f} {y:.1f} q {panjang*.25:.1f} {-3*s:.1f} {panjang*.5:.1f} 0 t {panjang*.5:.1f} 0" fill="none" stroke="{gelap}" stroke-width="{.65 + .65*s:.2f}" opacity=".25"/>')
        else:
            panjang = rnd.uniform(12, 34) * s
            elemen.append(f'<path d="M{x:.1f} {y:.1f} l {panjang:.1f} {rnd.uniform(-2,2)*s:.1f} l {panjang*.55:.1f} {rnd.uniform(-2,2)*s:.1f}" fill="none" stroke="{gelap}" stroke-width="{.7 + .55*s:.2f}" opacity=".28" stroke-linecap="round"/>')

    # Kerikil dibatasi pada area bawah dan diberi sorot tipis; tidak memakai filter/blur.
    if jenis in ("tanah_berbatu", "batu"):
        jumlah = 150 if jenis == "tanah_berbatu" else 168
        for _ in range(jumlah):
            y = rnd.uniform(y0 + 8, 1910)
            s = skala(y)
            x = rnd.uniform(-1080, 2160)
            besar = rnd.random() < .10 or jenis == "batu" and rnd.random() < .18
            rx = rnd.uniform(24, 42) * s if besar else rnd.uniform(5.5, 12) * s
            ry = rx * rnd.uniform(.48, .72)
            isi = _campur_warna(warna_atas, gelap, rnd.uniform(.18, .42))
            bentuk = _bentuk_bercak(rnd, x, y, rx, ry, 7)
            sorot = _bentuk_bercak(rnd, x-rx*.18, y-ry*.22, rx*.48, ry*.30, 6)
            elemen.append(f'<ellipse cx="{x+rx*.18:.1f}" cy="{y+ry*.42:.1f}" rx="{rx*1.12:.1f}" ry="{ry*.42:.1f}" fill="#000000" opacity=".34"/>'
                          f'<path d="{bentuk}" fill="{isi}" opacity="{rnd.uniform(.56, .70):.2f}"/>'
                          f'<path d="{sorot}" fill="{terang}" opacity=".62"/>')

    if jenis in ("tanah_berbatu", "tanah"):
        for _ in range(7):
            y = rnd.uniform(y0 + 45, 1870)
            s = skala(y)
            x = rnd.uniform(-1080, 2160)
            for _ in range(3):
                dx = rnd.uniform(-5, 5) * s
                tinggi = rnd.uniform(9, 18) * s
                elemen.append(f'<path d="M{x+dx:.1f} {y:.1f} q {rnd.uniform(-3,3)*s:.1f} {-tinggi*.55:.1f} {rnd.uniform(-8,8)*s:.1f} {-tinggi:.1f}" fill="none" stroke="{_campur_warna(terang, "#8f8057", .45)}" stroke-width="{.8+s*.45:.2f}" opacity=".24" stroke-linecap="round"/>')

    # Klip menjaga tekstur tetap di atas bidang tanah; adegan inti digambar setelah lapisan ini.
    return (f'<defs><clipPath id="tanah_tekstur_clip"><rect x="-1080" y="{y0:.1f}" width="3240" height="{max(0, 1920-y0):.1f}"/></clipPath></defs>'
            f'<g clip-path="url(#tanah_tekstur_clip)">{"".join(elemen)}</g>')


def tekstur_tanah(preset: str, y0: float = 1250, *, jenis: str | None = None, seed: int = 3) -> str:
    """Tekstur tanah deterministik di koordinat dunia; ikut kamera/paralaks dan tidak menutupi tokoh."""
    jenis = jenis or PERMUKAAN_BAWAAN.get(preset, "tanah_berbatu")
    return _tekstur_tanah_cache(preset, float(y0), jenis, int(seed))
