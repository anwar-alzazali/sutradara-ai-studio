"""Pustaka aset pemeran prosedural: karakter induk pria dewasa.

Jalankan dari akar repo:
    python -m sutradara.pustaka_tokoh --keluar keluaran/pustaka_tokoh

Semua variasi memakai satu kartu identitas dan satu rangka TK.orang. Modul ini
menyimpan SVG individual per kombinasi pose/sudut serta lembar kontak PNG.
Tidak memakai layanan gambar atau API berbayar.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import gerak as G
from .gaya import dasar, tokoh
from .render import peramban, png


# Identitas dikunci agar perubahan pose/sudut tidak mengubah pemeran.
PEMERAN = {
    "id": "pria_dewasa_01",
    "jenis": "pria",
    "usia": "dewasa",
    "zaman": "arab_kuno",
    "kepala": "imamah",
    "wajah": "datar",
    "warna_kulit": "#b97a52",
    "warna_baju": "#3f5a6b",
    "warna_aksen": "#d9b26a",
    "rambut": "#2a1b14",
    "janggut": "pendek",
    "warna_janggut": "#2a1b14",
}

# Sudut positif berputar dari depan ke samping lalu belakang. Sisi kanan
# memakai pencerminan horizontal agar identitas tetap satu dan tidak diduplikasi.
SUDUT = (
    ("depan", "depan", False),
    ("tiga_perempat_kiri", [(0.0, "depan"), (1.0, "samping")], False),
    ("samping_kiri", "samping", False),
    ("tiga_perempat_belakang_kiri", [(0.0, "samping"), (1.0, "belakang")], False),
    ("belakang", "belakang", False),
    ("tiga_perempat_belakang_kanan", [(0.0, "samping"), (1.0, "belakang")], True),
    ("samping_kanan", "samping", True),
    ("tiga_perempat_kanan", [(0.0, "depan"), (1.0, "samping")], True),
)

POSE = (
    "berdiri", "jalan", "lari", "duduk",
    "melambai", "berdoa", "tunjuk", "silang",
    "kaget", "mundur", "menengadah", "lemas",
)

WAKTU_POSE = {
    "jalan": 0.25,
    "lari": 0.18,
    "melambai": 0.25,
    "duduk": 0.2,
}


def _tokoh(x: float, y: float, skala: float, pose: str, arah, balik: bool, t: float) -> str:
    return tokoh.orang(
        x, y, skala, gerak=pose, t=t, indeks=0,
        mode="pakaian", kepala=PEMERAN["kepala"], jenis=PEMERAN["jenis"],
        wajah=PEMERAN["wajah"], arah=arah, balik=balik,
        usia=PEMERAN["usia"], zaman=PEMERAN["zaman"],
        warna_kulit=PEMERAN["warna_kulit"],
        warna_baju=PEMERAN["warna_baju"],
        warna_aksen=PEMERAN["warna_aksen"],
        rambut=PEMERAN["rambut"], janggut=PEMERAN["janggut"],
        warna_janggut=PEMERAN["warna_janggut"],
    )


def svg_individu(pose: str, nama_sudut: str) -> str:
    """Satu aset SVG penuh; koordinat dan identitas sama untuk seluruh variasi."""
    sudut = next((v for v in SUDUT if v[0] == nama_sudut), None)
    if sudut is None:
        raise ValueError(f"sudut tidak dikenal: {nama_sudut}")
    t = WAKTU_POSE.get(pose, 0.5)
    isi = (
        '<rect width="1080" height="1920" fill="#eee7d9"/>'
        '<path d="M0 1540 H1080" stroke="#d0c4b0" stroke-width="3"/>'
        + _tokoh(540, 1510, 1.65, pose, sudut[1], sudut[2], t)
    )
    return dasar.dokumen(isi)


def svg_lembar(pose: str) -> str:
    """Lembar delapan sudut dalam satu pose untuk pemeriksaan konsistensi."""
    kolom, baris = 4, 2
    lebar, tinggi = dasar.LEBAR // kolom, 900
    isi = ['<rect width="1080" height="1920" fill="#eee7d9"/>',
           '<text x="540" y="68" text-anchor="middle" font-size="34" '
           'font-weight="800" fill="#26323a">PRIA DEWASA 01 · ' + pose.upper() + '</text>']
    t = WAKTU_POSE.get(pose, 0.5)
    for i, (nama, arah, balik) in enumerate(SUDUT):
        x0, y0 = (i % kolom) * lebar, 120 + (i // kolom) * tinggi
        isi.append(f'<rect x="{x0 + 5}" y="{y0}" width="{lebar - 10}" height="{tinggi - 14}" '
                   'rx="18" fill="#f8f4ec" stroke="#d5caba" stroke-width="2"/>')
        isi.append(f'<g transform="translate({x0 + lebar / 2:.1f},{y0 + 690:.1f}) scale(.66) translate(-540,-1510)">'
                   + _tokoh(540, 1510, 1.0, pose, arah, balik, t) + '</g>')
        label = nama.replace("_", " ").upper()
        isi.append(f'<text x="{x0 + lebar / 2:.1f}" y="{y0 + 770}" text-anchor="middle" '
                   'font-size="17" font-weight="700" fill="#26323a">' + label + '</text>')
    return dasar.dokumen("\\n".join(isi))


def buat_pustaka(keluar: Path, *, buat_png_individu: bool = False) -> list[Path]:
    """Tulis 96 SVG aset, 12 lembar kontak SVG+PNG, opsional 96 PNG individual."""
    keluar = Path(keluar)
    folder_svg = keluar / "svg"
    folder_png = keluar / "png"
    folder_lembar = keluar / "lembar"
    for folder in (folder_svg, folder_png, folder_lembar):
        folder.mkdir(parents=True, exist_ok=True)

    hasil: list[Path] = []
    with peramban() as halaman:
        for pose in POSE:
            for nama_sudut, _, _ in SUDUT:
                jalur_svg = folder_svg / f"{pose}__{nama_sudut}.svg"
                jalur_svg.write_text(svg_individu(pose, nama_sudut), encoding="utf-8")
                hasil.append(jalur_svg)
                if buat_png_individu:
                    hasil.append(png(svg_individu(pose, nama_sudut),
                                     folder_png / f"{pose}__{nama_sudut}.png", halaman=halaman))
            lembar = svg_lembar(pose)
            (folder_lembar / f"{pose}.svg").write_text(lembar, encoding="utf-8")
            hasil.append(png(lembar, folder_lembar / f"{pose}.png", halaman=halaman))
    return hasil


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render pustaka aset tokoh prosedural")
    ap.add_argument("--keluar", type=Path, default=Path("keluaran/pustaka_tokoh/pria_dewasa_01"))
    ap.add_argument("--png-individu", action="store_true",
                    help="tambahkan PNG penuh untuk setiap kombinasi pose dan sudut")
    args = ap.parse_args(argv)
    hasil = buat_pustaka(args.keluar, buat_png_individu=args.png_individu)
    print(f"selesai: {len(hasil)} berkas di {args.keluar}")
    print(f"karakter: {PEMERAN['id']} | {len(POSE)} pose | {len(SUDUT)} sudut")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
