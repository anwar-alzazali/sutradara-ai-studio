"""Render bukti audiovisual Nuh secara eksplisit; tidak dijalankan oleh pytest biasa."""
import json
import subprocess
from pathlib import Path

from sutradara import garis_waktu as GW, video
from sutradara.suara import campur, narasi

AKAR = Path(__file__).resolve().parents[1]
NUH = json.loads((AKAR / "contoh/nuh_mengejek.json").read_text(encoding="utf-8"))


def tts_tiruan(teks, s, *, per_huruf=0.055, jeda_beat=0.45):
    """Audio nada untuk bukti sinkronisasi; bukan suara manusia."""
    karakter, mulai, akhir, t = [], [], [], 0.0
    for c in teks:
        d = jeda_beat if c == "\n" else per_huruf
        karakter.append(c)
        mulai.append(t)
        akhir.append(t + d)
        t += d
    mp3 = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"sine=f=220:d={t + 0.3:.2f}",
         "-ac", "1", "-f", "mp3", "-"],
        capture_output=True, check=True,
    ).stdout
    return mp3, {
        "characters": karakter,
        "character_start_times_seconds": mulai,
        "character_end_times_seconds": akhir,
    }


def main():
    bukti = Path("keluaran-bukti/nuh")
    bukti.mkdir(parents=True, exist_ok=True)
    folder_narasi = bukti / "narasi"
    folder_narasi.mkdir(parents=True, exist_ok=True)
    js = narasi.buat(NUH, folder=folder_narasi, kirim=tts_tiruan)
    n = json.loads(js.read_text(encoding="utf-8"))
    garis = GW.susun(NUH, n)
    efek = campur.rancang(NUH, garis)
    assert any("palu" in x.get("sebab", "") and x["berkas"] == "satu/palu" for x in efek)
    bisu = video.buat(NUH, bukti / "nuh_bisu.mp4", fps=12, garis=garis, kabar=lambda *_: None)
    mp3, _ = narasi.jalur(NUH, folder_narasi)
    hasil = campur.campur(bisu, mp3, garis, efek, bukti / "nuh_bersuara.mp4")
    kontak = video.lembar(hasil, bukti / "nuh_kontak.jpg", n=12, kolom=4)
    ukur = campur.ukur(hasil)
    assert -17.5 < ukur["lufs"] < -12.5, ukur
    assert ukur["puncak_dbtp"] <= -1.0, ukur
    assert hasil.is_file() and kontak.is_file()
    print(json.dumps({"durasi": garis.total, "lufs": ukur["lufs"],
                      "puncak_dbtp": ukur["puncak_dbtp"],
                      "video": str(hasil), "lembar_kontak": str(kontak)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
