"""Satu ketukan/langkah dipotong dari rekaman efek panjang -> aset/suara/satu/<nama>.mp3.

Kenapa: rekaman ElevenLabs (palu_kayu, langkah_*) berisi ketukan berulang dengan ritme SENDIRI (palu ±3,3 ketuk/dtk,
padahal ayunan tangan tokoh 1,4/dtk) dan panjangnya tetap 4 dtk. Agar suara mengikuti aksi di layar, yang dipakai
satu ketukan saja, diletakkan tepat di setiap titik kena gerak (gerak.titik_kena). Titik potong dicari dari selubung
energi (onset) rekaman asli: `python -m sutradara.suara.sampel` membuat ulang berkasnya.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
SUMBER, TUJUAN = AKAR / "aset/suara", AKAR / "aset/suara/satu"
# nama: (rekaman asal, mulai, panjang) — mulai = sedikit sebelum onset yang terdeteksi
SAMPEL = {"palu": ("palu_kayu", 0.13, 0.30), "langkah": ("langkah_pelan", 0.77, 0.32),
          "langkah_lari": ("langkah_lari", 0.27, 0.20), "gali": ("tanah_retak", 0.69, 0.40)}


def buat() -> list[Path]:
    ff = shutil.which("ffmpeg") or "ffmpeg"
    TUJUAN.mkdir(parents=True, exist_ok=True)
    out = []
    for nama, (asal, mulai, pjg) in SAMPEL.items():
        p = TUJUAN / f"{nama}.mp3"
        # puncak dinormalkan ke -3 dBFS supaya `vol` antar-sampel sebanding
        r = subprocess.run([ff, "-hide_banner", "-ss", str(mulai), "-t", str(pjg), "-i", str(SUMBER / f"{asal}.mp3"),
                            "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
        puncak = float(r.stderr.split("max_volume:")[1].split("dB")[0])
        subprocess.run([ff, "-v", "error", "-y", "-ss", str(mulai), "-t", str(pjg), "-i", str(SUMBER / f"{asal}.mp3"),
                        "-af", f"volume={-3 - puncak:.2f}dB,afade=t=in:d=0.005,afade=t=out:st={pjg - 0.06:.2f}:d=0.06",
                        "-ac", "2", "-ar", "44100", "-b:a", "128k", str(p)], check=True)
        out.append(p)
    return out


if __name__ == "__main__":
    for p in buat():
        print("ditulis", p)
