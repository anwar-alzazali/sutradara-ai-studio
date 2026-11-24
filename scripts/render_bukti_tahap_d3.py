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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for nama in SUMBER:
        buat_bukti(nama)


if __name__ == "__main__":
    main()
