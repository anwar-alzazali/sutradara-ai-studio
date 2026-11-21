"""Tokoh manusia biasa (kaum, NPC, orang beriman, pihak lawan).

Satu bentuk tubuh, dua mode tampil:
- mode="pakaian" (BAWAAN): gamis berwarna, ikat pinggang, penutup kepala, wajah berekspresi.
- mode="siluet": bentuk yang sama, gelap, tanpa wajah, tepi tersinari dari sisi kiri (arah cahaya utama).
Jarak jauh TIDAK memakai siluet; pakai `rinci=False` (tanpa wajah) + kabut dari latar (lihat docs/PANDUAN_GAYA.md).

DILARANG dipakai untuk nabi, malaikat, sahabat (pakai `nur.pilar`). Penjaga ada di `sutradara.rencana`.
"""
from __future__ import annotations

KULIT = ["#c98b62", "#a86a45", "#d9a07a", "#8d5a3b", "#b97a52"]
BAJU = [("#7a3b2e", "#d9b26a"), ("#3f5a6b", "#c9b48a"), ("#6b5a2e", "#e0d2b0"),
        ("#4b3a5e", "#c99a5a"), ("#2f4a3a", "#d6c08e"), ("#8a5a2a", "#f0e2c0")]
GELAP = "#150f1d"

JUBAH = "M-44 -252 Q 0 -266 44 -252 L 66 -10 Q 0 6 -66 -10Z"
# pose -> dua lengan: (path dari bahu, titik tangan)
POSE = {
    "tunjuk": [("M-40 -238 Q -95 -250 -150 -262", (-152, -263)), ("M40 -238 Q 66 -190 34 -150", (32, -148))],
    "tertawa": [("M-40 -238 Q -58 -180 -14 -158", (-12, -156)), ("M40 -238 Q 58 -180 14 -158", (12, -156))],
    "silang": [("M-40 -238 Q -36 -186 34 -192", (36, -192)), ("M40 -238 Q 36 -200 -32 -206", (-34, -206))],
    "angkat": [("M-40 -238 Q -60 -180 -30 -150", (-30, -148)), ("M40 -238 Q 86 -292 82 -346", (82, -348))],
    "kaget": [("M-40 -238 Q -92 -270 -70 -318", (-70, -320)), ("M40 -238 Q 92 -270 70 -318", (70, -320))],
    "mundur": [("M-40 -238 Q -110 -236 -132 -282", (-134, -284)), ("M40 -238 Q 70 -200 52 -160", (52, -158))],
    "tutup": [("M-40 -238 Q -60 -230 -16 -286", (-14, -288)), ("M40 -238 Q 70 -200 52 -160", (52, -158))],
    "berdiri": [("M-40 -238 Q -62 -190 -50 -140", (-50, -138)), ("M40 -238 Q 62 -190 50 -140", (50, -138))],
}
MIRING = {"tertawa": -10, "tunjuk": -4, "angkat": 6}
WAJAH = ("datar", "ejek", "tertawa", "takut", "pejam")
KEPALA = ("imamah", "kain", "kopiah", "tanpa")


def _wajah(jenis: str, pose: str) -> list[str]:
    g = ['<path d="M-30 -284 Q 0 -238 30 -284 Q 26 -262 0 -256 Q -26 -262 -30 -284Z" fill="#2a1b14"/>']  # janggut
    if jenis == "tertawa" or (jenis == "ejek" and pose == "tertawa"):
        g += ['<path d="M-17 -306 q 7 -7 14 0 M3 -306 q 7 -7 14 0" stroke="#2a1b14" stroke-width="4" fill="none" stroke-linecap="round"/>',
              '<path d="M-14 -284 Q 0 -266 14 -284Z" fill="#5a1e1e"/>']
    elif jenis == "takut":
        g += ['<circle cx="-12" cy="-304" r="7" fill="#fff"/><circle cx="12" cy="-304" r="7" fill="#fff"/>',
              '<circle cx="-12" cy="-303" r="3.5" fill="#2a1b14"/><circle cx="12" cy="-303" r="3.5" fill="#2a1b14"/>',
              '<path d="M-20 -318 l 12 -5 M20 -318 l -12 -5" stroke="#2a1b14" stroke-width="3.5" stroke-linecap="round"/>',
              '<ellipse cx="0" cy="-282" rx="8" ry="10" fill="#3a1414"/>']
    elif jenis == "pejam":
        g += ['<path d="M-18 -303 q 6 4 12 0 M6 -303 q 6 4 12 0" stroke="#2a1b14" stroke-width="3.5" fill="none" stroke-linecap="round"/>',
              '<path d="M-8 -284 h16" stroke="#5a1e1e" stroke-width="3.5" stroke-linecap="round"/>']
    else:  # datar / ejek: alis turun, senyum miring
        g += ['<circle cx="-11" cy="-304" r="4.5" fill="#2a1b14"/><circle cx="11" cy="-304" r="4.5" fill="#2a1b14"/>',
              '<path d="M-18 -315 l 12 4 M18 -315 l -12 4" stroke="#2a1b14" stroke-width="3.5" stroke-linecap="round"/>',
              ('<path d="M-12 -285 Q 2 -278 14 -290" stroke="#5a1e1e" stroke-width="4" fill="none" stroke-linecap="round"/>'
               if jenis == "ejek" else '<path d="M-9 -284 h18" stroke="#5a1e1e" stroke-width="3.5" stroke-linecap="round"/>')]
    return g


