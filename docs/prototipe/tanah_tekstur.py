"""PROTOTIPE (21 Nov 2026, Claude) — referensi untuk Tahap B, belum dipakai mesin.
Disetujui arahnya oleh pemilik: tanah perlu tekstur (bercak warna, batu, guratan/riak pasir) sesuai perspektif.
Integrasikan ke sutradara/gaya/latar.py (lihat docs/TAHAP_LANJUT.md / catatan PR #18), jangan diimpor dari sini.
"""
import math
import random


def _campur(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def _bercak(r, cx, cy, rx, ry, n=9):
    """Bentuk tak beraturan (gumpalan) dipipihkan perspektif."""
    tt = [2 * math.pi * i / n for i in range(n)]
    pts = [(cx + math.cos(a) * rx * r.uniform(.6, 1.15), cy + math.sin(a) * ry * r.uniform(.6, 1.15)) for a in tt]
    d = f"M{(pts[0][0] + pts[-1][0]) / 2:.0f} {(pts[0][1] + pts[-1][1]) / 2:.0f}"
    for i, p in enumerate(pts):
        q = pts[(i + 1) % n]
        d += f" Q {p[0]:.0f} {p[1]:.0f} {(p[0] + q[0]) / 2:.0f} {(p[1] + q[1]) / 2:.0f}"
    return d + "Z"


def tanah_tekstur(dasar_atas, dasar_bawah, cahaya, y0=1250, seed=3, jenis="tanah"):
    r = random.Random(seed)
    gelap = _campur(dasar_bawah, "#000000", .3)
    terang = _campur(dasar_atas, cahaya, .45)
    jauh = lambda yy: 0.25 + (yy - y0) / 560          # skala perspektif
    out = []
    # 1) bercak tanah terang/gelap besar (variasi warna alami)
    for _ in range(46):
        yy = r.uniform(y0 + 10, 1950); s = jauh(yy)
        warna, op = (terang, r.uniform(.10, .2)) if r.random() < .5 else (gelap, r.uniform(.15, .28))
        out.append(f'<path d="{_bercak(r, r.uniform(-1080, 2160), yy, r.uniform(90, 260) * s, r.uniform(14, 40) * s)}" fill="{warna}" opacity="{op:.2f}"/>')
    # 2) guratan / riak
    for _ in range(80):
        yy = r.uniform(y0 + 15, 1910); s = jauh(yy); xx = r.uniform(-1080, 2160)
        if jenis == "pasir":
            out.append(f'<path d="M{xx:.0f} {yy:.0f} q {35 * s:.0f} {-7 * s:.0f} {70 * s:.0f} 0 t {70 * s:.0f} 0 t {70 * s:.0f} 0" fill="none" stroke="{gelap}" stroke-width="{1.4 * s + .5:.1f}" opacity=".22"/>')
        else:
            out.append(f'<path d="M{xx:.0f} {yy:.0f} l {r.uniform(15, 45) * s:.0f} {r.uniform(-3, 3) * s:.0f} l {r.uniform(10, 30) * s:.0f} {r.uniform(-5, 5) * s:.0f}" fill="none" stroke="{gelap}" stroke-width="{1.3 * s + .6:.1f}" opacity=".4" stroke-linecap="round"/>')
    # 3) batu: banyak kerikil + beberapa batu sedang, bayangan + sisi gelap + sorot cahaya
    for i in range(170):
        yy = r.uniform(y0 + 8, 1915); s = jauh(yy); xx = r.uniform(-1080, 2160)
        besar = r.random() < .12
        rx = (r.uniform(14, 30) if besar else r.uniform(3, 9)) * s; ry = rx * r.uniform(.5, .75)
        isi = _campur(dasar_atas, gelap, r.uniform(.05, .45))
        out.append(f'<ellipse cx="{xx + rx * .25:.0f}" cy="{yy + ry * .55:.0f}" rx="{rx * 1.2:.1f}" ry="{ry * .5:.1f}" fill="#000" opacity=".3"/>'
                   f'<path d="{_bercak(r, xx, yy, rx, ry, 7)}" fill="{isi}"/>'
                   f'<path d="{_bercak(r, xx - rx * .25, yy - ry * .3, rx * .55, ry * .35, 6)}" fill="{terang}" opacity="{.6 if besar else .45}"/>')
    # 4) rumput kering jarang (bukan di pasir)
    if jenis != "pasir":
        for _ in range(16):
            yy = r.uniform(y0 + 40, 1880); s = jauh(yy) * 1.3; xx = r.uniform(-1080, 2160)
            helai = "".join(f'<path d="M{xx + r.uniform(-4, 4) * s:.0f} {yy:.0f} q {r.uniform(-6, 6) * s:.0f} {-10 * s:.0f} {r.uniform(-14, 14) * s:.0f} {-r.uniform(14, 26) * s:.0f}" stroke="{_campur(terang, "#9a8a52", .5)}" stroke-width="{1.5 * s:.1f}" fill="none" stroke-linecap="round"/>' for _ in range(6))
            out.append(f'<g opacity=".75">{helai}</g>')
    return "<g>" + "".join(out) + "</g>"
