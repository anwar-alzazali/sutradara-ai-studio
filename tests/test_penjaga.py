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


def test_npc_tidak_boleh_lebih_dekat_ke_visual_inti_daripada_pelaku():
    r = muat("nuh_mengejek.json")
    sh = r["beat"][0]["shot"][0]
    sh["nur"][0]["x"] = 60
    sh["tokoh"] = [{"x": 620, "y": 1260, "peran": "kaum", "pose": "silang"}]  # orang kaum berdiri di samping kapal
    assert "BUKAN_PELAKU_DEKAT" in kode(periksa(r), "PERIKSA")
