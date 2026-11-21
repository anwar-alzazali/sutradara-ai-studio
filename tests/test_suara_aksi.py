"""Tes keterlihatan, permukaan, variasi, sumber aksi, dan pembatasan efek diegetik."""
import json
from pathlib import Path

from sutradara.suara import aksi

AKAR = Path(__file__).resolve().parents[1]


def test_tokoh_di_luar_bingkai_tidak_menghasilkan_bunyi():
    shot = {"durasi": 3.0, "depan": False,
            "kamera": {"zoom": 2.0, "x": 1000, "y": 960},
            "tokoh": [{"x": 100, "y": 1400, "gerak": "jalan"}]}
    assert aksi.efek_aksi(shot, 0) == []


def test_tokoh_yang_tertutup_tokoh_depan_tidak_menghasilkan_bunyi():
    shot = {"durasi": 3.0, "depan": False, "tokoh": [
        {"x": 540, "y": 1300, "s": .6, "gerak": "jalan"},
        {"x": 540, "y": 1320, "s": 1.2, "gerak": "berdiri"},
    ]}
    assert aksi.efek_aksi(shot, 0) == []


def test_lapis_depan_menghilangkan_sumber_yang_tertutup():
    shot = {"durasi": 3.0, "tokoh": [
        {"x": 80, "y": 1940, "s": .5, "gerak": "jalan"}
    ]}
    assert aksi.efek_aksi(shot, 0) == []


def test_posisi_dan_ukuran_diambil_dari_keyframe():
    shot = {"durasi": 3.0, "depan": False, "tokoh": [
        {"x": [[0, 200], [3, 900]], "y": 1400,
         "s": [[0, .5], [3, 1.5]], "gerak": "jalan"}
    ]}
    rek = aksi.efek_aksi(shot, 0)
    assert len(rek) >= 4
    assert rek[-1]["pan"] > rek[0]["pan"]
    assert rek[-1]["vol"] > rek[0]["vol"]


def test_keyframe_kamera_dipakai_untuk_menentukan_keterlihatan():
    shot = {"durasi": 3.0, "depan": False,
            "kamera": {"zoom": [[0, 1], [3, 2]], "x": [[0, 540], [3, 1100]], "y": 960},
            "tokoh": [{"x": 100, "y": 1400, "gerak": "jalan"}]}
    rek = aksi.efek_aksi(shot, 0)
    statis = aksi.efek_aksi(
        {"durasi": 3.0, "depan": False, "tokoh": [{"x": 100, "y": 1400, "gerak": "jalan"}]}, 0)
    assert rek and all(r["pan"] < 0 for r in rek)
    assert len(rek) < len(statis)


def test_variasi_ketukan_deterministik_tetapi_tidak_identik():
    shot = {"durasi": 4.0, "depan": False,
            "tokoh": [{"x": 540, "y": 1400, "gerak": "jalan"}]}
    a = aksi.efek_aksi(shot, 0)
    b = aksi.efek_aksi(shot, 0)
    assert a == b
    assert len({r["kecepatan"] for r in a}) > 1


def test_permukaan_memilih_sampel_khusus_bila_sudah_direkam(monkeypatch):
    monkeypatch.setattr(aksi, "_ada", lambda nama: nama.startswith("aksi/"))
    for permukaan, nama in [
        ("pasir", "aksi/langkah_pasir"), ("kayu", "aksi/langkah_kayu"),
        ("air", "aksi/langkah_air"), ("batu", "aksi/langkah_batu_besi"),
    ]:
        shot = {"durasi": 2.0, "depan": False, "tokoh": [
            {"x": 540, "y": 1400, "gerak": "jalan", "permukaan": permukaan}
        ]}
        rek = aksi.efek_aksi(shot, 0)
        assert rek and all(r["berkas"] == nama for r in rek)


