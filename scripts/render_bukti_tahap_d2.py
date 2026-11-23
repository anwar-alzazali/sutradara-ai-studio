"""Render bukti D2 untuk blocking, dialog/arah hadap, dan perjalanan."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Eksekusi `python scripts/...` menempatkan folder scripts di sys.path,
# bukan root repositori; tambahkan root agar paket lokal dapat diimpor.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sutradara import video
from sutradara.paket_genre.kisah_islami.sutradara import rancang
from sutradara.rencana import periksa

OUT = Path("keluaran-bukti/tahap-d2")


def main() -> None:
    naskah = {
        "judul": "Bahtera, seruan, dan perjalanan",
        "inti": "Kisah Nabi Nuh membangun bahtera dan menyeru kaumnya.",
        "dalil": [],
        "beat": [
            {
                "narasi": "Pengikut beriman membangun bahtera; kaum penentang berdiri di seberang.",
                "kata_kunci": ["membangun"], "dalil": [], "suasana": "senja",
                "peran": ["pengikut beriman", "kaum penentang"],
            },
            {
                "narasi": "Nabi Nuh menyeru seorang penentang, lalu penentang itu menjawab.",
                "kata_kunci": [], "dalil": [], "suasana": "senja",
                "peran": ["Nabi Nuh", "penentang"],
                "dialog": [
                    {"pembicara": "Nabi Nuh", "penjawab": "penentang",
                     "ucapan": "Dengarkan seruanku."}
                ],
            },
            {
                "narasi": "Seorang pengelana berjalan menuju tepi kanan.",
                "kata_kunci": ["berjalan"], "dalil": [], "suasana": "fajar",
                "peran": ["pengelana"],
            },
            {
                "narasi": "Pemberi mengulurkan surat kepada penerima.",
                "kata_kunci": [], "dalil": [], "suasana": "senja",
                "peran": ["Pemberi", "Penerima"],
            },
            {
                "narasi": "Pengelana menunjuk bahtera.",
                "kata_kunci": [], "dalil": [], "suasana": "senja",
                "peran": ["Pengelana"],
            },
            {
                "narasi": "Pengelana berjalan menuju bahtera.",
                "kata_kunci": ["berjalan"], "dalil": [], "suasana": "fajar",
                "peran": ["Pengelana"],
            },
            {
                "narasi": "Pengelana berjalan menjauh dari kamera.",
                "kata_kunci": ["berjalan"], "dalil": [], "suasana": "fajar",
                "peran": ["Pengelana"],
            },
            {
                "narasi": "Pengelana menghadap serong tiga perempat ke bahtera.",
                "kata_kunci": [], "dalil": [], "suasana": "senja",
                "peran": ["Pengelana"],
            },
            {
                "narasi": "Pengelana berbalik arah lalu kabur ke kiri.",
                "kata_kunci": ["berlari"], "dalil": [], "suasana": "senja",
                "peran": ["Pengelana"],
            },
            {
                "narasi": "Penjaga mengejar pengelana ke kanan.",
                "kata_kunci": ["berlari"], "dalil": [], "suasana": "senja",
                "peran": ["Penjaga", "Pengelana"],
            },
        ],
    }
    rencana, _ = rancang(naskah)
    # Metadata benda berasal dari fixture B2; posisi, orientasi, dan gestur
    # pemberi/penerima tetap ditentukan sutradara otomatis.
    beat_serah = next(b for b in rencana["beat"] if b["narasi"].startswith("Pemberi"))
    beat_serah["shot"][0]["barang"] = [{
        "id": "surat_bukti_d2", "jenis": "surat", "pemilik": "pemberi",
        "tangan": "ka", "aksi": "ulurkan", "penerima": "penerima",
        "tangan_pasangan": "ki", "titik_serah": [600, 1270],
    }]
    # Bukti D2 harus menguji posisi kelompok, pasangan interaksi, gestur,
    # tujuan benda, dan perjalanan ke kedalaman, bukan sekadar menghasilkan MP4.
    tokoh_serah = {t["peran"]: t for t in beat_serah["shot"][0]["tokoh"]}
    assert tokoh_serah["pemberi"]["arah"] == tokoh_serah["penerima"]["arah"] == "samping"
    assert tokoh_serah["pemberi"]["balik"] is False and tokoh_serah["penerima"]["balik"] is True
    assert tokoh_serah["pemberi"]["gerak"] == tokoh_serah["penerima"]["gerak"] == "ulurkan"
    beat_tunjuk = next(b for b in rencana["beat"] if b["narasi"].startswith("Pengelana menunjuk"))
    assert beat_tunjuk["shot"][0]["tokoh"][0]["gerak"] == "tunjuk"
    assert beat_tunjuk["shot"][0]["tokoh"][0]["arah"] == "samping"
    beat_benda = next(b for b in rencana["beat"] if b["narasi"].startswith("Pengelana berjalan menuju bahtera"))
    assert beat_benda["shot"][0]["tokoh"][0]["tujuan"] == "benda:bahtera"
    beat_kedalaman = next(b for b in rencana["beat"] if b["narasi"].startswith("Pengelana berjalan menjauh"))
    assert beat_kedalaman["shot"][0]["tokoh"][0]["arah"] == "belakang"
    beat_serong = next(b for b in rencana["beat"] if b["narasi"].startswith("Pengelana menghadap serong"))
    assert beat_serong["shot"][0]["tokoh"][0]["arah"] == "tiga_perempat"
    beat_putar = next(b for b in rencana["beat"] if b["narasi"].startswith("Pengelana berbalik arah"))
    aktor_putar = beat_putar["shot"][0]["tokoh"][0]
    assert aktor_putar["berbalik_sesuai_cerita"] is True
    assert isinstance(aktor_putar["arah"], list) and isinstance(aktor_putar["balik"], list)
    # Adegan pengejaran: kedua tokoh harus menempuh arah layar yang sama,
    # bukan saling mendekat atau bergerak saling berlawanan.
    beat_kejar = next(b for b in rencana["beat"] if b["narasi"].startswith("Penjaga mengejar"))
    aktor_kejar = {a["peran"]: a for a in beat_kejar["shot"][0]["tokoh"]}
    for pid in ("penjaga", "pengelana"):
        lintasan = aktor_kejar[pid]["lintasan"]
        assert lintasan[0][1] < lintasan[-1][1]
        assert aktor_kejar[pid]["tujuan"] == "tepi:kanan"
        assert aktor_kejar[pid]["gerak"] == "lari"
    temuan = periksa(rencana)
    gagal = [str(x) for x in temuan if x.tingkat == "GAGAL"]
    if gagal:
        raise SystemExit("Rencana bukti D2 gagal penjaga:\n" + "\n".join(gagal))
    OUT.mkdir(parents=True, exist_ok=True)
    berkas = OUT / "rencana-d2.json"
    berkas.write_text(json.dumps(rencana, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mp4 = OUT / "d2-blocking-dialog-perjalanan.mp4"
    video.buat(rencana, mp4, fps=12, workers=1)
    lembar = video.lembar(mp4, OUT / "lembar-kontak-d2.jpg", n=16, kolom=4)
    print("BUKTI_D2", berkas, mp4, lembar)


if __name__ == "__main__":
    main()
