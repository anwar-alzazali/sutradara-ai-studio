from sutradara.paket_genre.kisah_islami.sutradara import _inti, rancang
from sutradara.paket_genre.kisah_islami.visual.peristiwa import render


def test_naskah_padang_tidak_dipaksa_ke_kota_atau_kapal():
    inti, _, _ = _inti({}, "Bumi putih kemerahan, rata, tanpa satu pun tanda.")

    assert inti == "padang"


def test_visual_peristiwa_bumi_terbelah_dan_matahari_didekatkan():
    bumi = render({"aksi": "terbelah", "sasaran": "bumi"})
    matahari = render({"aksi": "mendekat", "sasaran": "matahari"})

    assert 'class="peristiwa-bumi-terbelah"' in bumi
    assert 'class="peristiwa-matahari-dekat"' in matahari


def test_visual_peristiwa_kerumunan_dan_keringat():
    kerumunan = render({"aksi": "berkumpul", "sasaran": "kerumunan"})
    keringat = render({"aksi": "tenggelam", "sasaran": "keringat"})

    assert 'class="peristiwa-kerumunan"' in kerumunan
    assert 'class="peristiwa-keringat"' in keringat


def test_rencana_menyertakan_peristiwa_yang_menjadi_dasar_visual():
    naskah = {
        "judul": "Kebangkitan",
        "inti": "Tanah terbelah dan manusia bangkit.",
        "dalil": [],
        "beat": [
            {"narasi": "Tanah di atasmu terbelah.", "peran": ["kamu"], "dalil": []},
            {"narasi": "Kamu bangkit, tanpa alas kaki.", "peran": ["kamu"], "dalil": []},
            {"narasi": "Matahari didekatkan.", "peran": ["kamu"], "dalil": []},
        ],
    }

    hasil, _ = rancang(naskah)

    assert hasil["visual_inti"]["benda"] == "padang"
    assert hasil["beat"][0]["peristiwa"][0]["aksi"] == "terbelah"
    assert hasil["beat"][0]["shot"][0]["peristiwa_visual"]
    assert hasil["beat"][1]["peristiwa"][0]["aksi"] == "bangkit"
    assert hasil["beat"][2]["peristiwa"][0]["sasaran"] == "matahari"