def orang(x: float, y: float, s: float = 1.0, *, pose: str = "berdiri", indeks: int = 0, mode: str = "pakaian",
          kepala: str = "imamah", wajah: str = "datar", rinci: bool = True, balik: bool = False) -> str:
    """Satu tokoh dengan kaki di (x, y). Tinggi ±350 px pada s=1."""
    if pose not in POSE:
        raise ValueError(f"pose tak dikenal: {pose} (pilihan: {', '.join(POSE)})")
    if mode not in ("pakaian", "siluet"):
        raise ValueError("mode harus 'pakaian' atau 'siluet'")
    siluet = mode == "siluet"
    kulit = GELAP if siluet else KULIT[indeks % len(KULIT)]
    baju, aksen = (GELAP, GELAP) if siluet else BAJU[indeks % len(BAJU)]
    lengan = POSE[pose]
    g = [f'<g transform="translate({x:.1f},{y:.1f}) scale({-s if balik else s},{s})">',
         '<ellipse cx="0" cy="4" rx="70" ry="12" fill="#000" opacity=".35"/>',
         '<ellipse cx="-24" cy="-4" rx="20" ry="9" fill="#2a1a14"/><ellipse cx="24" cy="-4" rx="20" ry="9" fill="#2a1a14"/>',
         f'<path d="{JUBAH}" fill="{baju}"/>']
    if not siluet:
        g += [f'<path d="M-8 -250 L 8 -250 L 6 -40 L -6 -40Z" fill="{aksen}" opacity=".55"/>',
              f'<path d="M-58 -120 Q 0 -108 58 -120 L 60 -102 Q 0 -90 -60 -102Z" fill="{aksen}"/>',
              f'<path d="M-62 -40 Q 0 -26 62 -40" fill="none" stroke="{aksen}" stroke-width="5" opacity=".7"/>']
    for p, (hx, hy) in lengan:
        g += [f'<path d="{p}" fill="none" stroke="{baju}" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>',
              f'<circle cx="{hx}" cy="{hy}" r="13" fill="{kulit}"/>']
    g += [f'<g transform="rotate({MIRING.get(pose, 0)} 0 -262)">',
          f'<rect x="-11" y="-272" width="22" height="22" fill="{kulit}"/>', f'<circle cx="0" cy="-298" r="34" fill="{kulit}"/>']
    if not siluet and rinci:
        g += _wajah(wajah, pose)
    tutup = GELAP if siluet else aksen
    if kepala == "imamah":
        g += [f'<path d="M-37 -306 Q -40 -346 0 -350 Q 40 -346 37 -306 Q 0 -318 -37 -306Z" fill="{tutup}"/>',
              f'<path d="M30 -312 Q 46 -280 40 -246" stroke="{tutup}" stroke-width="12" fill="none" stroke-linecap="round"/>']
    elif kepala == "kain":
        g += [f'<path d="M-40 -296 Q -44 -350 0 -352 Q 44 -350 40 -296 L 48 -238 L 30 -250 L 34 -300 Q 0 -320 -34 -300 L -30 -250 L -48 -238Z" fill="{tutup}"/>',
              '<path d="M-38 -322 Q 0 -336 38 -322" stroke="#2a1b14" stroke-width="6" fill="none"/>']
    elif kepala == "kopiah":
        g.append(f'<path d="M-30 -318 Q -30 -342 0 -342 Q 30 -342 30 -318Z" fill="{tutup}"/>')
    g.append("</g>")
    if siluet:  # tepi tersinari hanya di sisi yang menghadap cahaya
        mid = f"m{indeks}_{int(x)}_{int(y)}"
        g.insert(1, f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="-200" y="-420" width="400" height="460">'
                    f'<rect x="-90" y="-420" width="120" height="460" fill="url(#sisiKiri)"/></mask>')
        rim = [f'<path d="{JUBAH}" fill="none" stroke="#fff1cc" stroke-width="7"/>',
               '<circle cx="0" cy="-298" r="34" fill="none" stroke="#fff1cc" stroke-width="6"/>']
        rim += [f'<path d="{p}" fill="none" stroke="#fff1cc" stroke-width="30" stroke-linecap="round" opacity=".55"/>' for p, _ in lengan]
        g.append(f'<g mask="url(#{mid})" filter="url(#b4)">{"".join(rim)}</g>')
    else:
        g.append(f'<path d="{JUBAH}" fill="#ffe9c0" opacity=".18" transform="translate(-6,0) scale(.92,1)"/>')
    g.append("</g>")
    return "\n".join(g)
