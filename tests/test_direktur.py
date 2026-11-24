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
    assert kiri["tokoh"][0]["arah"] == "tiga_perempat"
    assert kanan["tokoh"][0]["arah"] == "tiga_perempat"



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


def test_pengejar_aktif_ke_kiri_berada_di_belakang_yang_dikejar():
    naskah = {
        "judul": "Pengejaran ke kiri",
        "inti": "Penjaga mengejar pengelana ke kiri.",
        "dalil": [],
        "beat": [{
            "narasi": "Penjaga mengejar pengelana ke kiri.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Penjaga", "Pengelana"],
        }],
    }
    tokoh = rancang(naskah)["beat"][0]["shot"][0]["tokoh"]
    penjaga = next(t for t in tokoh if t["peran"] == "penjaga")
    pengelana = next(t for t in tokoh if t["peran"] == "pengelana")
    assert penjaga["gerak"] == pengelana["gerak"] == "lari"
    assert penjaga["x"][0][1] > pengelana["x"][0][1]
    assert penjaga["x"][-1][1] < penjaga["x"][0][1]
    assert pengelana["x"][-1][1] < pengelana["x"][0][1]
    assert penjaga["tujuan"] == pengelana["tujuan"] == "tepi:kiri"


def test_arah_tiga_perempat_dikenali_dan_dipakai_bila_disebut_narasi():
    from sutradara.gaya.tokoh import _arah_derajat

    naskah = {
        "judul": "Menghadap serong",
        "inti": "Pengelana menghadap serong tiga perempat ke bahtera.",
        "dalil": [],
        "beat": [{
            "narasi": "Pengelana menghadap serong tiga perempat ke bahtera.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Pengelana"],
        }],
    }
    aktor = rancang(naskah)["beat"][0]["shot"][0]["tokoh"][0]
    assert aktor["arah"] == "tiga_perempat"
    assert _arah_derajat("tiga_perempat", 0) == 45.0
    assert _arah_derajat("tiga_perempat_belakang", 0) == 135.0


def test_gerak_berbalik_menyimpan_jadwal_putaran_badan():
    naskah = {
        "judul": "Pengelana berbalik",
        "inti": "Pengelana berbalik arah lalu kabur ke kiri.",
        "dalil": [],
        "beat": [{
            "narasi": "Pengelana berbalik arah lalu kabur ke kiri.",
            "dalil": [], "kata_kunci": ["berlari"], "suasana": "senja",
            "peran": ["Pengelana"],
        }],
    }
    aktor = rancang(naskah)["beat"][0]["shot"][0]["tokoh"][0]
    assert aktor["tujuan"] == "tepi:kiri"
    assert isinstance(aktor["arah"], list)
    assert aktor["arah"] == [[0.0, "samping"], [3.8 * .34, "depan"], [3.8 * .68, "samping"]]
    assert aktor["balik"] == [[0.0, False], [3.8 * .68, True]]


def test_jadwal_mirror_tubuh_diinterpolasi_halus():
    from sutradara.gaya.tokoh import _balik_pada

    jadwal = [[0.0, False], [2.5, True]]
    assert _balik_pada(jadwal, 0.0) is False
    assert _balik_pada(jadwal, 2.49) is False
    assert _balik_pada(jadwal, 2.5) is True
    assert _balik_pada(jadwal, 3.8) is True


def test_memori_arah_perjalanan_dipertahankan_antar_beat():
    naskah = {
        "judul": "Perjalanan berlanjut", "inti": "Pengelana melintasi jalan.", "dalil": [],
        "beat": [
            {"narasi": "Pengelana berjalan ke kiri.", "dalil": [], "kata_kunci": [],
             "suasana": "senja", "peran": ["Pengelana"]},
            {"narasi": "Pengelana terus berjalan menyusuri jalan.", "dalil": [],
             "kata_kunci": [], "suasana": "senja", "peran": ["Pengelana"]},
        ],
    }
    hasil = rancang(naskah)
    pertama = hasil["beat"][0]["shot"][0]["tokoh"][0]
    kedua = hasil["beat"][1]["shot"][0]["tokoh"][0]
    assert pertama["lintasan"][-1][1] < pertama["lintasan"][0][1]
    assert kedua["lintasan"][-1][1] < kedua["lintasan"][0][1]


