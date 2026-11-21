import copy
import json
from pathlib import Path

from sutradara import adegan, video
from sutradara.dalil import segmen as SG
from sutradara.gaya import kartu as KT
from sutradara.rencana import periksa

CONTOH = Path(__file__).resolve().parents[1] / "contoh"


def muat(nama):
    return json.loads((CONTOH / nama).read_text(encoding="utf-8"))


def test_potongan_utuh_tanpa_kata_hilang_dan_muat_dua_baris():
    for nama in ("nuh_mengejek.json", "dajjal_dua_sungai.json"):
        for d in muat(nama)["dalil"]:
            if not d.get("teks_ar"):
                continue
            ar, tr = KT.teks_kartu(d)
            pot = SG.potong(ar, tr)
            assert SG.rapikan(" ".join(a for a, _ in pot)) == SG.rapikan(ar)
            assert SG.rapikan(" ".join(t for _, t in pot)) == SG.rapikan(tr)
            assert all(len(SG.baris(a, True)) <= 2 and len(SG.baris(t, False)) <= 2 for a, t in pot)


def test_hud38_dipotong_di_waqaf_dan_kalimat():
    d = muat("nuh_mengejek.json")["dalil"][0]
    pot = SG.potong(d["teks_ar"], d["terjemah"])
    assert pot[0][1].endswith("kapal.") and pot[1][0].rstrip().endswith("ۚ")


def test_kutipan_harus_potongan_persis():
    d = muat("dajjal_dua_sungai.json")["dalil"][0]
    assert SG.kutipan_sah(d["kutipan_ar"], d["teks_ar"]) and SG.kutipan_sah(d["kutipan_id"], d["terjemah"])
    r = muat("dajjal_dua_sungai.json")
    r["dalil"][0]["kutipan_id"] = "bersamanya ada dua sungai yang mengalir deras."  # kalimat karangan
    assert "KUTIPAN_TIDAK_ADA_DI_SUMBER" in {t.kode for t in periksa(r) if t.tingkat == "GAGAL"}


def test_kartu_bergantian_dan_teks_diketik():
    r = muat("nuh_mengejek.json"); dl = video.peta_dalil(r)
    sh = r["beat"][2]["shot"][1]
    pot = KT.potongan(dl["hud38"]); w = KT.rencana_waktu(pot, sh["kartu_dalil"]["mulai"])
    awal, penuh, berikut = (adegan.susun(sh, w[0][0] + 0.3, dalil=dl), adegan.susun(sh, w[0][1] - 0.4, dalil=dl),
                            adegan.susun(sh, w[1][0] + 2.5, dalil=dl))
    assert "kapal." not in awal and "kapal." in penuh       # diketik bertahap
    assert "kapal." not in berikut and "Setiap kali" in berikut  # diganti potongan berikutnya
    assert adegan.durasi(sh, dl) > w[-1][1]                  # durasi otomatis dari waktu baca


def test_kartu_merujuk_dalil_tak_terdaftar_ditolak():
    r = copy.deepcopy(muat("nuh_mengejek.json"))
    r["beat"][2]["shot"][1]["kartu_dalil"]["dalil"] = "tidak_ada"
    assert "KARTU_DALIL" in {t.kode for t in periksa(r)}
