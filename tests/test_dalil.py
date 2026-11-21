import json
from pathlib import Path

import pytest

from sutradara.dalil import hadis as H
from sutradara.dalil.quran import QuranFoundation
from sutradara.dalil.verifikasi import verifikasi
from sutradara.rencana import periksa

FIX = Path(__file__).parent / "data/hadis"
DAIF = (FIX / "DAIF.txt").read_text().strip()
CONTOH = Path(__file__).resolve().parents[1] / "contoh"


@pytest.fixture(autouse=True)
def dataset_uji(monkeypatch):
    monkeypatch.setattr(H, "DATA", FIX)
    H._muat.cache_clear()
    yield
    H._muat.cache_clear()


def kode(t, tingkat="GAGAL"):
    return {x.kode for x in t if x.tingkat == tingkat}


def test_penomoran_sunnah_com_termasuk_riwayat_berhuruf():
    semua = H.cari("muslim", "2934")
    assert len(semua) >= 2 and {h.sub for h in semua} >= {"a", "b"}
    b = H.cari("muslim", "2934b")
    assert len(b) == 1 and "Dajjal" in b[0].en
    assert "one eyed" in H.cari("bukhari", 7123)[0].en and H.cari("bukhari", 7123)[0].tautan == "https://sunnah.com/bukhari:7123"


def test_derajat():
    assert H.derajat("bukhari", [])[0] == "sahih"
    drj, beda = H.derajat("ibnmajah", H.cari("ibnmajah", "4080")[0].penilaian)
    assert drj == "sahih" and any("Zubair" in n for n in beda)  # Al-Albani sahih, Zubair Ali Zai daif -> diterima + dicatat
    assert H.derajat("abudawud", H.cari("abudawud", DAIF)[0].penilaian)[0] == "daif"
    assert H.derajat("abudawud", [{"name": "X", "grade": "Hasan"}, {"name": "Y", "grade": "Da'if"}])[0] == "daif"  # seri -> tolak


def _rencana(dalil):
    r = json.loads((CONTOH / "dajjal_dua_sungai.json").read_text(encoding="utf-8"))
    r["dalil"] = dalil
    for b in r["beat"]:
        b["dalil"] = [d["id"] for d in dalil][:1]
    return r


def test_verifikasi_hadis_sahih_lulus_final():
    r, lap = verifikasi(_rencana([{"id": "a", "jenis": "hadis", "label": "HR. BUKHARI 7123", "kitab": "bukhari", "nomor": "7123", "status": "belum"}]))
    d = r["dalil"][0]
    assert d["status"] == "terverifikasi" and d["derajat"] == "sahih" and d["teks_ar"] and d["diverifikasi_oleh"].startswith("sutradara.dalil")
    assert not kode(periksa(r, final=True))


def test_hadis_daif_ditolak():
    r, _ = verifikasi(_rencana([{"id": "a", "jenis": "hadis", "label": "HR. ABU DAWUD", "kitab": "abudawud", "nomor": DAIF, "status": "belum"}]))
    assert "DERAJAT_HADIS" in kode(periksa(r))


def test_nomor_salah_dan_kitab_tak_tersedia_tidak_pernah_lulus():
    r, _ = verifikasi(_rencana([
        {"id": "a", "jenis": "hadis", "label": "HR. BUKHARI 999999", "kitab": "bukhari", "nomor": "999999", "status": "belum"},
        {"id": "b", "jenis": "hadis", "label": "HR. AHMAD 22308", "kitab": "ahmad", "nomor": "22308", "status": "belum"}]))
    assert all(d["status"] == "belum" and d["alasan"] for d in r["dalil"])
    assert "DALIL_BELUM_DICEK" in kode(periksa(r, final=True))


def test_status_diketik_tangan_tidak_diterima_saat_final():
    r = _rencana([{"id": "a", "jenis": "hadis", "label": "HR. BUKHARI 7123", "kitab": "bukhari", "nomor": "7123",
                   "derajat": "sahih", "status": "terverifikasi"}])
    assert "DALIL_BELUM_DICEK" in kode(periksa(r, final=True))


def _transport_palsu(panggilan):
    def t(metode, url, kepala, data=None):
        panggilan.append(url)
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "tok", "expires_in": 3600}
        if "/resources/translations" in url:
            return 200, {"translations": [{"id": 33, "name": "Indonesian Islamic Affairs Ministry", "language_name": "indonesian"}]}
        if "/chapters" in url:
            return 200, {"chapters": [{"id": 11, "name_simple": "Hud"}]}
        if "/verses/by_key/11:38" in url:
            return 200, {"verse": {"text_uthmani": "وَيَصْنَعُ ٱلْفُلْكَ", "translations": [{"resource_id": 33, "text": "Dan mulailah dia (Nuh) membuat kapal.<sup>1</sup>"}]}}
        return 404, {}
    return t


def test_verifikasi_quran_dengan_transport_palsu(tmp_path):
    panggilan = []
    q = QuranFoundation(transport=_transport_palsu(panggilan), cache=tmp_path)
    r, lap = verifikasi(_rencana([{"id": "h", "jenis": "quran", "label": "QS HUD 38", "surah": 11, "ayat": "38", "status": "belum"}]), quran=q)
    d = r["dalil"][0]
    assert d["status"] == "terverifikasi" and d["terjemah"] == "Dan mulailah dia (Nuh) membuat kapal." and "label_saran" not in d
    r2, _ = verifikasi(_rencana([{"id": "h", "jenis": "quran", "label": "QS NUH 38", "surah": 11, "ayat": "38", "status": "belum"}]), quran=q)
    assert r2["dalil"][0]["label_saran"] == "QS HUD 38"
    r3, _ = verifikasi(_rencana([{"id": "h", "jenis": "quran", "label": "QS HUD 999", "surah": 11, "ayat": "999", "status": "belum"}]), quran=q)
    assert r3["dalil"][0]["status"] == "belum"
    assert not any("secret" in u.lower() for u in panggilan)
