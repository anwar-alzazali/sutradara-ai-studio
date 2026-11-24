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
    keringat = render({"aksi": "berkeringat", "sasaran": "keringat"})

    assert 'class="peristiwa-kerumunan"' in kerumunan
    assert 'class="peristiwa-keringat"' in keringat


def test_tenggelam_tidak_disalahgambarkan_sebagai_keringat():
    visual = render({"aksi": "tenggelam", "sasaran": "keringat"})

    assert visual == ""
    assert 'peristiwa-keringat' not in visual


def test_rencana_menyertakan_peristiwa_yang_menjadi_dasar_visual():
    naskah = {
        "judul": "Kebangkitan",
        "inti": "Bumi putih kemerahan, rata, dengan tanah terbelah dan manusia bangkit.",
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


def test_frasa_mahyar_menghasilkan_peristiwa_dan_visual_yang_relevan():
    from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa

    tanah = analisis_peristiwa("Tanah di atasmu terbelah.", ["kamu"])
    matahari = analisis_peristiwa("Matahari… didekatkan.", ["kamu"])
    manusia = analisis_peristiwa("Seluruh manusia, dari yang pertama sampai yang terakhir.", ["manusia"])
    keringat = analisis_peristiwa("Manusia berkeringat.", ["manusia"])
    pelarian = analisis_peristiwa("Seseorang lari dari saudaranya.", ["seseorang"])

    assert render(tanah[0])
    assert render(matahari[0])
    assert render(manusia[0])
    assert render(keringat[0])
    assert render(pelarian[0])