def test_kembali_membalik_memori_dan_arah_eksplisit_tidak_dibalik_dua_kali():
    naskah = {
        "judul": "Kembali", "inti": "Pengelana melakukan perjalanan.", "dalil": [],
        "beat": [
            {"narasi": "Pengelana berjalan ke kiri.", "dalil": [], "kata_kunci": [],
             "suasana": "senja", "peran": ["Pengelana"]},
            {"narasi": "Pengelana berjalan kembali.", "dalil": [], "kata_kunci": [],
             "suasana": "senja", "peran": ["Pengelana"]},
            {"narasi": "Pengelana berjalan kembali ke kiri.", "dalil": [], "kata_kunci": [],
             "suasana": "senja", "peran": ["Pengelana"]},
        ],
    }
    hasil = rancang(naskah)
    arah = []
    for beat in hasil["beat"]:
        aktor = beat["shot"][0]["tokoh"][0]
        arah.append((aktor["lintasan"][-1][1] > aktor["lintasan"][0][1]) -
                    (aktor["lintasan"][-1][1] < aktor["lintasan"][0][1]))
    assert arah == [-1, 1, -1]


def test_judul_hook_hanya_muncul_di_shot_pembuka_beat_hook():
    naskah = {
        "judul": "Bahtera dan seruan",
        "inti": "Nabi Nuh membangun bahtera lalu menyeru kaumnya.",
        "dalil": [],
        "beat": [
            {
                "narasi": "Pengikut beriman membangun bahtera.",
                "dalil": [], "kata_kunci": ["membangun"], "suasana": "senja",
                "peran": ["Pengikut beriman"],
            },
            {
                "narasi": "Nabi Nuh menyeru kaum penentang.",
                "dalil": [], "kata_kunci": [], "suasana": "senja",
                "peran": ["Nabi Nuh", "Kaum penentang"],
                "dialog": [{"pembicara": "Nabi Nuh", "penjawab": "Kaum penentang",
                            "ucapan": "Dengarkan seruanku."}],
            },
        ],
    }
    hasil = rancang(naskah)
    lokasi_judul = [
        (i, j)
        for i, beat in enumerate(hasil["beat"])
        for j, shot in enumerate(beat["shot"])
        if shot.get("teks", {}).get("judul")
    ]
    assert lokasi_judul == [(0, 0)]
    assert hasil["beat"][0]["shot"][0]["teks"]["judul"] == hasil["hook"]["teks"]


def test_interaksi_menginferensikan_pasangan_tanpa_nama_lawan_eksplisit():
    naskah = {
        "judul": "Memberi air",
        "inti": "Pengelana memberikan air kepada musafir.",
        "dalil": [],
        "beat": [{
            "narasi": "Pengelana memberikan air kepada orang di depannya.",
            "dalil": [], "kata_kunci": [], "suasana": "senja",
            "peran": ["Pengelana", "Musafir", "Pedagang"],
        }],
    }
    shot = rancang(naskah)["beat"][0]["shot"][0]
    pengelana = next(t for t in shot["tokoh"] if t["peran"] == "pengelana")
    musafir = next(t for t in shot["tokoh"] if t["peran"] == "musafir")
    pedagang = next(t for t in shot["tokoh"] if t["peran"] == "pedagang")
    assert (pengelana["x"], musafir["x"]) == (380, 820)
    assert pengelana["arah"] == musafir["arah"] == "samping"
    assert pedagang["x"] not in {pengelana["x"], musafir["x"]}


def test_interaksi_tanpa_nama_tokoh_hanya_diinferensikan_jika_tepat_dua_peran():
    from sutradara.paket_genre.kisah_islami.sutradara import _pasangan_interaksi

    peta = {
        "a": {"nama": "Tokoh A"},
        "b": {"nama": "Tokoh B"},
        "c": {"nama": "Tokoh C"},
    }
    assert _pasangan_interaksi("Seseorang menyapa orang lain.", ["a", "b"], peta) == ("a", "b")
    assert _pasangan_interaksi("Seseorang menyapa orang lain.", ["a", "b", "c"], peta) is None


def test_status_bahtera_tidak_berubah_hanya_karena_indeks_beat():
    from sutradara.paket_genre.kisah_islami.sutradara import _keadaan

    awal = _keadaan("bahtera", ["rangka", "dibangun", "badai"], "Tidak ada pembangunan.", 0, 2)
    setelah_beat_netral = _keadaan("bahtera", ["rangka", "dibangun", "badai"], "Tidak ada pembangunan.", 9, 10)
    assert awal == setelah_beat_netral
    assert awal[0] == "rangka"
    assert awal[1]["jadi"] == .18


