import copy
import json
from pathlib import Path

import pytest

from sutradara.rencana import periksa

CONTOH = Path(__file__).resolve().parents[1] / "contoh"


def muat(nama):
    return json.loads((CONTOH / nama).read_text(encoding="utf-8"))


def kode(temuan, tingkat="GAGAL"):
    return {t.kode for t in temuan if t.tingkat == tingkat}


@pytest.mark.parametrize("nama", sorted(p.name for p in CONTOH.glob("*.json")))
def test_semua_contoh_tidak_gagal(nama):
    assert not kode(periksa(muat(nama)))


def test_nabi_tidak_boleh_digambar_sebagai_tokoh():
    r = muat("nuh_mengejek.json")
    r["peran"][0]["tampil"] = "pakaian"
    assert "TOKOH_SUCI" in kode(periksa(r))


def test_shot_tidak_boleh_memakai_nabi_sebagai_tokoh():
    r = muat("nuh_mengejek.json")
    r["beat"][0]["shot"][0]["tokoh"] = [{"x": 300, "y": 1300, "peran": "nuh"}]
    assert "TOKOH_SUCI" in kode(periksa(r))


def test_penjaga_rencana_otomatis_mewajibkan_tujuan_dan_lintasan_jalan():
    r = muat("nuh_mengejek.json")
    r["beat"] = [r["beat"][0]]
    r["beat"][0]["shot"] = [r["beat"][0]["shot"][0]]
    r["hook"]["dari_beat"] = 0
    r["dibuat_otomatis"] = True
    aktor = r["beat"][0]["shot"][0]["tokoh"][0]
    aktor.update(gerak="jalan", x=aktor["x"] if isinstance(aktor["x"], (int, float)) else 430)
    assert {"TUJUAN_GERAK_TAK_ADA", "LINTASAN_TAK_ADA"} <= kode(periksa(r))
    aktor.update(tujuan="tepi:kiri", x=[[0, 520], [2, 300]], arah="samping", balik=True)
    assert not {"TUJUAN_GERAK_TAK_ADA", "LINTASAN_TAK_ADA"} & kode(periksa(r))


def test_nur_hanya_untuk_tokoh_suci():
    r = muat("nuh_mengejek.json")
    r["peran"][1]["tampil"] = "nur"
    assert "NUR_KHUSUS" in kode(periksa(r))


def test_makhluk_tanpa_wujud_dalil_harus_kabut():
    r = muat("dabbah_dhuha.json")
    r["peran"][0]["tampil"] = "pakaian"
    assert "WUJUD_TAK_DIJELASKAN" in kode(periksa(r))


def test_dajjal_hanya_desain_b_atau_siluet():
    r = muat("dajjal_dua_sungai.json")
    r["peran"][0]["tampil"] = "kabut_tanpa_wujud"
    assert "DAJJAL" in kode(periksa(r))


def test_hadis_lemah_ditolak():
    r = muat("dajjal_dua_sungai.json")
    r["dalil"][0].update(status="terverifikasi", diverifikasi_oleh="sutradara.dalil uji", derajat="daif")
    assert "DERAJAT_HADIS" in kode(periksa(r))


def test_dalil_belum_dicek_gagal_saat_final():
    r = muat("nuh_mengejek.json")
    assert not kode(periksa(r, final=True))  # contoh sudah diverifikasi mesin (workflow 'verifikasi dalil')
    r["dalil"][0]["status"] = "belum"
    assert "DALIL_BELUM_DICEK" in kode(periksa(r), "PERIKSA")
    assert "DALIL_BELUM_DICEK" in kode(periksa(r, final=True))


def test_keadaan_harus_ada_di_jalur_visual_inti():
    r = muat("nuh_mengejek.json")
    r["beat"][1]["keadaan"] = "tenggelam"
    assert "KEADAAN" in kode(periksa(r))


def test_skema_menolak_kunci_asing():
    r = copy.deepcopy(muat("nuh_mengejek.json"))
    r["warna_favorit"] = "merah"
    assert "SKEMA" in kode(periksa(r))


def test_siluet_tanpa_alasan_diberi_catatan():
    r = muat("nuh_mengejek.json")
    r["peran"][1]["tampil"] = "siluet"
    assert "SILUET_TANPA_ALASAN" in kode(periksa(r), "PERIKSA")


def test_pelaku_harus_dekat_visual_inti():
    r = muat("nuh_mengejek.json")
    assert not {"PELAKU_JAUH", "BUKAN_PELAKU_DEKAT"} & kode(periksa(r), "PERIKSA")
    r["beat"][0]["shot"][0]["nur"][0]["x"] = -300  # Nabi Nuh dijauhkan dari kapal
    assert "PELAKU_JAUH" in kode(periksa(r), "PERIKSA")


def test_beberapa_pelaku_tidak_membebaskan_tokoh_non_pelaku_yang_lebih_dekat():
    r = muat("nuh_mengejek.json")
    r["beat"][0]["pelaku"] = ["nuh", "pengikut_beriman"]
    sh = r["beat"][0]["shot"][0]
    sh["nur"][0]["x"] = 60
    sh["tokoh"] = [
        {"x": 60, "y": 1330, "peran": "pengikut_beriman", "pose": "palu"},
        {"x": 620, "y": 1260, "peran": "kaum", "pose": "silang"},
    ]
    temuan = kode(periksa(r), "PERIKSA")
    assert "PELAKU_JAUH" in temuan
    assert "BUKAN_PELAKU_DEKAT" in temuan


