"""Dajjal, desain B (disetujui pemilik 21 Nov 2026).

Hanya ciri dari hadis sahih yang digambar:
- mata kanan buta, menonjol seperti anggur (HR. Bukhari 7123) -> bola mata keruh tanpa pupil, berkelopak, TANPA gore;
- tertulis ك ف ر di antara kedua mata (HR. Bukhari 7131, Muslim 2933);
- rambut sangat keriting; muda (tanpa janggut).
Yang tidak disebut hadis dibuat netral: warna kulit sedang tanpa ciri ras, tinggi normal, tanpa taring/tanduk.
Jubah merah tua bersulam emas = pilihan gaya (penguasa yang meyakinkan), bukan klaim hadis.
Satu fungsi untuk semua jarak (dekat sampai penuh) supaya wajah konsisten antar shot.
"""
from __future__ import annotations

import math
import random

KULIT, KULIT_G = "#b98a68", "#9a6e50"
JUBAH, JUBAH_G, MANTEL, EMAS = "#7a1c2c", "#5a1220", "#2a0c16", "#d9a94a"


def sosok(x: float, y: float, s: float = 1.0, *, lengan: str = "terbuka", tepi_merah: bool = True, arah: str = "depan", t: float = 0.0, jalan: bool = False, jubah_berkibar: float = 0.0) -> str:
    """Dajjal dengan kaki di (x, y); tinggi ±420 px pada s=1. lengan: 'terbuka' | 'turun'."""
    if arah not in ("depan", "belakang"):
        raise ValueError("arah Dajjal hanya depan atau belakang")
    rnd = random.Random(5)
    ayun = math.sin(t * 4.0) * (5.0 if jalan else 0.0)
    kibas = max(-1.0, min(1.0, float(jubah_berkibar)))
    g = [f'<g class="dajjal" transform="translate({x:.1f},{y + ayun:.1f}) scale({s if arah == "depan" else -s},{s})">',
         '<ellipse cx="0" cy="4" rx="150" ry="18" fill="#000" opacity=".4"/>',
         f'<path d="M-92 -300 Q -170 -200 -175 0 L 175 0 Q 170 -200 92 -300Z" fill="{MANTEL}"/>',
         f'<path d="M-82 -304 Q 0 -318 82 -304 Q 118 -160 124 0 Q 0 14 -124 0 Q -118 -160 -82 -304Z" fill="{JUBAH}"/>',
         f'<path d="M-12 -306 L 12 -306 L 18 2 L -18 2Z" fill="{JUBAH_G}"/>',
         f'<path d="M-24 -306 L -30 2 M24 -306 L 30 2" stroke="{EMAS}" stroke-width="4"/>',
         f'<path d="M-122 -14 Q 0 0 122 -14" stroke="{EMAS}" stroke-width="5" fill="none"/>',
         f'<path d="M-104 -150 Q 0 -134 104 -150 L 106 -132 Q 0 -116 -106 -132Z" fill="{EMAS}"/>',
         f'<path d="M-46 -306 Q 0 -270 46 -306" stroke="{EMAS}" stroke-width="7" fill="none"/>']
    if lengan == "terbuka":
        tangan = [((-82, -296), (-150, -240), (-205, -175)), ((82, -296), (150, -240), (205, -175))]
    elif lengan == "turun":
        tangan = [((-82, -296), (-112, -220), (-108, -140)), ((82, -296), (112, -220), (108, -140))]
    else:
        raise ValueError("lengan: 'terbuka' | 'turun'")
    for a, b, c in tangan:
        g += [f'<path d="M{a[0]} {a[1]} Q {b[0]} {b[1]} {c[0]} {c[1]}" stroke="{JUBAH}" stroke-width="44" fill="none" stroke-linecap="round"/>',
              f'<circle cx="{c[0]}" cy="{c[1]}" r="17" fill="{KULIT}"/>']
    g += [f'<rect x="-16" y="-330" width="32" height="30" fill="{KULIT_G}"/>',
          f'<ellipse cx="0" cy="-366" rx="42" ry="48" fill="{KULIT}"/>',
          f'<ellipse cx="-43" cy="-362" rx="7" ry="11" fill="{KULIT_G}"/><ellipse cx="43" cy="-362" rx="7" ry="11" fill="{KULIT_G}"/>']
    for k in range(34):  # rambut sangat keriting
        a = math.pi * (0.95 + k / 33 * 1.1); rr = 44 + rnd.uniform(-2, 6)
        g.append(f'<circle cx="{math.cos(a) * rr:.1f}" cy="{-372 + math.sin(a) * rr * 1.08:.1f}" r="{rnd.uniform(9, 12):.1f}" fill="#1c1210"/>')
    for k in range(18):
        a = math.pi * (1.12 + k / 17 * 0.76); rr = 30 + rnd.uniform(-3, 3)
        g.append(f'<circle cx="{math.cos(a) * rr:.1f}" cy="{-380 + math.sin(a) * rr:.1f}" r="{rnd.uniform(9, 11):.1f}" fill="#1c1210"/>')
    g += ['<path d="M-30 -374 L -8 -368 M30 -374 L 8 -368" stroke="#1c1210" stroke-width="4" stroke-linecap="round"/>',
          # mata kanan (sisi kiri layar): buta, menonjol, keruh, tanpa pupil
          '<ellipse cx="-17" cy="-357" rx="11" ry="10" fill="url(#anggur)"/>',
          '<ellipse cx="-20" cy="-361" rx="3.2" ry="2.2" fill="#fff" opacity=".75"/>',
          f'<path d="M-30 -360 Q -17 -372 -4 -360" stroke="{KULIT_G}" stroke-width="3.2" fill="none" stroke-linecap="round"/>',
          f'<path d="M-28 -351 Q -17 -345 -6 -351" stroke="{KULIT_G}" stroke-width="2.4" fill="none" stroke-linecap="round" opacity=".8"/>',
          # mata kiri: normal, tajam
          '<path d="M7 -358 Q 17 -366 27 -358 Q 17 -352 7 -358Z" fill="#fff"/><circle cx="17" cy="-358.5" r="3.6" fill="#1c1210"/>',
          '<text x="0" y="-379" text-anchor="middle" font-family="Amiri" font-size="13" fill="#3a1010" opacity=".9">ك ف ر</text>',
          f'<path d="M0 -356 Q -4 -344 2 -340" stroke="{KULIT_G}" stroke-width="3" fill="none" stroke-linecap="round"/>',
          '<path d="M-12 -331 Q 0 -328 15 -336" stroke="#5a1e1e" stroke-width="3.2" fill="none" stroke-linecap="round"/>']
    if tepi_merah:
        g += ['<path d="M-124 0 Q -118 -160 -82 -304 Q 0 -318 82 -304 Q 118 -160 124 0" fill="none" stroke="#ff7a4a" stroke-width="4" opacity=".45" filter="url(#b4)"/>',
              '<ellipse cx="0" cy="-372" rx="54" ry="58" fill="none" stroke="#ff7a4a" stroke-width="4" opacity=".35" filter="url(#b4)"/>']
    g.append("</g>")
    return "\n".join(g)

