"""Render bukti kartu word-by-word Tahap C (fixture tata letak, tanpa API/rahasia)."""

from pathlib import Path
import sys

AKAR = Path(__file__).resolve().parents[1]
if str(AKAR) not in sys.path:
    sys.path.insert(0, str(AKAR))

from PIL import Image

from sutradara.gaya import dasar, kartu
from sutradara.render import png

KELUAR = AKAR / "keluaran-bukti/tahap-c"
TEMP = KELUAR / "sementara"

# Fixture ini menguji tata letak pasangan, bukan klaim verifikasi live atau pengganti teks sumber.
PASANGAN = [
    {"ar": "وَيَصْنَعُ", "id": "dan membuat"},
    {"ar": "الْفُلْكَ", "id": "kapal"},
    {"ar": "وَكُلَّمَا", "id": "dan setiap kali"},
    {"ar": "مَرَّ", "id": "lewat"},
    {"ar": "عَلَيْهِ", "id": "kepadanya"},
    {"ar": "مَلَأٌ", "id": "para pembesar"},
    {"ar": "مِنْ", "id": "dari"},
    {"ar": "قَوْمِهِ", "id": "kaumnya"},
    {"ar": "سَخِرُوا", "id": "mereka mengejek"},
    {"ar": "مِنْهُ", "id": "darinya"},
]


def main() -> None:
    KELUAR.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    dalil = {
        "jenis": "quran",
        "label": "CONTOH PEMETAAN KATA · QS HUD 38",
        "teks_ar": "وَيَصْنَعُ الْفُلْكَ وَكُلَّمَا مَرَّ عَلَيْهِ مَلَأٌ مِنْ قَوْمِهِ سَخِرُوا مِنْهُ",
        "terjemah": "Dan dia membuat kapal. Setiap kali para pemuka kaumnya berjalan melewatinya, mereka mengejeknya.",
        "pasangan_kata": PASANGAN,
    }
    potongan = kartu.potongan(dalil)
    if len(potongan) < 2:
        raise RuntimeError("Fixture harus menghasilkan setidaknya dua potongan untuk bukti pergantian kartu")
    waktu = kartu.rencana_waktu(potongan)
    latar = (
        '<defs><linearGradient id="latar-c" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#d8c7a4"/><stop offset="1" stop-color="#51443a"/>'
        '</linearGradient></defs>'
        '<rect width="1080" height="1920" fill="url(#latar-c)"/>'
        '<path d="M0 1450 Q260 1370 540 1450 T1080 1440 V1920 H0Z" fill="#40362f" opacity=".72"/>'
        '<text x="540" y="1120" text-anchor="middle" font-size="46" fill="#fffaf0" opacity=".9">KARTU DALIL · BUKTI TATA LETAK</text>'
        '<text x="540" y="1190" text-anchor="middle" font-size="30" fill="#fffaf0" opacity=".8">Pasangan kata tetap sepadan saat dipotong</text>'
    )
    lembar = Image.new("RGB", (1080, 960), "#171717")
    for indeks in range(2):
        awal, akhir = waktu[indeks]
        svg = dasar.dokumen(latar + kartu.kartu(dalil, potongan, akhir - 0.25, mulai=awal,
                                                idx_uid=f"tahapc{indeks}", preset="dhuha"))
        png(svg, TEMP / f"potongan-{indeks + 1}.png")
        with Image.open(TEMP / f"potongan-{indeks + 1}.png") as gambar:
            lembar.paste(gambar.convert("RGB").resize((540, 960)), (indeks * 540, 0))
    tujuan = KELUAR / "kartu-pasangan-kata.jpg"
    lembar.save(tujuan, format="JPEG", quality=92, optimize=True)
    print(f"Bukti tata letak dibuat: {tujuan.relative_to(AKAR)}")


if __name__ == "__main__":
    main()
