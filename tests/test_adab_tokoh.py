import copy
import json
from pathlib import Path

import pytest

from sutradara import adegan, video
from sutradara.gaya import malaikat, nur, tokoh
from sutradara.rencana.penjaga import periksa


CONTOH = Path(__file__).parents[1] / "contoh"


def _rencana():
    return json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))


def _tambah_golongan(r):
    r["peran"] += [
        {"id": "malaikat", "nama": "Malaikat", "kategori": "malaikat", "tampil": "cahaya_malaikat"},
        {"id": "sahabat", "nama": "Sahabat", "kategori": "sahabat", "tampil": "wajah_cahaya"},
    ]
    shot = r["beat"][0]["shot"][0]
    shot["nur"].append({"x": 760, "y": 1330, "nama": "Malaikat", "peran": "malaikat", "tinggi": 1500})
    shot["tokoh"].append({"x": 900, "y": 1395, "s": 0.9, "peran": "sahabat", "pose": "berdiri"})
    return shot


def _kode(r):
    return {temuan.kode for temuan in periksa(r)}


def test_berkas_malaikat_berbeda_dari_pilar_nabi():
    svg_malaikat = malaikat.berkas(500, 1300)
    svg_nabi = nur.pilar(500, 1300)
    assert 'class="cahaya-malaikat"' in svg_malaikat
    assert 'class="nur"' not in svg_malaikat
    assert 'class="nur"' in svg_nabi
    assert 'rx="59"' not in svg_malaikat
    assert " 0.0 " in svg_malaikat
    with pytest.raises(ValueError, match="tepi atas bingkai"):
        malaikat.berkas(500, 1300, tinggi=620)


def test_wajah_cahaya_tidak_memiliki_fitur_dan_mengikuti_sudut_hadap():
    depan = tokoh.orang(500, 1500, wajah="marah", bicara=[(0, 2)], wajah_cahaya=True, arah="depan")
    samping = tokoh.orang(500, 1500, wajah="marah", bicara=[(0, 2)], wajah_cahaya=True, arah="samping")
    belakang = tokoh.orang(500, 1500, wajah="marah", bicara=[(0, 2)], wajah_cahaya=True, arah="belakang")
    for svg in (depan, samping):
        assert 'fill="#fff8df"' in svg
        assert "M-18 -17" not in svg
        assert "M-9 16" not in svg
        assert "<ellipse cx=\"0\" cy=\"17\"" not in svg
    assert 'fill="#fff8df"' not in belakang


def test_adab_semua_golongan_lulus_dan_renderer_memilih_bentuk_berbeda():
    r = _rencana()
    shot = _tambah_golongan(r)
    assert not {"TOKOH_SUCI", "MALAIKAT_TAMPIL", "SAHABAT_TAMPIL", "CAHAYA_KHUSUS"} & _kode(r)
    shot_render = video.daftar_shot(r)[0]
    svg = adegan.susun(shot_render)
    assert 'class="cahaya-malaikat"' in svg
    assert 'class="nur"' in svg
    assert 'fill="#fff8df"' in svg


def test_nabi_tetap_wajib_pilar():
    r = _rencana()
    r["peran"][0]["tampil"] = "pakaian"
    assert "TOKOH_SUCI" in _kode(r)


def test_malaikat_tidak_boleh_memakai_pilar():
    r = _rencana()
    _tambah_golongan(r)
    r["peran"][-2]["tampil"] = "nur"
    assert "MALAIKAT_TAMPIL" in _kode(r)


def test_sahabat_wajib_tubuh_dengan_wajah_cahaya():
    r = _rencana()
    _tambah_golongan(r)
    r["peran"][-1]["tampil"] = "nur"
    assert "SAHABAT_TAMPIL" in _kode(r)


def test_manusia_biasa_dilarang_memakai_bentuk_cahaya_khusus():
    r = _rencana()
    r["peran"][1]["tampil"] = "cahaya_malaikat"
    assert "CAHAYA_KHUSUS" in _kode(r)


def test_sahabat_dilarang_ditampilkan_sebagai_pilar():
    r = _rencana()
    _tambah_golongan(r)
    r["beat"][0]["shot"][0]["nur"].append({"x": 820, "y": 1300, "peran": "sahabat"})
    assert "SAHABAT_BERTIANG" in _kode(r)


