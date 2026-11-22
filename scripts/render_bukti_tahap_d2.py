"""Render bukti D2 untuk blocking, dialog/arah hadap, dan perjalanan."""
from __future__ import annotations

import json
from pathlib import Path

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
        ],
    }
    rencana, _ = rancang(naskah)
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
