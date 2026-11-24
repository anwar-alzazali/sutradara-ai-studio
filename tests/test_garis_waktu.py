from types import SimpleNamespace

import pytest

from sutradara import garis_waktu


def _paket_tiruan():
    return SimpleNamespace(
        data_render=lambda rencana: {},
        sisipan_waktu_baca=lambda shot: False,
        waktu_tetap=lambda spec, kunci: False,
    )


def _rencana(potong_di):
    return {
        "suara": {"awal": 0, "jeda": 0},
        "beat": [{
            "narasi": "Pengelana berjalan lalu membangun.",
            "potong_di": potong_di,
            "shot": [
                {"durasi": 2.0, "tokoh": []},
                {"durasi": 2.0, "tokoh": []},
            ],
        }],
    }


def _narasi():
    return {"beat": [[
        [0.0, 0.8, "Pengelana"],
        [0.8, 1.5, "berjalan"],
        [1.5, 1.9, "lalu"],
        [1.9, 2.8, "membangun."],
    ]]}


def _siapkan(monkeypatch):
    monkeypatch.setattr(garis_waktu, "_durasi_rancangan", lambda shot, dl: shot["durasi"])
    monkeypatch.setattr(garis_waktu, "_sisipan_waktu_baca", lambda shot, paket: False)
    monkeypatch.setattr(garis_waktu, "dari_rencana", lambda rencana: _paket_tiruan(), raising=False)


def test_susun_menolak_jumlah_jangkar_eksplisit_yang_tidak_cocok(monkeypatch):
    _siapkan(monkeypatch)
    with pytest.raises(ValueError, match=r"2 kata potong untuk 2 shot berbicara \(harus 1\)"):
        garis_waktu.susun(_rencana(["berjalan", "membangun"]), _narasi())


def test_susun_menerima_satu_jangkar_untuk_dua_shot(monkeypatch):
    _siapkan(monkeypatch)
    hasil = garis_waktu.susun(_rencana(["membangun"]), _narasi())
    assert len(hasil.shot) == 2
    assert hasil.potong[1] == pytest.approx(1.8)
