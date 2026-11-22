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
    assert len(hasil["beat"][0]["shot"]) == 1
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



def test_blocking_otomatis_mengikuti_visual_inti_dan_memisahkan_pihak():
    naskah = {
        "judul": "Pembangunan bahtera",
        "inti": "Nabi Nuh dan pengikut beriman membangun bahtera.",
        "dalil": [],
        "beat": [{
            "narasi": "Pengikut beriman membangun bahtera.",
            "dalil": [], "kata_kunci": ["membangun"], "suasana": "senja",
            "peran": ["pengikut beriman", "kaum penentang"],
        }],
    }
    hasil = rancang(naskah)
    beat = hasil["beat"][0]
    shot = beat["shot"][0]
    kapal = next(b for b in shot["benda"] if b["jenis"] == "bahtera")
    pengikut = next(t for t in shot["tokoh"] if t["peran"] == "pengikut_beriman")
    penentang = next(t for t in shot["tokoh"] if t["peran"] == "kaum_penentang")
    assert abs(pengikut["x"] - kapal["x"]) < 150
    assert pengikut["arah"] == "samping" and pengikut["balik"] is True
    assert abs(penentang["x"] - kapal["x"]) > 180
    assert all(120 <= tokoh["x"] <= 960 for tokoh in shot["tokoh"])
    assert beat["pelaku"] == ["pengikut_beriman"]
    temuan = periksa(hasil)
    assert not [t for t in temuan if t.kode in {"PELAKU_JAUH", "BUKAN_PELAKU_DEKAT"}]


def test_dialog_reverse_shot_mempertahankan_sisi_dan_mengganti_pembicara():
    naskah = {
        "judul": "Percakapan",
        "inti": "Nabi Nuh berbicara kepada seorang penentang.",
        "dalil": [],
        "beat": [{
            "narasi": "Nabi Nuh berkata kepada penentang itu.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Nabi Nuh", "penentang"],
            "dialog": [{"pembicara": "Nabi Nuh", "penjawab": "penentang",
                        "ucapan": "Dengarkan seruanku."}],
        }],
    }
    hasil = rancang(naskah)
    shots = hasil["beat"][0]["shot"]
    assert len(shots) == 2
    kiri, kanan = shots
    assert kiri["nur"][0]["x"] == kanan["nur"][0]["x"]
    assert kiri["tokoh"][0]["x"] == kanan["tokoh"][0]["x"]
    assert kiri["nur"][0]["bicara"]
    assert not kanan["nur"][0]["bicara"]
    assert kanan["tokoh"][0].get("bicara")
    assert not kiri["tokoh"][0].get("bicara")
    assert kiri["tokoh"][0]["arah"] == "samping"
    assert kanan["tokoh"][0]["arah"] == "samping"



def test_interaksi_otomatis_menghadapkan_pemberi_dan_penerima():
    naskah = {
        "judul": "Serah terima",
        "inti": "Pemberi mengulurkan surat kepada penerima.",
        "dalil": [],
        "beat": [{
            "narasi": "Pemberi mengulurkan surat kepada penerima.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Pemberi", "Penerima"],
        }],
    }
    shot = rancang(naskah)["beat"][0]["shot"][0]
    pemberi = next(t for t in shot["tokoh"] if t["peran"] == "pemberi")
    penerima = next(t for t in shot["tokoh"] if t["peran"] == "penerima")
    assert (pemberi["x"], penerima["x"]) == (380, 820)
    assert pemberi["arah"] == penerima["arah"] == "samping"
    assert pemberi["balik"] is False and penerima["balik"] is True
    assert pemberi["gerak"] == penerima["gerak"] == "ulurkan"


