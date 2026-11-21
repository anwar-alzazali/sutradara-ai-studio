import json
from pathlib import Path

from sutradara.rencana.penjaga import periksa


def test_penjaga_menolak_penunggang_buraq():
    rencana = json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = rencana["beat"][0]["shot"][0]
    shot["buraq"] = [{"x": 540, "y": 1300, "penunggang": "tokoh"}]
    temuan = periksa(rencana)
    assert any(t.kode == "PENUNGGANG_BURAQ" and t.tingkat == "GAGAL" for t in temuan)


def test_penjaga_menolak_tokoh_yang_ditandai_menunggang_buraq():
    rencana = json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = rencana["beat"][0]["shot"][0]
    shot["buraq"] = [{"x": 540, "y": 1300}]
    shot["tokoh"] = [{"x": 540, "y": 1200, "naik_di": "buraq"}]
    temuan = periksa(rencana)
    assert any(t.kode == "PENUNGGANG_BURAQ" and t.tingkat == "GAGAL" for t in temuan)

def test_penjaga_menolak_tokoh_di_area_punggung_buraq():
    rencana = json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = rencana["beat"][0]["shot"][0]
    shot["buraq"] = [{"x": 540, "y": 1500, "s": 1.0}]
    shot["tokoh"] = [{"x": 540, "y": 1300}]
    temuan = periksa(rencana)
    assert any(t.kode == "PENUNGGANG_BURAQ" and t.tingkat == "GAGAL" for t in temuan)