def test_malaikat_dilarang_ditampilkan_sebagai_tubuh():
    r = _rencana()
    _tambah_golongan(r)
    r["beat"][0]["shot"][0]["tokoh"].append({"x": 700, "y": 1400, "peran": "malaikat"})
    assert "TOKOH_SUCI_BERTUBUH" in _kode(r)


def test_setiap_bentuk_cahaya_wajib_menunjuk_id_peran():
    r = _rencana()
    r["beat"][0]["shot"][0]["nur"].append({"x": 800, "y": 1300})
    assert "CAHAYA_TANPA_PERAN" in _kode(r)


def test_kartu_identitas_dipakai_renderer_dan_perubahan_dicatat_periksa():
    r = _rencana()
    shot = r["beat"][0]["shot"][0]
    shot["tokoh"].append({"x": 760, "y": 1390, "s": 0.9, "peran": "kaum"})
    svg = adegan.susun(video.daftar_shot(r)[0])
    assert '#c98b62' in svg
    assert '#7a3b2e' in svg
    shot["tokoh"][-1]["warna_baju"] = "#123456"
    temuan = _periksa(r)
    assert any(x.kode == "IDENTITAS_BERUBAH" and x.tingkat == "PERIKSA" for x in temuan)


def _periksa(r):
    return periksa(r)


def test_barang_menempel_di_tangan_manusia_dengan_ik():
    r = _rencana()
    shot = r["beat"][0]["shot"][0]
    shot["tokoh"].append({"x": 760, "y": 1390, "s": 0.9, "peran": "kaum"})
    shot["barang"] = [{"id": "surat_amanah", "jenis": "surat", "pemilik": "kaum",
                       "tangan": "ka", "aksi": "pegang", "posisi_genggam": [530, 1250]}]
    svg = adegan.susun(video.daftar_shot(r)[0])
    assert 'class="barang"' in svg
    assert "translate(" in svg


def test_barang_milik_nabi_tampil_di_sisi_pilar_tanpa_tangan():
    r = _rencana()
    shot = r["beat"][0]["shot"][0]
    shot["barang"] = [{"id": "tongkat_nabi", "jenis": "tongkat", "pemilik": "nuh",
                       "skala": 0.9, "sisi_x": 105, "sisi_y": -65}]
    svg = adegan.susun(video.daftar_shot(r)[0])
    assert 'class="nur"' in svg
    assert 'class="barang"' in svg
    assert 'fill="#fff2c8"' in svg
    assert not any(x in svg for x in ('pergelangan-nabi', 'tangan-nabi'))


def test_serah_terima_barang_mengubah_pemilik_dengan_aksi_berpasangan():
    r = _rencana()
    awal = copy.deepcopy(r["beat"][0]["shot"][0])
    awal["tokoh"] = [
        {"x": 410, "y": 1390, "s": 0.9, "peran": "kaum"},
        {"x": 700, "y": 1390, "s": 0.9, "peran": "pengikut_beriman"},
    ]
    awal["barang"] = [{"id": "surat_amanah", "jenis": "surat", "pemilik": "kaum",
                       "tangan": "ka", "aksi": "ulurkan", "penerima": "pengikut_beriman",
                       "titik_serah": [560, 1270], "tangan_pasangan": "ki"}]
    akhir = copy.deepcopy(awal)
    akhir["barang"] = [{"id": "surat_amanah", "jenis": "surat", "pemilik": "pengikut_beriman",
                        "tangan": "ki", "aksi": "terima", "pemberi": "kaum",
                        "titik_serah": [560, 1270], "tangan_pasangan": "ka"}]
    r["beat"] = [copy.deepcopy(r["beat"][0]), copy.deepcopy(r["beat"][0])]
    r["beat"][0]["shot"] = [awal]
    r["beat"][1]["shot"] = [akhir]
    temuan = periksa(r)
    assert not any(x.kode == "PEMILIK_BARANG_BERUBAH" for x in temuan)
    svg = adegan.susun(video.daftar_shot(r)[0])
    assert 'class="barang"' in svg


