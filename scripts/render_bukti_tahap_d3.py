"""Bukti render D3: reduksi peristiwa tetap terbawa ke rencana dan video."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sutradara import video
from sutradara.paket_genre.kisah_islami.sutradara import rancang
from sutradara.rencana import periksa

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "keluaran-bukti" / "tahap-d3"
SUMBER = ("nuh.json", "hud.json")


def buat_bukti(nama: str) -> None:
    naskah = json.loads((ROOT / "naskah" / nama).read_text(encoding="utf-8"))
    rencana, _ = rancang(naskah)

    assert rencana.get("genre") == "kisah_islami"
    assert len(rencana.get("beat", [])) == len(naskah.get("beat", []))

    jumlah_peristiwa = 0
    for indeks, beat in enumerate(rencana["beat"]):
        peristiwa = beat.get("peristiwa", [])
        jumlah_peristiwa += len(peristiwa)
        # Snapshot peristiwa yang dipakai sutradara harus tetap tersedia
        # pada setiap shot beat; renderer tidak boleh kehilangan jejaknya.
        for shot in beat.get("shot", []):
            assert shot.get("peristiwa_visual", []) == peristiwa, (
                f"{nama}: peristiwa beat {indeks} tidak terbawa ke shot"
            )

    if jumlah_peristiwa == 0:
        raise AssertionError(f"{nama}: parser tidak menghasilkan peristiwa D3")

    temuan = periksa(rencana)
    gagal = [str(x) for x in temuan if x.tingkat == "GAGAL"]
    if gagal:
        raise SystemExit(f"{nama}: rencana gagal pemeriksaan:\n" + "\n".join(gagal))

    nama_dasar = Path(nama).stem
    berkas = OUT / f"rencana-{nama_dasar}.json"
    mp4 = OUT / f"d3-{nama_dasar}.mp4"
    lembar = OUT / f"lembar-kontak-{nama_dasar}.jpg"
    berkas.write_text(
        json.dumps(rencana, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    video.buat(rencana, mp4, fps=12, workers=1)
    video.lembar(mp4, lembar, n=16, kolom=4)
    print(f"BUKTI_D3 {nama}: {jumlah_peristiwa} peristiwa; {berkas}; {mp4}; {lembar}")



def buat_bukti_dinding() -> None:
    # Fixture sintetis untuk menguji kontrak transisi benda, bukan klaim
    # bahwa fixture ini merupakan naskah atau riwayat kisah yang tervalidasi.
    naskah = {
        "judul": "Uji transisi dinding",
        "inti": "Uji visual dinding Ya'juj: utuh, digali, lalu terbuka.",
        "dalil": [],
        "beat": [
            {
                "narasi": "Dinding berdiri utuh menutup celah di antara dua bukit.",
                "kata_kunci": [],
                "dalil": [],
                "suasana": "senja",
                "peran": ["Kaum penggali"],
            },
            {
                "narasi": "Kaum penggali menggali dinding dengan alat mereka.",
                "kata_kunci": ["menggali"],
                "dalil": [],
                "suasana": "senja",
                "peran": ["Kaum penggali"],
            },
            {
                "narasi": "Dinding terbuka setelah penggalian selesai.",
                "kata_kunci": ["terbuka"],
                "dalil": [],
                "suasana": "fajar",
                "peran": ["Kaum penggali"],
            },
        ],
    }
    rencana, _ = rancang(naskah)
    status = [beat["keadaan"] for beat in rencana["beat"]]
    assert status == ["utuh", "dilubangi", "terbuka"], (
        f"Transisi dinding tidak sesuai peristiwa eksplisit: {status}"
    )
    assert rencana["beat"][1]["peristiwa"]
    assert rencana["beat"][2]["peristiwa"]
    for indeks, beat in enumerate(rencana["beat"]):
        for shot in beat.get("shot", []):
            assert shot.get("peristiwa_visual", []) == beat.get("peristiwa", []), (
                f"Fixture dinding: peristiwa beat {indeks} tidak terbawa ke shot"
            )

    temuan = periksa(rencana)
    gagal = [str(x) for x in temuan if x.tingkat == "GAGAL"]
    if gagal:
        raise SystemExit("Fixture dinding gagal pemeriksaan:\n" + "\n".join(gagal))

    berkas = OUT / "rencana-dinding-yajuj-fixture.json"
    mp4 = OUT / "d3-dinding-yajuj-fixture.mp4"
    lembar = OUT / "lembar-kontak-dinding-yajuj-fixture.jpg"
    berkas.write_text(
        json.dumps(rencana, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    video.buat(rencana, mp4, fps=12, workers=1)
    video.lembar(mp4, lembar, n=16, kolom=4)
    print(f"BUKTI_D3 dinding fixture: {status}; {berkas}; {mp4}; {lembar}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for nama in SUMBER:
        buat_bukti(nama)
    buat_bukti_dinding()


if __name__ == "__main__":
    main()
