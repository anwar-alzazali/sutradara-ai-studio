"""Benda adegan. Benda yang menjadi VISUAL INTI (resep A1) wajib punya parameter keadaan 0..1."""
from __future__ import annotations

import math
import random


def _klem(v: float) -> float:
    return max(0.0, min(1.0, v))


def bahtera(x: float, y: float, s: float = 1.0, *, jadi: float = 1.0, goyang: float = 0.0, cahaya: float = 0.8,
            pintu: float = 0.0, orang: int = 0, darat: bool = True, t: float = 0.0) -> str:
    """Kapal Nabi Nuh dari papan dan pasak (QS Al-Qamar 13), tampak samping. (x, y) = tengah lunas.

    Asal: mesin-video/papan/cerita.js jenis "bahtera" (16 Nov 2026), di-port ke Python tanpa mengubah desain.
    jadi 0..1 : rusuk saja -> papan berpasak naik mengisi lambung (0,12-0,67) -> rumah geladak berjendela (0,7-1).
    goyang    : derajat ayunan di air (0 di darat). cahaya 0..1: lampu jendela & tepi emas. pintu 0..1: pintu menyala + titian.
    orang     : jumlah penumpang kecil di geladak. darat: penyangga kayu + bayangan di tanah. Lebar ±990 px pada s=1.
    """
    W, H = 460, 250
    rnd = random.Random(11)
    jd, ch, pt = _klem(jadi), _klem(cahaya), _klem(pintu)
    pp, rh = _klem((jd - 0.12) / 0.55), _klem((jd - 0.7) / 0.3)
    lamb = f"M {-W} {-H} Q {-W + 20} -50 {-W + 190} 0 L {W - 170} 0 Q {W + 10} -70 {W + 70} {-H - 46} L {W - 20} {-H} Z"
    uid = f"bh{int(x)}_{int(y)}"
    g = [f'<g class="bahtera" transform="translate({x:.1f},{y:.1f}) scale({s})">',
         f'<defs><linearGradient id="{uid}k" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9a6638"/>'
         f'<stop offset=".6" stop-color="#5e3a20"/><stop offset="1" stop-color="#2a180e"/></linearGradient>'
         f'<linearGradient id="{uid}s" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000" stop-opacity="0"/>'
         f'<stop offset="1" stop-color="#000" stop-opacity=".5"/></linearGradient><clipPath id="{uid}c"><path d="{lamb}"/></clipPath>'
         f'<radialGradient id="{uid}l"><stop offset="0" stop-color="#fff3c8"/><stop offset=".5" stop-color="#ffc45a" stop-opacity=".8"/>'
         f'<stop offset="1" stop-color="#ff9a3a" stop-opacity="0"/></radialGradient></defs>']
    if darat:
        g.append('<ellipse cx="20" cy="14" rx="510" ry="48" fill="#08070a" opacity=".62"/>')
        for px in (-330, -150, 60, 250):
            g.append(f'<path d="M {px - 46} 14 L {px} -64 L {px + 46} 14" stroke="#3a2416" stroke-width="16" fill="none" stroke-linecap="round"/>'
                     f'<path d="M {px - 50} 10 L {px - 4} -68" stroke="#c08a50" stroke-width="4" fill="none" opacity=".5"/>')
    g.append(f'<g transform="translate(0 {goyang * 3 * math.sin(t * 0.9 + 1):.1f}) rotate({goyang * math.sin(t * 1.3):.2f})">')
    if pp < 0.99:  # rusuk lengkung + kilau
        for i in range(12):
            xx = -W + 70 + i * ((2 * W - 150) / 11); kl = (xx / W) * 34
            g.append(f'<path d="M {xx:.1f} -4 Q {xx + kl * .3:.1f} {-H * .5} {xx + kl:.1f} {-H - 8}" stroke="#7a4f2b" stroke-width="13" fill="none" stroke-linecap="round"/>'
                     f'<path d="M {xx - 5:.1f} -6 Q {xx + kl * .3 - 5:.1f} {-H * .5} {xx + kl - 5:.1f} {-H - 8}" stroke="#e0a868" stroke-width="3" fill="none" opacity=".55"/>')
    g.append(f'<path d="M {-W + 150} 0 L {W - 150} 0" stroke="#3a2416" stroke-width="22" stroke-linecap="round"/>')  # lunas
    if pp > 0.01:
        yt = -(H + 60) * pp
        g.append(f'<g clip-path="url(#{uid}c)"><rect x="{-W - 20}" y="{yt:.1f}" width="{2 * W + 140}" height="{-yt + 20:.1f}" fill="url(#{uid}k)"/>')
        r0 = 0
        while r0 * 36 < -yt:  # lajur papan berselang-seling + pasak
            yy = -r0 * 36
            g.append(f'<line x1="{-W - 20}" y1="{yy}" x2="{W + 100}" y2="{yy}" stroke="#1d120b" stroke-width="5"/>'
                     f'<line x1="{-W - 20}" y1="{yy + 5}" x2="{W + 100}" y2="{yy + 5}" stroke="#e0a868" stroke-width="2" opacity=".25"/>')
            for c0 in range(9):
                xx = -W + 40 + c0 * 118 + (r0 % 2) * 59 + rnd.random() * 20
                g.append(f'<line x1="{xx:.1f}" y1="{yy}" x2="{xx:.1f}" y2="{yy - 36}" stroke="#1d120b" stroke-width="3"/>'
                         f'<circle cx="{xx - 12:.1f}" cy="{yy - 18}" r="4.5" fill="#1a100a"/><circle cx="{xx + 12:.1f}" cy="{yy - 18}" r="4.5" fill="#1a100a"/>')
            r0 += 1
        g.append(f'<rect x="{-W - 20}" y="{yt:.1f}" width="{2 * W + 140}" height="{-yt + 20:.1f}" fill="url(#{uid}s)"/>')
        if pt > 0.01:
            g.append(f'<rect x="-70" y="-190" width="140" height="170" rx="10" fill="#1a0f08"/><rect x="-58" y="-180" width="116" height="160" rx="8" fill="#ffd27a" opacity="{pt:.2f}"/>')
        g.append("</g>")
        if pt > 0.01:
            g.append(f'<circle cx="0" cy="-100" r="{230 * pt:.1f}" fill="url(#{uid}l)" opacity="{.55 * pt:.2f}"/>'
                     f'<path d="M -72 -22 L 72 -22 L 250 96 L -250 96 Z" fill="#4a2e1a" opacity="{pt:.2f}"/>'
                     f'<path d="M -72 -22 L 72 -22" stroke="#e0a868" stroke-width="5" opacity="{.7 * pt:.2f}"/>')
        if pp >= 0.99:  # bibir geladak + tepi emas
            g.append(f'<path d="M {-W} {-H} L {W - 20} {-H} L {W + 70} {-H - 46}" stroke="#2a180e" stroke-width="20" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                     f'<path d="M {-W + 4} {-H - 8} L {W - 24} {-H - 8}" stroke="#ffd98a" stroke-width="5" fill="none" opacity="{.35 + .4 * ch:.2f}" stroke-linecap="round"/>'
                     f'<path d="M {-W - 4} {-H + 6} Q {-W + 14} -56 {-W + 180} -6" stroke="#ffd98a" stroke-width="5" fill="none" opacity="{.25 + .3 * ch:.2f}" stroke-linecap="round"/>')
    # Kontur gelap dan garis tepi hangat menjaga bentuk lambung terbaca pada shot jauh.
    g.append(f'<path d="{lamb}" fill="none" stroke="#160d08" stroke-width="22" stroke-linejoin="round" stroke-linecap="round"/>')
    g.append(f'<path d="M {-W + 18} {-H + 12} Q {-W + 40} -48 {-W + 195} -10 L {W - 178} -10 Q {W - 6} -72 {W + 45} {-H - 38}" fill="none" stroke="#f0bd79" stroke-width="7" opacity=".82" stroke-linecap="round"/>')
    if rh > 0.01:  # rumah geladak tumbuh ke atas
        hh, y0 = 150 * rh, -H - 10
        g.append(f'<rect x="-250" y="{y0 - hh:.1f}" width="470" height="{hh:.1f}" fill="#6b4324"/><rect x="-250" y="{y0 - hh:.1f}" width="470" height="{hh:.1f}" fill="url(#{uid}s)"/>')
        r0 = 1
        while r0 * 34 < hh:
            g.append(f'<line x1="-250" y1="{y0 - r0 * 34}" x2="220" y2="{y0 - r0 * 34}" stroke="#1d120b" stroke-width="4"/>'); r0 += 1
        if rh > 0.9:
            g.append(f'<path d="M -290 {y0 - hh:.1f} L -15 {y0 - hh - 96:.1f} L 260 {y0 - hh:.1f} Z" fill="#3a2416"/>'
                     f'<path d="M -290 {y0 - hh:.1f} L -15 {y0 - hh - 96:.1f}" stroke="#ffd98a" stroke-width="6" opacity="{.4 + .4 * ch:.2f}" stroke-linecap="round"/>')
            for wx in (-180, -70, 40, 150):
                g.append(f'<rect x="{wx - 26}" y="{y0 - 108}" width="52" height="62" rx="8" fill="#1a0f08"/>'
                         f'<rect x="{wx - 20}" y="{y0 - 102}" width="40" height="50" rx="6" fill="#ffd27a" opacity="{ch:.2f}"/>'
                         f'<circle cx="{wx}" cy="{y0 - 78}" r="70" fill="url(#{uid}l)" opacity="{.35 * ch:.2f}"/>')
    for i in range(orang):  # penumpang kecil di geladak (berwarna, bukan siluet hitam; lihat PANDUAN_GAYA)
        ox, oh = 262 + i * 44 + (i % 2) * 8, 62 + (i % 3) * 8
        warna = ["#7a3b2e", "#3f5a6b", "#6b5a2e", "#4b3a5e", "#2f4a3a"][i % 5]
        g.append(f'<g transform="translate({ox} {-H - 10})"><rect x="-13" y="{-oh}" width="26" height="{oh}" rx="12" fill="{warna}"/>'
                 f'<circle cy="{-oh - 13}" r="14" fill="#b97a52"/><path d="M -13 {-oh + 6} Q -15 {-oh - 24} 0 {-oh - 28}" stroke="#ffcf7a" stroke-width="4" fill="none" opacity=".7"/></g>')
    g.append("</g></g>")
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