def test_perubahan_pemilik_barang_tanpa_serah_terima_ditolak():
    r = _rencana()
    a = copy.deepcopy(r["beat"][0]["shot"][0])
    a["tokoh"].append({"x": 760, "y": 1390, "s": 0.9, "peran": "kaum"})
    a["barang"] = [{"id": "surat_amanah", "jenis": "surat", "pemilik": "kaum"}]
    b = copy.deepcopy(a)
    b["tokoh"][-1]["peran"] = "pengikut_beriman"
    b["barang"] = [{"id": "surat_amanah", "jenis": "surat", "pemilik": "pengikut_beriman"}]
    r["beat"] = [copy.deepcopy(r["beat"][0]), copy.deepcopy(r["beat"][0])]
    r["beat"][0]["shot"] = [a]
    r["beat"][1]["shot"] = [b]
    assert any(x.kode == "PEMILIK_BARANG_BERUBAH" for x in periksa(r))


def test_contoh_b2_lengkap_lolos_penjaga_dan_render_semua_shot():
    r = json.loads((CONTOH / "b2_adab_barang.json").read_text(encoding="utf-8"))
    temuan = periksa(r)
    gagal = [x for x in temuan if x.tingkat == "GAGAL"]
    assert not gagal, "\\n".join(map(str, gagal))
    shots = video.daftar_shot(r)
    hasil = [adegan.susun(s) for s in shots]
    assert len(hasil) == 4
    assert all("<svg" in svg for svg in hasil)
    assert "DIULURKAN KE PILAR" in hasil[2]
    assert "DITERIMA DI SISI PILAR" in hasil[3]
    assert "Barang berpindah lewat tangan" in hasil[0]
    assert "Tongkat menuju pilar" in hasil[2]
    assert 'class="cahaya-malaikat"' in hasil[0]
    assert 'class="barang"' in hasil[0]
    assert 'class="barang"' in hasil[1]
    assert 'class="nur"' in hasil[2]
    assert 'class="barang"' in hasil[2]
    assert 'class="nur"' in hasil[3]
    assert 'class="barang"' in hasil[3]
    assert '#fff8df' in hasil[0]
    assert not any(x.kode == "PEMILIK_BARANG_BERUBAH" for x in temuan)


def test_kartu_identitas_mengikat_ciri_tetap_pada_tokoh_sahabat():
    r = json.loads((CONTOH / "b2_adab_barang.json").read_text(encoding="utf-8"))
    shot = r["beat"][0]["shot"][0]
    sahabat = next(t for t in shot["tokoh"] if t["peran"] == "sahabat")
    sahabat["warna_baju"] = "#abcdef"
    temuan = periksa(r)
    assert any(x.kode == "IDENTITAS_BERUBAH" and x.tingkat == "PERIKSA" for x in temuan)


def test_janggut_dapat_dikunci_dari_kartu_identitas():
    pendek = tokoh.orang(500, 1500, janggut="pendek", warna_janggut="#123456")
    tanpa = tokoh.orang(500, 1500, janggut="tanpa")
    assert "#123456" in pendek
    assert 'Q 0 60 30 14' not in tanpa


def test_perubahan_gaya_siluet_ke_pakaian_dicatat_terpisah_dari_drift():
    r = json.loads((CONTOH / "b2_adab_barang.json").read_text(encoding="utf-8"))
    p = next(x for x in r["peran"] if x["id"] == "pemberi")
    p["tampil"] = "siluet"
    tokoh_shot = r["beat"][0]["shot"][0]["tokoh"][0]
    tokoh_shot["mode"] = "pakaian"
    temuan = periksa(r)
    assert any(x.kode == "IDENTITAS_GAYA_BERUBAH" and x.tingkat == "PERIKSA" for x in temuan)
    tokoh_shot["perubahan_gaya"] = "Pengungkapan identitas sesuai alur cerita"
    temuan = periksa(r)
    assert any(x.kode == "PERUBAHAN_GAYA_DISENGAJA" for x in temuan)


def test_preset_ekspresi_halus_tersedia_dan_menghasilkan_ciri_wajah():
    for ekspresi in ("kepergok_panik", "jijik_ilfil", "sinis", "curiga", "heran"):
        svg = tokoh.orang(500, 1500, wajah=ekspresi)
        assert 'stroke-width="3.8"' in svg
        assert 'fill="#fff"' in svg
    # Heran dibuat sebagai keterkejutan ringan, bukan mata dan mulut terbuka lebar seperti kaget.
    heran = tokoh.orang(500, 1500, wajah="heran")
    kaget = tokoh.orang(500, 1500, wajah="kaget")
    assert heran != kaget
    assert 'M-9 16 h18' in heran
    assert 'rx="5.7" ry="5.2"' in heran
    assert 'rx="9" ry="11"' in kaget


