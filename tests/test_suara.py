"""Fase 2: narasi (dengan TTS tiruan, tanpa kredit), garis waktu, subtitle, dan campur suara."""
import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from sutradara import garis_waktu as GW
from sutradara.suara import campur, narasi

AKAR = Path(__file__).resolve().parents[1]
NUH = json.loads((AKAR / "contoh/nuh_mengejek.json").read_text(encoding="utf-8"))


def tts_tiruan(teks, s, *, per_huruf=0.055, jeda_beat=0.45):
    """Penjajaran huruf buatan + audio nada (bukan suara manusia) sepanjang narasi."""
    ch, a, b, t = [], [], [], 0.0
    for c in teks:
        d = jeda_beat if c == "\n" else per_huruf
        ch.append(c); a.append(t); b.append(t + d); t += d
    mp3 = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"sine=f=220:d={t + 0.3:.2f}", "-ac", "1",
                          "-f", "mp3", "-"], capture_output=True, check=True).stdout
    return mp3, {"characters": ch, "character_start_times_seconds": a, "character_end_times_seconds": b}


@pytest.fixture
def narasi_nuh(tmp_path):
    js = narasi.buat(NUH, folder=tmp_path, kirim=tts_tiruan)
    return tmp_path, json.loads(js.read_text(encoding="utf-8"))


def test_kata_dari_huruf_lewati_tag():
    al = {"characters": list("[sedih] Halo dunia"), "character_start_times_seconds": [i * .1 for i in range(18)],
          "character_end_times_seconds": [i * .1 + .1 for i in range(18)]}
    assert [k["teks"] for k in narasi.kata_dari_huruf(al)] == ["Halo", "dunia"]


def test_lafal_dikembalikan_ke_tulisan_asli():
    teks, balik = narasi.terapkan_lafal("Kisah Nuh a.s. hari ini", {"Nuh": "Nuhh"})
    assert "Nuhh" in teks
    kata = [{"teks": "Nuhh,", "t0": 0, "t1": 1}]
    narasi._kembalikan_tulisan(kata, balik)
    assert kata[0]["teks"] == "Nuh,"


def test_arab_ditolak_sebelum_dikirim(tmp_path):
    r = copy.deepcopy(NUH); r["beat"][0]["narasi"] = "Allah berfirman: قَالَ"
    with pytest.raises(ValueError):
        narasi.buat(r, folder=tmp_path, kirim=lambda *a: pytest.fail("tidak boleh terkirim"))


def test_cache_tidak_membayar_dua_kali(narasi_nuh):
    folder, _ = narasi_nuh
    narasi.buat(NUH, folder=folder, kirim=lambda *a: pytest.fail("cache seharusnya dipakai"))


def test_sidik_berubah_bila_naskah_berubah():
    r = copy.deepcopy(NUH); r["beat"][0]["narasi"] += " Lagi."
    assert narasi.sidik(r) != narasi.sidik(NUH)


def test_garis_waktu_nuh(narasi_nuh):
    _, n = narasi_nuh
    g = GW.susun(NUH, n)
    assert len(g.shot) == sum(len(b["shot"]) for b in NUH["beat"])
    assert abs(sum(s["durasi"] for s in g.shot) - g.total) < 1e-6
    # potongan beat 2 jatuh tepat sebelum "mengejeknya"
    kunci = next(k for k in g.kata if k["teks"].startswith("mengejek"))
    assert abs(g.potong[2] - (kunci["t0"] - GW.POTONG_SEBELUM)) < 1e-6
    # kartu dalil = sisipan sesudah narasi beat 3: tidak ada kata yang diucapkan selama kartu
    t_kartu = g.potong[-1]
    assert all(k["t1"] <= t_kartu + 0.01 for k in g.kata)
    assert g.shot[-1]["durasi"] >= 5
    # subtitle tulisan tangan dibuang, digantikan waktu kata
    assert all("subtitle" not in (s.get("teks") or {}) for s in g.shot)
    kata, aktif = g.subtitle_pada(g.kata[3]["t0"] + 0.01)
    assert kata[aktif] == g.kata[3]["teks"]