def test_perjalanan_otomatis_mengenali_tujuan_benda_dan_kedalaman():
    menuju = {
        "judul": "Menuju bahtera", "inti": "Pengelana berjalan menuju bahtera.", "dalil": [],
        "beat": [{
            "narasi": "Pengelana berjalan menuju bahtera.", "dalil": [],
            "kata_kunci": ["berjalan"], "suasana": "senja", "peran": ["Pengelana"],
        }],
    }
    aktor = rancang(menuju)["beat"][0]["shot"][0]["tokoh"][0]
    assert aktor["tujuan"] == "benda:bahtera"
    assert aktor["x"][-1][1] < 650 and aktor["x"][-1][1] > aktor["x"][0][1]

    menjauh = {
        "judul": "Menjauh", "inti": "Pengelana berjalan menjauh dari kamera.", "dalil": [],
        "beat": [{
            "narasi": "Pengelana berjalan menjauh dari kamera.", "dalil": [],
            "kata_kunci": ["berjalan"], "suasana": "senja", "peran": ["Pengelana"],
        }],
    }
    aktor = rancang(menjauh)["beat"][0]["shot"][0]["tokoh"][0]
    assert aktor["tujuan"] == "kedalaman:belakang"
    assert aktor["arah"] == "belakang"
    assert aktor["lintasan"][-1][2] < aktor["lintasan"][0][2]
    assert aktor["y"][-1][1] < aktor["y"][0][1]


def test_kabur_otomatis_bergerak_berlawanan_dengan_arah_perjalanan_bawaan():
    naskah = {
        "judul": "Kabur", "inti": "Pengelana kabur.", "dalil": [],
        "beat": [{
            "narasi": "Pengelana kabur.", "dalil": [],
            "kata_kunci": [], "suasana": "senja", "peran": ["Pengelana"],
        }],
    }
    aktor = rancang(naskah)["beat"][0]["shot"][0]["tokoh"][0]
    assert aktor["gerak"] == "lari"
    assert aktor["tujuan"] == "tepi:kiri"
    assert aktor["x"][-1][1] < aktor["x"][0][1]



def test_menunjuk_visual_inti_menghadap_ke_benda():
    naskah = {
        "judul": "Menunjuk bahtera",
        "inti": "Pengelana menunjuk bahtera.",
        "dalil": [],
        "beat": [{
            "narasi": "Pengelana menunjuk bahtera.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Pengelana"],
        }],
    }
    aktor = rancang(naskah)["beat"][0]["shot"][0]["tokoh"][0]
    assert aktor["arah"] == "samping"
    assert aktor["balik"] is False
    assert aktor["gerak"] == "tunjuk"
    assert aktor["x"] < 650



def test_dialog_menyisipkan_reaksi_pendengar_bila_disebut_narasi():
    naskah = {
        "judul": "Seruan",
        "inti": "Seorang penyeru menyampaikan peringatan kepada pendengar.",
        "dalil": [],
        "beat": [{
            "narasi": "Penyeru berbicara. Pendengar terkejut dan tersentak.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Penyeru", "Pendengar"],
            "dialog": [{"pembicara": "Penyeru", "penjawab": "Pendengar", "ucapan": "Dengarkan peringatan ini."}],
        }],
    }
    shot = rancang(naskah)["beat"][0]["shot"]
    assert len(shot) == 3
    reaksi = shot[1]["tokoh"]
    pendengar = next(t for t in reaksi if t["peran"] == "pendengar")
    assert pendengar["gerak"] == "kaget"
    assert pendengar["wajah"] == "kaget"
    assert "bicara" not in pendengar
    reverse = {t["peran"]: t for t in shot[2]["tokoh"]}
    assert reverse["pendengar"].get("bicara")
    assert "bicara" not in reverse["penyeru"]



def test_pengejar_dan_yang_dikejar_bergerak_searah():
    naskah = {
        "judul": "Pengejaran",
        "inti": "Pengelana mengejar pencuri ke tepi kanan.",
        "dalil": [],
        "beat": [{
            "narasi": "Pengelana mengejar pencuri ke tepi kanan.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Pengelana", "Pencuri"],
        }],
    }
    tokoh = rancang(naskah)["beat"][0]["shot"][0]["tokoh"]
    pengelana = next(t for t in tokoh if t["peran"] == "pengelana")
    pencuri = next(t for t in tokoh if t["peran"] == "pencuri")
    assert pengelana["gerak"] == pencuri["gerak"] == "lari"
    dx_a = pengelana["x"][-1][1] - pengelana["x"][0][1]
    dx_b = pencuri["x"][-1][1] - pencuri["x"][0][1]
    assert dx_a > 0 and dx_b > 0
    assert pengelana["tujuan"] == pencuri["tujuan"] == "tepi:kanan"