def test_kendali_mikro_wajah_mengatur_kelopak_lirikan_alis_hidung_dan_mulut():
    svg = tokoh.orang(500, 1500, wajah="datar", detail_wajah={
        "kelopak": 0.8, "lirikan": 0.7, "alis_dalam": -0.8, "alis_luar": 0.6,
        "alis_rapat": 0.9, "kerut_hidung": 1.0, "mulut_bulat": 1.0,
    })
    assert 'M-7 2 l-4 5' in svg
    assert 'rx="9.0" ry="9.0"' in svg


def test_detail_ekspresi_tidak_diterapkan_pada_wajah_cahaya_sahabat():
    svg = tokoh.orang(500, 1500, wajah="kepergok_panik", wajah_cahaya=True,
                      detail_wajah={"kerut_hidung": 1, "mulut_bulat": 1})
    assert 'fill="#fff8df"' in svg
    assert 'M-7 2 l-4 5' not in svg
    assert 'rx="9.0" ry="9.0"' not in svg


def test_batas_penjaga_bahtera_tidak_dilemahkan():
    from sutradara.rencana.penjaga import SETENGAH_LEBAR
    assert SETENGAH_LEBAR["bahtera"] == 500


def test_variasi_ciri_antar_individu_kerumunan_tidak_memicu_drift_palsu():
    r = _rencana()
    for role in r["peran"]:
        if role["id"] in ("kaum", "pengikut_beriman"):
            role["kolektif"] = True
    shot_awal = r["beat"][1]["shot"][0]
    shot_awal["tokoh"] = [
        {"x": 700, "y": 1500, "peran": "kaum", "kepala": "imamah"},
        {"x": 860, "y": 1500, "peran": "kaum", "kepala": "kain"},
        {"x": 990, "y": 1500, "peran": "pengikut_beriman", "kepala": "kopiah"},
    ]
    shot_lanjut = copy.deepcopy(shot_awal)
    shot_lanjut["tokoh"] = [
        {"x": 710, "y": 1500, "peran": "kaum", "kepala": "kain"},
        {"x": 870, "y": 1500, "peran": "pengikut_beriman", "kepala": "imamah"},
    ]
    r["beat"][1]["shot"] = [shot_awal]
    r["beat"][2]["shot"] = [shot_lanjut]
    assert not any(x.kode == "IDENTITAS_BERUBAH" for x in periksa(r))


def test_identitas_individu_di_dalam_kerumunan_tetap_dijaga_antar_shot():
    r = _rencana()
    for role in r["peran"]:
        if role["id"] == "kaum":
            role["kolektif"] = True
    r["pemeran"] = [{
        "id": "pengejek_01",
        "nama": "Pengejek 01",
        "identitas": {
            "jenis": "pria", "usia": "dewasa", "zaman": "arab_kuno",
            "penutup_kepala": "imamah",
        },
        "saluran_id": "kisah_islami",
    }]
    tokoh_awal = {"x": 700, "y": 1500, "peran": "kaum",
                  "pemeran_id": "pengejek_01", "kepala": "imamah"}
    tokoh_akhir = {**tokoh_awal, "kepala": "kain"}
    awal = copy.deepcopy(r["beat"][1]["shot"][0])
    akhir = copy.deepcopy(awal)
    awal["tokoh"] = [tokoh_awal]
    akhir["tokoh"] = [tokoh_akhir]
    r["beat"][1]["shot"] = [awal]
    r["beat"][2]["shot"] = [akhir]
    temuan = periksa(r)
    assert any(x.kode == "IDENTITAS_BERUBAH" and x.tingkat == "PERIKSA"
               and "pengejek_01" in x.pesan for x in temuan)


def test_tokoh_tunggal_tanpa_peran_kolektif_tetap_diperiksa_dari_kartu_peran():
    r = _rencana()
    shot = r["beat"][0]["shot"][0]
    shot["tokoh"] = [{"x": 500, "y": 1500, "peran": "kaum", "kepala": "kain"}]
    temuan = periksa(r)
    assert any(x.kode == "IDENTITAS_BERUBAH" and x.tingkat == "PERIKSA"
               for x in temuan)
