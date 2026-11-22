"""Antrean naskah dari bot: format, penjaga narasi, AI tiruan, verifikasi dalil (dataset tiruan), kartu status."""
import json
from pathlib import Path

import pytest

from sutradara import antrean as A

DATA = Path(__file__).parent / "data"
NASKAH = {"judul": "Uji", "inti": "x", "dalil": [{"id": "b1", "jenis": "hadis", "label": "HR. BUKHARI 1", "kitab": "bukhari", "nomor": "1"}],
          "beat": [{"narasi": "Kalimat pertama yang kuat.", "dalil": ["b1"], "suasana": "senja", "kata_kunci": ["kuat"], "peran": ["tokoh utama"]},
                   {"narasi": "Kalimat kedua.", "dalil": [], "suasana": "malam", "kata_kunci": [], "peran": []}]}


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


def test_validator_menjelaskan_kesalahan_kunci_format_beat():
    rusak = json.loads(json.dumps(NASKAH))
    del rusak["beat"][0]["peran"]
    rusak["beat"][1]["kata_kunci"] = "malam"
    rusak["beat"][1]["dalil"] = [{"bukan": "id"}]
    galat = " | ".join(A.validasi(rusak))
    assert "peran harus berupa daftar" in galat
    assert "kata_kunci harus berupa daftar" in galat
    assert "dalil harus berupa daftar id" in galat


def test_validator_menolak_id_dalil_ganda_dan_peran_tidak_teks():
    rusak = json.loads(json.dumps(NASKAH))
    rusak["dalil"].append(dict(rusak["dalil"][0]))
    rusak["beat"][0]["peran"] = [None]
    galat = " | ".join(A.validasi(rusak))
    assert "dipakai lebih dari sekali" in galat
    assert "peran harus berupa daftar" in galat


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


def test_tempel_narasi_diambil_apa_adanya_walau_ai_mengubah(tmp_path, monkeypatch):
    from sutradara.dalil import hadis as H
    monkeypatch.setattr(H, "DATA", DATA / "hadis")
    asal = "Judul: Uji Tempel\n\nKalimat pertama, mereka mengejeknya. (QS Hud 38)\n\nKalimat kedua.\n\nKalimat ketiga yang terlewat AI."
    d = _siapkan(tmp_path, "tempel", asal)
    peta = {"judul": "Judul karangan AI", "inti": "Uji pemetaan paragraf.", "dalil": [{"id": "hud38", "jenis": "quran", "label": "QS HUD 38", "surah": 11, "ayat": "38"}],
            "beat": [{"paragraf": [2], "dalil": [], "suasana": "malam", "kata_kunci": ["kedua"], "peran": []},
                     {"paragraf": [1], "dalil": ["hud38"], "suasana": "senja", "kata_kunci": ["ejekan"], "peran": ["Nabi Nuh"],
                      "narasi": "mereka mengejek Nuh (diubah AI, harus diabaikan)"}]}
    st = A.proses("u1", "tempel", folder=tmp_path, tanya=lambda *a, **k: (json.dumps(peta), 1), quran=QuranTiruan(), kirim_tg=False)
    n = json.loads((d / "naskah.json").read_text(encoding="utf-8"))
    assert n["judul"] == "Uji Tempel"
    assert [b["narasi"] for b in n["beat"]] == ["Kalimat pertama, mereka mengejeknya.", "Kalimat kedua.", "Kalimat ketiga yang terlewat AI."]
    assert n["beat"][0]["dalil"] == ["hud38"] and st["tahap"]["diterima"] == "selesai"


