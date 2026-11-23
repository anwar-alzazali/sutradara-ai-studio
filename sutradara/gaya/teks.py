"""Teks layar (resep C): judul 1-3 kata kapital, warna punya arti, sumber dalil kecil di atas, subtitle di bawah."""
from __future__ import annotations

from html import escape

from .dasar import KUNING, MERAH, PUTIH

WARNA = {"kuning": KUNING, "putih": PUTIH, "merah": MERAH}


def sumber(teks: str, y: float = 170) -> str:
    w = len(teks) * 17 + 60
    return (f'<rect x="{540 - w / 2}" y="{y - 20}" width="{w}" height="54" rx="27" fill="#1a1426" stroke="{KUNING}" stroke-width="2.5" opacity=".92"/>'
            f'<text x="540" y="{y + 17}" text-anchor="middle" font-size="27" font-weight="800" fill="{KUNING}">{escape(teks)}</text>')


def judul(baris: list[str], *, warna: str = "putih", y0: float = 330, ukuran: int = 112) -> str:
    panjang = max(len(b) for b in baris)
    ukuran = int(min(ukuran, 960 / (0.62 * max(panjang, 1))))  # jangan melebihi lebar layar
    c = WARNA.get(warna, warna)
    return "".join(f'<text x="540" y="{y0 + i * (ukuran + 6)}" text-anchor="middle" font-size="{ukuran}" font-weight="900" '
                   f'fill="{c}" stroke="#1a1426" stroke-width="10" paint-order="stroke">{escape(b)}</text>' for i, b in enumerate(baris))


def subtitle(teks: str, *, sorot: str | None = None, y: float = 1720) -> str:
    """Satu baris subtitle; kata `sorot` diberi warna kuning."""
    isi = escape(teks)
    if sorot and sorot in teks:
        a, b = teks.split(sorot, 1)
        isi = f'{escape(a)}<tspan fill="{KUNING}">{escape(sorot)}</tspan>{escape(b)}'
    return (f'<text x="540" y="{y}" text-anchor="middle" font-size="60" font-weight="800" fill="#fff" stroke="#000" '
            f'stroke-width="8" paint-order="stroke">{isi}</text>')


def _ukur_baris(kata: list[str], ukuran: float) -> float:
    return sum(len(w) for w in kata) * ukuran * 0.56 + max(0, len(kata) - 1) * ukuran * 0.28


def _bungkus_subtitle(kata: list[str], ukuran: float, lebar: float) -> list[list[int]]:
    """Bungkus kata secara greedy tanpa memotong kata; hasil maksimal tiga baris."""
    baris: list[list[int]] = []
    aktif: list[int] = []
    for i, kata_i in enumerate(kata):
        calon = aktif + [i]
        if aktif and _ukur_baris([kata[j] for j in calon], ukuran) > lebar:
            baris.append(aktif)
            aktif = [i]
        else:
            aktif = calon
    if aktif:
        baris.append(aktif)
    return baris


def subtitle_frasa(kata: list[str], aktif: int | None = None, *, y: float = 1720, uk: float = 60, lebar: float = 900) -> str:
    """Subtitle aman layar: bungkus otomatis sampai 3 baris, lalu kecilkan font bila perlu."""
    if not kata:
        return ""
    u = float(uk)
    baris = _bungkus_subtitle(kata, u, lebar)
    while (len(baris) > 3 or max(_ukur_baris([kata[j] for j in b], u) for b in baris) > lebar) and u > 24:
        u -= 2
        baris = _bungkus_subtitle(kata, u, lebar)
    # Pusatkan blok teks terhadap baseline acuan agar jarak aman atas/bawah konsisten.
    jarak = u * 1.12
    y0 = y - (len(baris) - 1) * jarak / 2
    out = []
    for n, b in enumerate(baris):
        isi = " ".join((f'<tspan fill="{KUNING}">{escape(kata[j])}</tspan>' if j == aktif else escape(kata[j])) for j in b)
        out.append(f'<text x="540" y="{y0 + n * jarak:.1f}" text-anchor="middle" font-size="{u:.1f}" font-weight="800" fill="#fff" '
                   f'stroke="#000" stroke-width="{u * 0.13:.1f}" paint-order="stroke">{isi}</text>')
    return "".join(out)