def test_skala_waktu_koreografi():
    s = {"durasi": 4, "kamera": {"zoom": [[0, 1], [4, 1.2]], "hentak": [[2, .05]]}, "tokoh": [{"gerak": [[0, "jalan"], [2, "tunjuk"]]}],
         "teks": {"judul_mulai": 1.0}, "matahari": [860, 1060]}
    b = GW.skala_waktu(s, 2.0)
    assert b["kamera"]["zoom"] == [[0, 1], [8, 1.2]] and b["kamera"]["hentak"] == [[4, .05]]
    assert b["tokoh"][0]["gerak"] == [[0, "jalan"], [4, "tunjuk"]] and b["teks"]["judul_mulai"] == 2.0
    assert b["matahari"] == [860, 1060]


def test_periksa_naskah_menangkap_kata_potong_salah():
    r = copy.deepcopy(NUH); r["beat"][1]["potong_di"] = ["menertawakan"]
    assert GW.periksa_naskah(r) and not GW.periksa_naskah(NUH)


def test_rancang_efek(narasi_nuh):
    _, n = narasi_nuh
    g = GW.susun(NUH, n)
    r = copy.deepcopy(NUH); r["beat"][0]["efek"] = [{"berkas": "palu_kayu", "kata": "kapal", "vol": 0.6}]
    rek = campur.rancang(r, g)
    nama = [x["berkas"] for x in rek]
    assert "palu_kayu" in nama and "kilau_cahaya" in nama and nama.count("whoosh") == len(NUH["beat"]) - 1
    palu = next(x for x in rek if x["berkas"] == "palu_kayu")
    assert abs(palu["at"] - next(k["t0"] for k in g.kata if k["teks"] == "kapal")) < 1e-6


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="butuh ffmpeg")
def test_campur_menghasilkan_audio_dan_kenyaringan(narasi_nuh, tmp_path):
    folder, n = narasi_nuh
    g = GW.susun(NUH, n)
    bisu = tmp_path / "bisu.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s=108x192:d={g.total:.2f}:r=10",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bisu)], check=True)
    mp3, _ = narasi.jalur(NUH, folder)
    out = campur.campur(bisu, mp3, g, campur.rancang(NUH, g), tmp_path / "jadi.mp4")
    u = campur.ukur(out)
    assert -17.5 < u["lufs"] < -12.5 and u["puncak_dbtp"] <= -0.5
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(out)]))
    assert {s["codec_type"] for s in info["streams"]} == {"video", "audio"}


def test_titik_kena_palu_sinkron_dengan_ayunan():
    from sutradara import gerak as GR
    for tc in GR.titik_kena("palu", 0, 3):
        u = GR.palu(tc)  # saat kena: lengan atas paling turun (u=0 -> la_ka = 40)
        assert abs(u["la_ka"] - 40) < 0.5
    assert len(GR.titik_kena("jalan", 0, 2)) == 4 and GR.titik_kena("berdiri", 0, 2) == []


def test_efek_aksi_mengikuti_jadwal_gerak():
    shot = {"durasi": 4.0, "tokoh": [{"x": 900, "s": 1.0, "gerak": [[0, "berdiri"], [2, "palu"]]}]}
    rek = campur.efek_aksi(shot, 10.0)
    assert rek and all(12.0 <= r["at"] < 14.0 for r in rek)   # hanya selama memalu, di waktu video
    assert all(r["berkas"] == "satu/palu" and r["pan"] > 0 for r in rek)  # tokoh di kanan -> suara di kanan


def test_bahtera_dibangun_berbunyi_hanya_saat_bertambah():
    shot = {"durasi": 6.0, "benda": [{"jenis": "bahtera", "x": 600, "s": 0.5, "jadi": [[0, 0.1], [3, 0.6], [6, 0.6]]}]}
    rek = campur.efek_aksi(shot, 0.0)
    assert rek and max(r["at"] for r in rek) < 3.0


def test_efek_bebas_berhenti_di_akhir_shot_kecuali_lewat(narasi_nuh):
    _, n = narasi_nuh
    g = GW.susun(NUH, n)
    r = copy.deepcopy(NUH)
    r["beat"][0]["efek"] = [{"berkas": "palu_kayu", "kata": "kapal"}, {"berkas": "guntur_hujan", "kata": "kapal", "lewat": True}]
    rek = campur.rancang(r, g)
    palu = next(x for x in rek if x["berkas"] == "palu_kayu")
    assert abs(palu["at"] + palu["sampai"] - g.potong[1]) < 1e-3
    assert "sampai" not in next(x for x in rek if x["berkas"] == "guntur_hujan")