def test_tempel_mengurutkan_paragraf_berdasarkan_nomor_bukan_kecocokan_substring():
    asal = "Nabi Nuh pergi.\n\nNabi Nuh pergi ke laut."
    peta = {"judul": "Uji urutan", "inti": "Uji urutan paragraf.",
            "dalil": [], "beat": [
                {"paragraf": [2], "dalil": [], "kata_kunci": [], "peran": []},
                {"paragraf": [1], "dalil": [], "kata_kunci": [], "peran": []},
            ]}
    n, _ = A.buat_naskah("tempel", asal, tanya=lambda *a, **k: (json.dumps(peta), 1))
    assert [b["narasi"] for b in n["beat"]] == ["Nabi Nuh pergi.", "Nabi Nuh pergi ke laut."]


def test_paragraf_membuang_rujukan_dalam_kurung():
    assert A.paragraf("A (HR. Muslim 2934).\n\nB [QS 11:38]")[1] == ["A.", "B"]


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


def test_normalisasi_keluaran_ai_yang_wajar_salah():
    n = {"judul": "x", "inti": "Inti kisah.", "dalil": [{"id": "a", "jenis": "QS", "surah": "11", "ayat": "38 "},
                                 {"id": "b", "jenis": "Hadits", "kitab": "Sahih Muslim", "nomor": " 2934B"}],
         "beat": [{"narasi": "x", "dalil": ["a", "b"], "suasana": "Tegas, penuh ejekan",
                   "kata_kunci": ["x"], "peran": []}]}
    A.normalisasi(n)
    assert A.validasi(n) == []
    assert n["dalil"][0]["surah"] == 11 and n["dalil"][1]["kitab"] == "muslim" and n["dalil"][1]["nomor"] == "2934b"
    assert "suasana" not in n["beat"][0]


def test_terjemah_dalil_yang_sama_cukup_sekali():
    n = json.loads(json.dumps(NASKAH)); n["dalil"][0].update(status="terverifikasi", derajat="sahih", terjemah="TERJEMAH")
    n["beat"][1]["dalil"] = ["b1"]
    t = "".join(A.teks_tinjauan(n))
    assert t.count("TERJEMAH") == 1 and "(terjemah di atas)" in t


def test_pilih_model_gemini_flash_stabil_tertinggi():
    nama = ["models/gemini-2.5-flash", "models/gemini-3.8-flash", "models/gemini-3.8-flash-lite", "models/gemini-4.0-flash-preview",
            "models/gemini-3.8-flash-image", "models/gemini-3.5-flash", "models/gemma-4"]
    assert A.pilih_model_gemini(nama) == "gemini-3.8-flash"
    assert A.pilih_model_gemini(["models/gemma-4"]) is None


def test_tanpa_kunci_gemini_pindah_ke_claude(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(A, "tanya_claude", lambda *a, **k: ("{}", 7))
    A.PENYEDIA.clear()
    assert A.tanya_otomatis("s", "i", model="m") == ("{}", 7)
    assert A.PENYEDIA["terakhir"] == "Claude m" and "GEMINI_API_KEY" in A.PENYEDIA["catatan"]


def test_urutan_model_cadangan_lite():
    assert A.urutan_model_gemini(["models/gemini-3.8-flash", "models/gemini-3.8-flash-lite", "models/gemini-3.5-flash"]) == \
        ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.8-flash-lite"]


def test_rujukan_tidak_dikenal_dipertahankan_dan_menggagalkan_validasi():
    n = json.loads(json.dumps(NASKAH)); n["beat"][1]["dalil"] = ["b1", "hud53"]
    A.normalisasi(n)
    assert n["beat"][1]["dalil"] == ["b1", "hud53"]
    assert any("hud53" in galat for galat in A.validasi(n))
    assert "hud53" in n["peringatan"][0]


@pytest.mark.parametrize("peringatan", [None, "teks salah", 7, {}])
def test_normalisasi_tidak_gagal_jika_peringatan_bukan_daftar(peringatan):
    n = json.loads(json.dumps(NASKAH))
    n["beat"][1]["dalil"] = ["b1", "hud53"]
    n["peringatan"] = peringatan
    A.normalisasi(n)
    assert isinstance(n["peringatan"], list)
    assert "hud53" in n["peringatan"][0]
