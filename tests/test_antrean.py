"""Antrean naskah dari bot: format, penjaga narasi, AI tiruan, verifikasi dalil (dataset tiruan), kartu status."""
import json
from pathlib import Path

import pytest

from sutradara import antrean as A

DATA = Path(__file__).parent / "data"
NASKAH = {"judul": "Uji", "inti": "x", "dalil": [{"id": "b1", "jenis": "hadis", "label": "HR. BUKHARI 1", "kitab": "bukhari", "nomor": "1"}],
          "beat": [{"narasi": "Kalimat pertama yang kuat.", "dalil": ["b1"], "suasana": "senja", "kata_kunci": ["kuat"]},
                   {"narasi": "Kalimat kedua.", "dalil": [], "suasana": "malam"}]}


class QuranTiruan:
    def ayat(self, s, a):
        return None


def test_kartu_sama_dengan_fixture_bersama_bot():
    f = json.loads((DATA / "kartu_status.json").read_text(encoding="utf-8"))
    assert A.kartu(f["status"]) == f["teks"]


def test_validasi_menangkap_kesalahan_format():
    assert A.validasi(NASKAH) == []
    rusak = json.loads(json.dumps(NASKAH))
    rusak["beat"][0]["narasi"] = "Allah berfirman قَالَ"
    rusak["beat"][1]["dalil"] = ["tidakada"]
    rusak["dalil"].append({"id": "q", "jenis": "quran", "label": "QS", "surah": 200, "ayat": "1"})
    rusak["dalil"].append({"id": "a", "jenis": "hadis", "label": "HR AHMAD", "kitab": "ahmad", "nomor": "1"})
    g = " | ".join(A.validasi(rusak))
    for kata in ("huruf Arab", "tidakada", "surah/ayat", "ahmad"):
        assert kata in g


def test_narasi_tempelan_tidak_boleh_diubah_ai():
    asal = "Kalimat pertama yang kuat.\n\nKalimat kedua."
    assert A.narasi_utuh(NASKAH, asal) == []
    ubah = json.loads(json.dumps(NASKAH)); ubah["beat"][1]["narasi"] = "Kalimat kedua yang diperindah AI."
    assert A.narasi_utuh(ubah, asal)


def _siapkan(tmp_path, mode, masukan):
    d = tmp_path / "u1"; d.mkdir()
    (d / "status.json").write_text(json.dumps(A.status_baru("u1", "", mode)), encoding="utf-8")
    (d / ("catatan.txt" if mode == "revisi" else "masukan.txt")).write_text(masukan, encoding="utf-8")
    return d


def test_proses_ide_lengkap_dengan_ai_dan_dataset_tiruan(tmp_path, monkeypatch):
    from sutradara.dalil import hadis as H
    monkeypatch.setattr(H, "DATA", DATA / "hadis")
    d = _siapkan(tmp_path, "ide", "kisah uji")
    st = A.proses("u1", "ide", folder=tmp_path, tanya=lambda *a, **k: (json.dumps(NASKAH), 123), quran=QuranTiruan(), kirim_tg=False)
    assert st["tahap"]["diterima"] == "selesai" and st["tahap"]["tinjau"] == "jalan"
    assert st["tahap"]["dalil"] in ("selesai", "gagal")
    n = json.loads((d / "naskah.json").read_text(encoding="utf-8"))
    assert n["dalil"][0].get("status") in ("terverifikasi", "belum")
    assert st["token_ai"] == 123


def test_proses_tempel_menolak_narasi_yang_diubah(tmp_path):
    _siapkan(tmp_path, "tempel", "Kalimat pertama yang kuat.")
    st = A.proses("u1", "tempel", folder=tmp_path, tanya=lambda *a, **k: (json.dumps(NASKAH), 1), quran=QuranTiruan(), kirim_tg=False)
    assert st["tahap"]["diterima"] == "gagal" and "tidak sama" in st["ket"]["diterima"]


def test_proses_ai_gagal_dilaporkan_bukan_meledak(tmp_path):
    _siapkan(tmp_path, "ide", "x")
    def gagal(*a, **k):
        raise RuntimeError("ANTHROPIC_API_KEY belum diisi")
    st = A.proses("u1", "ide", folder=tmp_path, tanya=gagal, quran=QuranTiruan(), kirim_tg=False)
    assert st["tahap"]["diterima"] == "gagal" and "ANTHROPIC" in st["ket"]["diterima"]


def test_teks_tinjauan_memuat_tanda_dalil_dan_muat_telegram():
    n = json.loads(json.dumps(NASKAH)); n["dalil"][0].update(status="terverifikasi", derajat="sahih", terjemah="t" * 500)
    t = A.teks_tinjauan(n)
    assert all(len(x) <= 4096 for x in t) and "✅ HR. BUKHARI 1 (sahih)" in "".join(t)