def test_palu_di_batu_besi_memakai_rekaman_khusus(monkeypatch):
    monkeypatch.setattr(aksi, "_ada", lambda nama: nama.startswith("aksi/"))
    shot = {"durasi": 2.0, "depan": False, "tokoh": [
        {"x": 540, "y": 1400, "gerak": "palu", "permukaan": "batu_besi"}
    ]}
    rek = aksi.efek_aksi(shot, 0)
    assert rek and all(r["berkas"] == "aksi/palu_batu_besi" for r in rek)


def test_tawa_dan_ejekan_berbunyi_hanya_saat_wajah_terlihat():
    shot = {"durasi": 3.0, "depan": False, "tokoh": [
        {"x": 540, "y": 1400, "gerak": "berdiri",
         "wajah": [[0, "datar"], [1, "tertawa"]]}
    ]}
    rek = aksi.efek_aksi(shot, 0)
    tawa = [r for r in rek if r["sebab"] == "tokoh tertawa/mengejek"]
    assert len(tawa) == 1
    assert tawa[0]["berkas"] == "kerumunan_cemas"  # fallback yang sudah ada


def test_kerumunan_jauh_memakai_ambience_kerumunan():
    shot = {"durasi": 3.0, "depan": False,
            "npc_jauh": {"n": 12, "x0": 200, "x1": 900, "y": 1260}}
    rek = aksi.efek_aksi(shot, 0)
    crowd = next(r for r in rek if r["sebab"] == "kerumunan jauh")
    assert crowd["berkas"] == "kerumunan_cemas" and crowd["loop"]


def test_kabut_keluar_dan_retakan_memiliki_efek_berbeda():
    shot = {"durasi": 3.0, "depan": False,
            "kabut_tanpa_wujud": [{"x": 540, "y": 1300, "retakan": True,
                                    "keluar": [[0, .1], [2, 1.0]]}]}
    rek = aksi.efek_aksi(shot, 0)
    sebab = {r["sebab"]: r["berkas"] for r in rek}
    assert sebab["kabut keluar"] == "dentum_jauh"
    assert sebab["retakan tanah"] == "tanah_retak"


def test_benda_berubah_memiliki_suara_fallback():
    shot = {"durasi": 4.0, "depan": False,
            "benda": [{"jenis": "bahtera", "x": 600, "y": 1235, "s": .5,
                       "jadi": [[0, .1], [3, .6], [4, .6]]}]}
    rek = aksi.efek_aksi(shot, 0)
    assert rek and all(r["sebab"] == "papan bahtera bertambah" for r in rek)
    assert all(r["berkas"] == "satu/palu" for r in rek)


def test_tokoh_diam_tidak_diberi_efek_tanpa_aksi_terdengar():
    shot = {"durasi": 3.0, "depan": False,
            "tokoh": [{"x": 540, "y": 1400, "gerak": "berdiri", "wajah": "datar"}]}
    assert aksi.efek_aksi(shot, 0) == []


