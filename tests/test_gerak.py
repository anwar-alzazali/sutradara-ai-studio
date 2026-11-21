import copy
import json
import subprocess
from pathlib import Path

from sutradara import adegan, kamera, video
from sutradara.waktu import adalah_kf, interp, pada

CONTOH = Path(__file__).resolve().parents[1] / "contoh"


def test_keyframe_halus_dan_ditahan_di_ujung():
    kf = [[0, 0.0], [2, 1.0]]
    assert interp(kf, -1) == 0.0 and interp(kf, 3) == 1.0
    assert interp(kf, 1) == 0.5
    assert 0 < interp(kf, 0.2) < 0.1  # ease-in: awal pelan


def test_peristiwa_bukan_keyframe_dan_daftar_angka_bukan_keyframe():
    sp = pada({"kamera": {"zoom": [[0, 1], [1, 2]], "guncang": [[0.5, 30]]}, "matahari": [860, 1060]}, 0.5)
    assert sp["kamera"]["zoom"] == 1.5
    assert sp["kamera"]["guncang"] == [[0.5, 30]]
    assert sp["matahari"] == [860, 1060] and not adalah_kf([860, 1060])


def test_kamera_hentak_dan_guncang():
    diam = kamera.transform({"zoom": 1.2, "x": 540, "y": 960}, 1.0)
    assert "scale(1.2000)" in diam
    assert "scale(1.2000)" not in kamera.transform({"zoom": 1.2, "hentak": [[0.95, 0.1]]}, 1.0)
    assert kamera.transform({"guncang": [[0.9, 40]]}, 1.0) != kamera.transform({}, 1.0)
    assert kamera.transform({"guncang": [[0.0, 40]]}, 2.0) == kamera.transform({}, 2.0)  # sudah meluruh


def test_shot_hidup_di_setiap_waktu():
    r = json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))
    s = r["beat"][0]["shot"][0]
    assert adegan.susun(s, 0.0) != adegan.susun(s, 1.0)  # kamera + gerak nur
    assert "MEMBUAT" not in adegan.susun(s, 0.1) and "MEMBUAT" in adegan.susun(s, 0.5)  # judul muncul di 0.3


def test_video_pendek(tmp_path):
    r = json.loads((CONTOH / "dabbah_dhuha.json").read_text(encoding="utf-8"))
    r = copy.deepcopy(r)
    for b in r["beat"]:
        for s in b["shot"]:
            s["durasi"] = 0.6
    mp4 = video.buat(r, tmp_path / "v.mp4", fps=5, kabar=lambda *_: None)
    keluaran = subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                        "stream=nb_read_frames,width,height", "-of", "json", str(mp4)])
    st = json.loads(keluaran)["streams"][0]
    assert (st["width"], st["height"]) == (1080, 1920)
    assert int(st["nb_read_frames"]) == 6
    jpg = video.lembar(mp4, tmp_path / "v.jpg", n=4, kolom=4)
    assert jpg.exists() and jpg.stat().st_size > 1000

def test_bahtera_nuh_semakin_jadi_di_setiap_shot_dan_tidak_tertutup_nur():
    r = json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))
    nilai_jadi = []
    for beat in r["beat"]:
        for shot in beat["shot"]:
            bahtera = next(b for b in shot.get("benda", []) if b.get("jenis") == "bahtera")
            jadi = bahtera["jadi"]
            nilai_jadi.extend([v for _, v in jadi] if isinstance(jadi, list) else [jadi])
            # Shot jauh tetap menampilkan siluet kapal yang cukup besar.
            assert bahtera.get("s", 1.0) >= 0.8
            # Pilar cahaya berada di sisi kiri dan sinarnya diarahkan menjauhi kapal.
            for nur in shot.get("nur", []):
                assert nur["x"] + 180 < bahtera["x"]
                assert nur.get("sinar_ke") == "kiri"
    assert all(a <= b for a, b in zip(nilai_jadi, nilai_jadi[1:])), nilai_jadi