def test_reducer_bahtera_hanya_berubah_oleh_peristiwa_pembangunan():
    from sutradara.paket_genre.kisah_islami.sutradara import (
        _keadaan, _reduksi_keadaan_benda,
    )

    status = {}
    netral = {"aksi": "jalan", "sasaran": None, "perubahan_keadaan": None}
    _reduksi_keadaan_benda(status, "bahtera", netral)
    assert _keadaan("bahtera", [], "Berjalan.", 5, 6, status)[1]["jadi"] == .18

    bangun = {"aksi": "membangun", "sasaran": "bahtera", "perubahan_keadaan": None}
    _reduksi_keadaan_benda(status, "bahtera", bangun)
    snapshot = _keadaan("bahtera", [], "Beat netral sesudahnya.", 0, 1, status)
    assert snapshot[0] == "dibangun"
    assert snapshot[1]["jadi"] == .55

    _reduksi_keadaan_benda(status, "bahtera", netral)
    assert _keadaan("bahtera", [], "Masih beat netral.", 20, 21, status) == snapshot


def test_reducer_dinding_tidak_menyamakan_penggalian_dengan_terbuka():
    from sutradara.paket_genre.kisah_islami.sutradara import (
        _keadaan, _reduksi_keadaan_benda,
    )

    status = {}
    gali = {"aksi": "menggali", "sasaran": "dinding", "perubahan_keadaan": None}
    _reduksi_keadaan_benda(status, "dinding_yajuj", gali)
    keadaan = _keadaan("dinding_yajuj", ["utuh", "dilubangi", "terbuka"],
                       "Beat tanpa aksi.", 8, 9, status)
    assert keadaan[0] == "dilubangi"
    assert keadaan[1]["lubang"] == .25

    buka = {"aksi": "terbuka", "sasaran": "dinding",
            "perubahan_keadaan": {"objek": "dinding", "keadaan": "terbuka"}}
    _reduksi_keadaan_benda(status, "dinding_yajuj", buka)
    terbuka = _keadaan("dinding_yajuj", [], "Beat netral.", 0, 1, status)
    assert terbuka[0] == "terbuka"
    assert terbuka[1]["lubang"] == 1.0


def test_kota_tidak_runtuh_hanya_karena_angin_disebut():
    from sutradara.paket_genre.kisah_islami.sutradara import (
        _keadaan, _reduksi_keadaan_benda,
    )

    status = {}
    sebelum = _keadaan("kota_kuno", ["awal", "peristiwa"], "Angin datang.", 7, 8, status)
    assert sebelum[0] == "angin"
    assert sebelum[1]["runtuh"] == 0.0

    runtuh = {"aksi": "runtuh", "sasaran": "kota",
              "perubahan_keadaan": {"objek": "kota", "keadaan": "runtuh"}}
    _reduksi_keadaan_benda(status, "kota_kuno", runtuh)
    sesudah = _keadaan("kota_kuno", ["awal", "peristiwa"], "Angin datang.", 0, 1, status)
    assert sesudah[1]["runtuh"] == .7


def test_parser_mengenali_pembangunan_dan_penyelesaian_bahtera():
    from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa
    from sutradara.paket_genre.kisah_islami.sutradara import _keadaan, _reduksi_keadaan_benda

    status = {}
    for narasi in ("Kaum membangun bahtera.", "Pembangunan bahtera selesai."):
        peristiwa = analisis_peristiwa(narasi, ["kaum"])
        assert peristiwa
        _reduksi_keadaan_benda(status, "bahtera", peristiwa[0])

    snapshot = _keadaan("bahtera", [], "Beat tanpa perubahan.", 0, 1, status)
    assert snapshot[0] == "jadi"
    assert snapshot[1]["jadi"] == 1.0


def test_parser_mengenali_penggalian_dinding_tanpa_menganggapnya_terbuka():
    from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa
    from sutradara.paket_genre.kisah_islami.sutradara import _keadaan, _reduksi_keadaan_benda

    peristiwa = analisis_peristiwa("Mereka menggali dinding.", ["mereka"])
    assert peristiwa and peristiwa[0]["sasaran"] == "dinding"
    status = {}
    _reduksi_keadaan_benda(status, "dinding_yajuj", peristiwa[0])
    snapshot = _keadaan("dinding_yajuj", [], "Tidak ada perubahan.", 0, 1, status)
    assert snapshot[0] == "dilubangi"
    assert snapshot[1]["lubang"] == .25