def belakang(x: float, y: float, s: float = 1.0, *, t: float = 0.0, jalan: bool = False,
             jubah_berkibar: float = 0.0, buka: float = 0.0) -> str:
    """Tampak belakang Dajjal; jubah bergerak dan lengan membuka perlahan."""
    kibas = max(-1.0, min(1.0, float(jubah_berkibar)))
    u = max(0.0, min(1.0, float(buka)))
    ayun = math.sin(t * 4.0) * (5.0 if jalan else 0.0)
    sudut = 18 + 52 * u
    tangan_kiri = (-82 - 120 * math.sin(math.radians(sudut)), -280 - 90 * math.sin(math.radians(sudut)))
    tangan_kanan = (82 + 120 * math.sin(math.radians(sudut)), -280 - 90 * math.sin(math.radians(sudut)))
    return (f'<g class="dajjal belakang" transform="translate({x:.1f},{y+ayun:.1f}) scale({s})>'
            '<ellipse cx="0" cy="4" rx="150" ry="18" fill="#000" opacity=".4"/>'
            f'<path d="M{-92-25*kibas:.1f} -300 Q0 -325 {92+25*kibas:.1f} -300 Q{175+35*kibas:.1f} -160 {180+30*kibas:.1f} 0 L-180 0 Q{-175-35*kibas:.1f} -160 {-92-25*kibas:.1f} -300Z" fill="{MANTEL}"/>'
            f'<path d="M-82 -304 Q0 -318 82 -304 Q{118+30*kibas:.1f} -160 {124+25*kibas:.1f} 0 Q0 14 {-124-25*kibas:.1f} 0 Q{-118-30*kibas:.1f} -160 -82 -304Z" fill="{JUBAH}"/>'
            f'<path d="M-82 -296 Q{tangan_kiri[0]:.1f} {tangan_kiri[1]:.1f} -205 -175 M82 -296 Q{tangan_kanan[0]:.1f} {tangan_kanan[1]:.1f} 205 -175" stroke="{JUBAH}" stroke-width="44" fill="none" stroke-linecap="round"/>'
            f'<path d="M-42 -390 Q0 -430 42 -390 L48 -330 Q0 -300 -48 -330Z" fill="#1c1210"/>'
            f'<path d="M-30 -300 L-18 0 M30 -300 L18 0" stroke="{EMAS}" stroke-width="4" opacity=".7"/>'
            + (f'<path d="M-38 -8 L{-52 + 16*math.sin(t*4):.1f} 48 L{-64 + 16*math.sin(t*4):.1f} 58 M38 -8 L{52 - 16*math.sin(t*4):.1f} 48 L{64 - 16*math.sin(t*4):.1f} 58" stroke="#241a18" stroke-width="22" stroke-linecap="round" fill="none"/>' if jalan else '') + '</g>')
