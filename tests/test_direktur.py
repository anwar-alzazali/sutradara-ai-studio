"""Sutradara otomatis: masukan antrean, kait paket, dan model opsional."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sutradara import genre
from sutradara.direktur import rancang
from sutradara.rencana import periksa


AKAR = Path(__file__).parents[1]


@pytest.mark.parametrize("nama", ["nuh", "hud"])
def test_naskah_contoh_menghasilkan_rencana_layak_tanpa_model(nama, monkeypatch):
    monkeypatch.delenv("SUTRADARA_AI_AKTIF", raising=False)
    naskah = json.loads((AKAR / "naskah" / f"{nama}.json").read_text(encoding="utf-8-sig"))
    hasil = rancang(naskah)
    assert hasil["dibuat_otomatis"] is True
    assert hasil["visual_inti"]["jalur_keadaan"]
    assert all(b["shot"] for b in hasil["beat"])
    assert not [t for t in periksa(hasil) if t.tingkat == "GAGAL"]


def test_peran_kolektif_digambar_sebagai_kelompok_pada_shot_lebar():
    naskah = json.loads((AKAR / "naskah/nuh.json").read_text(encoding="utf-8-sig"))
    hasil = rancang(naskah)
    # Pada shot pembuka lebar, Nabi tampil sebagai nur dan kaum sebagai beberapa orang.
    shot = hasil["beat"][0]["shot"][0]
    assert len([t for t in shot["tokoh"] if t["peran"] == "kaum_nuh"]) == 3
    assert not [t for t in shot["tokoh"] if t["peran"] == "nabi_nuh"]
    assert any(n["peran"] == "nabi_nuh" for n in shot["nur"])


def test_jalan_mengisi_tujuan_lintasan_arah_dan_frekuensi_langkah():
    naskah = {"judul": "Perjalanan", "inti": "Seseorang menuju tepi jalan.", "dalil": [],
              "beat": [{"narasi": "Seorang pengelana berjalan menuju tepi kanan.", "dalil": [],
                        "kata_kunci": ["berjalan"], "suasana": "senja", "peran": ["pengelana"]}]}
    hasil = rancang(naskah)
    tokoh = hasil["beat"][0]["shot"][0]["tokoh"][0]
    assert tokoh["gerak"] == "jalan" and tokoh["arah"] == "samping"
    assert tokoh["tujuan"] == "tepi:kanan" and len(tokoh["x"]) == 2
    assert tokoh["faktor_gerak"] > 0
    assert not [t for t in periksa(hasil) if t.tingkat == "GAGAL"]


def test_model_tidak_dipanggil_bawaan_dan_hanya_jika_aturan_ragu(tmp_path):
    naskah = {"judul": "Kisah tak dikenal", "inti": "Renungan tanpa tokoh tertentu.", "dalil": [],
              "beat": [{"narasi": "Mari mengambil pelajaran.", "dalil": [], "kata_kunci": ["pelajaran"],
                        "suasana": "fajar", "peran": ["orang beriman"]}]}
    biaya = tmp_path / "biaya.jsonl"
    panggil = []
    def model(n, kandidat):
        panggil.append(True)
        return kandidat, {"penyedia": "tiruan", "model": "ujian", "input_token": 2, "output_token": 3,
                          "biaya_usd": 0}
    rancang(naskah, model=model, biaya_ke=biaya)
    assert not panggil and not biaya.exists()
    with pytest.raises(RuntimeError, match="adapter model tidak tersedia"):
        rancang(naskah, gunakan_model=True)
    rancang(naskah, gunakan_model=True, model=model, biaya_ke=biaya)
    assert panggil and json.loads(biaya.read_text(encoding="utf-8").splitlines()[0])["biaya_usd"] == 0


def test_resep_dapat_ditambah_dari_data_paket():
    paket = genre.ambil("kisah_islami")
    assert paket.sutradara is not None
    data = json.loads((AKAR / "sutradara/paket_genre/kisah_islami/resep_adegan.json").read_text(encoding="utf-8"))
    ids = [r["id"] for r in data["resep"]]
    assert len(ids) == len(set(ids))
    assert {"kaum_mengejek", "azab_datang", "doa_sunyi"} <= set(ids)


def test_nama_rasulullah_dan_aisyah_memakai_representasi_sakral():
    from sutradara.paket_genre.kisah_islami.sutradara import _peran

    hasil, _ = _peran({"beat": [{"peran": ["Rasulullah ﷺ", "Aisyah RA"]}]})
    peta = {p["nama"]: p for p in hasil}
    assert (peta["Rasulullah ﷺ"]["kategori"], peta["Rasulullah ﷺ"]["tampil"]) == ("nabi", "nur")
    assert (peta["Aisyah RA"]["kategori"], peta["Aisyah RA"]["tampil"]) == ("sahabat", "wajah_cahaya")
    assert peta["Aisyah RA"]["identitas"]["jenis"] == "wanita"


@pytest.mark.parametrize("nama", ["Allah", "Allah SWT", "Tuhan"])
def test_allah_tidak_dapat_dimasukkan_sebagai_peran_visual(nama):
    from sutradara.antrean import validasi

    naskah = {"judul": "Uji", "inti": "Renungan.", "dalil": [], "beat": [{
        "narasi": "Renungkan makna kisah ini.", "kata_kunci": [], "dalil": [], "peran": [nama],
    }]}
    assert any("tidak boleh menjadi peran visual" in pesan for pesan in validasi(naskah))
