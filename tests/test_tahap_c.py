import json

from sutradara.dalil import koreksi
from sutradara.dalil.quran import QuranFoundation
from sutradara.dalil.verifikasi import verifikasi_quran
from sutradara.gaya import kartu


def test_koreksi_terjemah_menunggu_persetujuan_pemilik():
    dalil = {"jenis": "hadis", "kitab": "muslim", "nomor": "2934b"}
    usulan = [{"kitab": "muslim", "nomor": "2934b", "teks_asli": "surga",
               "teks_koreksi": "sungai", "status": "menunggu_persetujuan_pemilik"}]
    assert koreksi.terapkan_terjemah(dalil, "Dia menuju surga.", koreksi=usulan) == "Dia menuju surga."
    disetujui = [dict(usulan[0], status="disetujui_pemilik")]
    assert koreksi.terapkan_terjemah(dalil, "Dia menuju surga.", koreksi=disetujui) == "Dia menuju sungai."
    assert koreksi.terapkan_terjemah(dalil, "surga dan surga", koreksi=disetujui) == "surga dan surga"


def test_kartu_hanya_menerapkan_koreksi_yang_disetujui(monkeypatch):
    dalil = {"jenis": "hadis", "kitab": "muslim", "nomor": "2934b", "teks_ar": "النهر",
             "terjemah": "surga"}
    monkeypatch.setattr(koreksi, "daftar", lambda: [
        {"kitab": "muslim", "nomor": "2934b", "teks_asli": "surga", "teks_koreksi": "sungai",
         "status": "menunggu_persetujuan_pemilik"}
    ])
    assert kartu.teks_kartu(dalil) == ("النهر", "surga")
    monkeypatch.setattr(koreksi, "daftar", lambda: [
        {"kitab": "muslim", "nomor": "2934b", "teks_asli": "surga", "teks_koreksi": "sungai",
         "status": "disetujui_pemilik"}
    ])
    assert kartu.teks_kartu(dalil) == ("النهر", "sungai")


def test_kartu_memakai_pasangan_kata_resmi_tanpa_potong_proporsional():
    dalil = {"jenis": "quran", "teks_ar": "نص عربي كامل", "terjemah": "terjemahan utuh",
             "pasangan_kata": [{"ar": "وَيَصْنَعُ", "id": "dan membuat"},
                               {"ar": "الْفُلْكَ", "id": "kapal"}]}
    assert kartu.potongan(dalil) == [("وَيَصْنَعُ الْفُلْكَ", "dan membuat kapal")]


def test_quran_foundation_menyimpan_pasangan_kata_dari_api(tmp_path):
    def transport(metode, url, kepala, data=None):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "token-uji", "expires_in": 3600}
        if "/resources/translations" in url:
            return 200, {"translations": [{"id": 33, "name": "Kemenag", "language_name": "indonesian"}]}
        if "/chapters" in url:
            return 200, {"chapters": [{"id": 11, "name_simple": "Hud"}]}
        if "/verses/by_key/11:38" in url:
            return 200, {"verse": {
                "text_uthmani": "وَيَصْنَعُ الْفُلْكَ",
                "translations": [{"resource_id": 33, "text": "Dan dia membuat kapal."}],
                "words": [
                    {"text_uthmani": "وَيَصْنَعُ", "translation": {"text": "dan membuat"}},
                    {"text_uthmani": "الْفُلْكَ", "translation": {"text": "kapal"}}
                ]
            }}
        return 404, {}

    quran = QuranFoundation(transport=transport, cache=tmp_path)
    dalil = {"jenis": "quran", "label": "QS HUD 38", "surah": 11, "ayat": "38"}
    laporan = verifikasi_quran(dalil, quran)
    assert "✓" in laporan
    assert dalil["pasangan_kata"] == [
        {"ar": "وَيَصْنَعُ", "id": "dan membuat"},
        {"ar": "الْفُلْكَ", "id": "kapal"}
    ]


def test_bacaan_latin_tetap_mati_tanpa_permintaan_pemilik(monkeypatch):
    from sutradara.dalil import quran
    monkeypatch.setattr(quran, "FITUR_BACAAN_LATIN", False)
    klien = QuranFoundation(transport=lambda *a, **k: (_ for _ in ()).throw(AssertionError("API tidak boleh dipanggil")),
                            cache=None)
    assert klien.transliterasi_latin(1, 1) is None