def test_pembangun_nuh_dan_kaum_pengejek_memiliki_peran_berbeda():
    r = muat("nuh_mengejek.json")
    shot = r["beat"][0]["shot"][0]
    assert r["beat"][0]["pelaku"] == ["nuh", "pengikut_beriman"]
    assert all(t["peran"] == "pengikut_beriman" and "nama" not in t and "bicara" not in t
               for t in shot["tokoh"])
    assert r["peran"][1]["id"] == "kaum"
    assert r["peran"][2]["id"] == "pengikut_beriman"



def test_blocking_otomatis_mengubah_pelanggaran_kedekatan_menjadi_gagal():
    r = muat("nuh_mengejek.json")
    r["dibuat_otomatis"] = True
    r["beat"] = [r["beat"][0]]
    r["beat"][0]["shot"] = [r["beat"][0]["shot"][0]]
    r["hook"]["dari_beat"] = 0
    r["beat"][0]["shot"][0]["nur"][0]["x"] = -300
    temuan = periksa(r)
    assert "PELAKU_JAUH" in kode(temuan, "GAGAL")


def test_perjalanan_otomatis_menyimpan_lintasan_xy_eksplisit():
    naskah = {
        "judul": "Perjalanan",
        "inti": "Pengelana berjalan menuju tepi kanan.",
        "dalil": [],
        "beat": [{
            "narasi": "Pengelana berjalan menuju tepi kanan.",
            "dalil": [], "kata_kunci": ["berjalan"], "suasana": "senja",
            "peran": ["pengelana"],
        }],
    }
    from sutradara.direktur import rancang
    hasil = rancang(naskah)
    aktor = hasil["beat"][0]["shot"][0]["tokoh"][0]
    assert aktor["tujuan"] == "tepi:kanan"
    assert aktor["lintasan"][0][1:] == [aktor["x"][0][1], aktor["y"]]
    assert aktor["lintasan"][1][1] == aktor["x"][-1][1]
    assert aktor["lintasan"][1][2] == aktor["y"]



def test_perjalanan_kedalaman_depan_belakang_tidak_diberi_peringatan_mendatar():
    from sutradara.rencana.pemeriksaan_umum import periksa_lintasan_dan_interaksi

    rencana = {
        "peran": [{"id": "pengelana", "nama": "Pengelana"}],
        "beat": [{
            "shot": [{
                "tokoh": [{
                    "peran": "pengelana", "gerak": "jalan", "tujuan": "kedalaman:belakang",
                    "arah": "belakang", "x": [[0, 430], [3, 430]],
                    "y": [[0, 1510], [3, 1300]],
                    "lintasan": [[0, 430, 1510], [3, 430, 1300]],
                }]
            }]
        }]
    }
    temuan = periksa_lintasan_dan_interaksi(rencana)
    assert "ARAH_GERAK" not in {t.kode for t in temuan}



def test_penjaga_mendeteksi_tokoh_bertumpuk_dan_posisi_berubah_antar_shot():
    from sutradara.rencana.pemeriksaan_umum import periksa_kontinuitas_panggung

    rencana = {
        "beat": [{
            "shot": [
                {"tokoh": [
                    {"peran": "pemberi", "x": 400, "y": 1500, "s": .68},
                    {"peran": "penerima", "x": 420, "y": 1500, "s": .68},
                ]},
                {"tokoh": [
                    {"peran": "pemberi", "x": 650, "y": 1500, "s": .68},
                    {"peran": "penerima", "x": 820, "y": 1500, "s": .68},
                ]},
            ]
        }]
    }
    temuan = periksa_kontinuitas_panggung(rencana)
    kode_temuan = {t.kode for t in temuan}
    assert "TOKOH_BERTUMPUK" in kode_temuan
    assert "POSISI_BERUBAH_ANTAR_SHOT" in kode_temuan


def test_penjaga_tidak_menganggap_anggota_kelompok_satu_peran_bertumpuk():
    from sutradara.rencana.pemeriksaan_umum import periksa_kontinuitas_panggung

    rencana = {"beat": [{"shot": [{"tokoh": [
        {"peran": "kaum", "x": 400, "y": 1500},
        {"peran": "kaum", "x": 430, "y": 1500},
        {"peran": "kaum", "x": 460, "y": 1500},
    ]}]}]}
    assert not periksa_kontinuitas_panggung(rencana)


def test_penjaga_memahami_jadwal_putar_balik_dan_tetap_memeriksa_kaidah_180():
    from sutradara.rencana.pemeriksaan_umum import periksa_lintasan_dan_interaksi

    dasar = {
        "peran": [{"id": "pengelana", "nama": "Pengelana"}],
        "beat": [
            {"shot": [{"tokoh": [{
                "peran": "pengelana", "gerak": "lari", "tujuan": "tepi:kanan",
                "arah": "samping", "balik": False,
                "lintasan": [[0, 430, 1510], [3.8, 710, 1510]],
            }]}]},
            {"shot": [{"tokoh": [{
                "peran": "pengelana", "gerak": "lari", "tujuan": "tepi:kanan",
                "arah": [[0, "samping"], [1.2, "depan"], [2.5, "samping"]],
                "balik": [[0, False], [2.5, True]], "berbalik_sesuai_cerita": True,
                "lintasan": [[0, 710, 1510], [3.8, 430, 1510]],
            }]}]},
        ],
    }
    temuan = periksa_lintasan_dan_interaksi(dasar)
    assert "ARAH_GERAK" not in {x.kode for x in temuan}
    assert "ARAH_LAYAR_BERUBAH" not in {x.kode for x in temuan}

    dasar["beat"][1]["shot"][0]["tokoh"][0].pop("berbalik_sesuai_cerita")
    temuan = periksa_lintasan_dan_interaksi(dasar)
    assert "ARAH_LAYAR_BERUBAH" in {x.kode for x in temuan}