def test_batas_ketukan_memilih_tokoh_terlihat_terdekat_bukan_awal_daftar():
    tokoh = [
        {"x": 80 + (i % 8) * 130, "y": 900 + (i // 8) * 160,
         "s": .42, "gerak": "jalan"}
        for i in range(55)
    ]
    rek = aksi.efek_aksi({"durasi": 4.0, "depan": False, "tokoh": tokoh,
                          "benda": [{"jenis": "bahtera", "x": 540, "y": 1235, "s": .5,
                                     "jadi": [[0, .1], [3, .8]]}]}, 0)
    sumber = {int(r["sebab"].split()[1]) for r in rek if r["sebab"].startswith("tokoh ")}
    assert len(rek) <= aksi.MAKS_KETUK_PER_SHOT
    assert len(sumber) == aksi.MAKS_KETUK_PER_SHOT
    assert max(sumber) > 40


def test_contoh_nuh_memiliki_pemalu_terlihat_tanpa_nama_dan_dialog():
    r = json.loads((AKAR / "contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = r["beat"][0]["shot"][0]
    pemalu = [t for t in shot["tokoh"] if t.get("gerak") == "palu"]
    assert len(pemalu) >= 2
    assert all("nama" not in t and "bicara" not in t for t in pemalu)
    assert shot["nur"] and shot["nur"][0]["nama"] == "Nabi Nuh a.s."

def test_gerak_tertawa_tanpa_jadwal_wajah_tetap_berbunyi():
    shot = {"durasi": 3.0, "depan": False, "tokoh": [
        {"x": 540, "y": 1400, "gerak": "tertawa"}
    ]}
    rek = aksi.efek_aksi(shot, 0)
    assert any(r["sebab"] == "tokoh tertawa/mengejek" for r in rek)


def test_prompt_rekaman_dan_workflow_dispatch_saja():
    prompts = json.loads((AKAR / "aset/suara/prompt_efek.json").read_text(encoding="utf-8"))
    target = [p["berkas"] for p in prompts]
    assert len(target) == len(set(target))
    assert all(p["berkas"].startswith("aset/suara/aksi/") and p["berkas"].endswith(".mp3")
               and .5 <= p["durasi"] <= 22 for p in prompts)
    workflow = (AKAR / ".github/workflows/efek.yml").read_text(encoding="utf-8")
    assert "on:\n  workflow_dispatch:" in workflow
    assert not any(line.strip() in {"push:", "pull_request:", "issues:"} for line in workflow.splitlines())
    assert "secrets.ELEVENLABS_API_KEY" in workflow
    assert "if path.exists():" in workflow
    assert "git add aset/suara/aksi" in workflow

def test_perubahan_besar_benda_non_bahtera_mendapat_tekstur():
    shot = {"durasi": 3.0, "depan": False,
            "benda": [{"jenis": "dinding", "x": 540, "y": 1250,
                       "retak": [[0, 0.0], [1.0, 0.6]]}]}
    rek = aksi.efek_aksi(shot, 0)
    assert any(r["sebab"] == "benda berubah: dinding" and r["berkas"] == "tanah_retak" for r in rek)


def test_pemalu_terlihat_dekat_bahtera_menghindari_ketukan_ganda():
    shot = {"durasi": 3.0, "depan": False,
            "benda": [{"jenis": "bahtera", "x": 600, "y": 1235, "s": .56,
                       "jadi": [[0, .1], [2, .6]]}],
            "tokoh": [{"x": 430, "y": 1360, "s": .52, "gerak": "palu"}]}
    rek = aksi.efek_aksi(shot, 0)
    assert any(r["sebab"] == "tokoh 1 palu" for r in rek)
    assert not any(r["sebab"] == "papan bahtera bertambah" for r in rek)


def test_tokoh_berjalan_dekat_bahtera_tidak_menghapus_suara_pembangunan():
    shot = {"durasi": 3.0, "depan": False,
            "benda": [{"jenis": "bahtera", "x": 600, "y": 1235, "s": .56,
                       "jadi": [[0, .1], [2, .6]]}],
            "tokoh": [{"x": 430, "y": 1360, "s": .52, "gerak": "jalan"}]}
    rek = aksi.efek_aksi(shot, 0)
    assert any(r["sebab"] == "papan bahtera bertambah" for r in rek)

def test_tawa_beberapa_kelompok_waktu_tidak_saling_menghapus():
    shot = {"durasi": 4.0, "depan": False, "tokoh": [
        {"x": 300, "y": 1400, "gerak": "berdiri", "wajah": "tertawa"},
        {"x": 800, "y": 1400, "gerak": "berdiri",
         "wajah": [[0, "datar"], [2, "ejek"]]},
    ]}
    rek = aksi.efek_aksi(shot, 0)
    tawa = [r for r in rek if r["sebab"] == "tokoh tertawa/mengejek"]
    assert len(tawa) == 2

def test_wajah_mengejek_yang_persisten_tidak_berbunyi_setiap_pose_berubah():
    shot = {"durasi": 4.0, "depan": False, "tokoh": [
        {"x": 540, "y": 1400, "gerak": [[0, "jalan"], [1.5, "tunjuk"], [2.8, "silang"]],
         "wajah": [[0, "ejek"]]}
    ]}
    rek = aksi.efek_aksi(shot, 0)
    assert len([r for r in rek if r["sebab"] == "tokoh tertawa/mengejek"]) == 1