def test_parser_mengenali_runtuhnya_kota_sebagai_perubahan_eksplisit():
    from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa
    from sutradara.paket_genre.kisah_islami.sutradara import _keadaan, _reduksi_keadaan_benda

    peristiwa = analisis_peristiwa("Kota itu runtuh.", ["penduduk"])
    assert peristiwa and peristiwa[0]["perubahan_keadaan"] == {
        "objek": "kota", "keadaan": "runtuh"
    }
    status = {}
    _reduksi_keadaan_benda(status, "kota_kuno", peristiwa[0])
    snapshot = _keadaan("kota_kuno", [], "Angin datang.", 0, 1, status)
    assert snapshot[1]["runtuh"] == .7


def test_badai_tidak_menyelesaikan_bahtera_tanpa_peristiwa_pembangunan():
    from sutradara.paket_genre.kisah_islami.sutradara import _keadaan

    keadaan, objek = _keadaan("bahtera", [], "Badai dan gelombang datang.", 0, 1, {})
    assert keadaan == "badai"
    assert objek["jadi"] == .18
    assert objek["darat"] is False


def test_naskah_nuh_menghasilkan_peristiwa_pembangunan_bahtera_dari_teks_asli():
    from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa
    from sutradara.paket_genre.kisah_islami.sutradara import _keadaan, _reduksi_keadaan_benda

    naskah = json.loads((AKAR / "naskah" / "nuh.json").read_text(encoding="utf-8-sig"))
    status = {}
    peristiwa_terdeteksi = []
    for indeks, beat in enumerate(naskah["beat"]):
        peristiwa = analisis_peristiwa(beat["narasi"], beat.get("peran", []), indeks)
        peristiwa_terdeteksi.extend(peristiwa)
        for item in peristiwa:
            _reduksi_keadaan_benda(status, "bahtera", item)

    assert any(p["aksi"] == "membangun" and p["sasaran"] == "bahtera"
               for p in peristiwa_terdeteksi)
    keadaan, objek = _keadaan("bahtera", [], "Beat setelah pembangunan.", 0, 1, status)
    assert keadaan == "dibangun"
    assert objek["jadi"] == .55


def test_naskah_hud_tidak_mengubah_angin_membinasakan_menjadi_runtuhnya_kota():
    from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa
    from sutradara.paket_genre.kisah_islami.sutradara import _keadaan, _reduksi_keadaan_benda

    naskah = json.loads((AKAR / "naskah" / "hud.json").read_text(encoding="utf-8-sig"))
    status = {}
    for indeks, beat in enumerate(naskah["beat"]):
        for item in analisis_peristiwa(beat["narasi"], beat.get("peran", []), indeks):
            _reduksi_keadaan_benda(status, "kota_kuno", item)

    keadaan, objek = _keadaan("kota_kuno", ["awal", "peristiwa"],
                              "Angin dahsyat membinasakan kaum.", 0, 1, status)
    assert keadaan == "angin"
    assert objek["runtuh"] == 0.0


def test_parser_mengabaikan_aksi_yang_dinegasikan_dengan_kata_bantu():
    from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa

    assert analisis_peristiwa("Kaum tidak akan membangun bahtera.") == []
    assert analisis_peristiwa("Dinding belum juga terbuka.") == []
    assert analisis_peristiwa("Mereka tidak berhasil meruntuhkan kota.") == []
    assert analisis_peristiwa("Kaum membangun bahtera.")


def test_alur_sutradara_nuh_mempertahankan_status_bahtera_dari_peristiwa():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang as rancang_kisah

    naskah = json.loads((AKAR / "naskah" / "nuh.json").read_text(encoding="utf-8-sig"))
    rencana, _ = rancang_kisah(naskah)
    beat_pembangunan = rencana["beat"][1]
    assert beat_pembangunan["keadaan"] == "dibangun"
    assert any(p["aksi"] == "membangun" and p["sasaran"] == "bahtera"
               for p in beat_pembangunan["peristiwa"])


def test_alur_sutradara_hud_tidak_mengarang_status_runtuh_kota():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang as rancang_kisah

    naskah = json.loads((AKAR / "naskah" / "hud.json").read_text(encoding="utf-8-sig"))
    rencana, _ = rancang_kisah(naskah)
    beat_azab = rencana["beat"][-1]
    assert beat_azab["keadaan"] == "angin"
    assert not any((p.get("perubahan_keadaan") or {}).get("objek") in {
        "kota", "permukiman", "kota_kuno"
    } and (p.get("perubahan_keadaan") or {}).get("keadaan") == "runtuh"
                   for p in beat_azab["peristiwa"])
