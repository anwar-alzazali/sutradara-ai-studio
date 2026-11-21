"""Ukur overhead tekstur tanah lewat Chromium pada shot Nuh dan Dabbah."""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
import sys
import tempfile

AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR))

from sutradara import adegan
from sutradara.gaya import dasar
from sutradara.render import peramban

OUT = Path("keluaran-bukti/tahap-b")
OUT.mkdir(parents=True, exist_ok=True)


def ukur(pg, nama: str, shot: dict, tekstur: bool, frames: int = 36) -> float:
    spec = dict(shot)
    if not tekstur:
        spec["permukaan_tanah"] = "tanpa"
    mulai = time.perf_counter()
    for i in range(frames):
        # t berubah seperti render sungguhan; pola tanah tetap harus identik.
        svg = adegan.susun(spec, i / 12)
        pg.evaluate("s => { document.getElementById('k').innerHTML = s; }", svg)
        if i == 0:
            pg.evaluate("document.fonts.ready")
        pg.screenshot(type="jpeg", quality=88)
    return time.perf_counter() - mulai


def main():
    nuh = json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    dabbah = json.loads(Path("contoh/dabbah_dhuha.json").read_text(encoding="utf-8"))
    sampel = {
        "Nuh": nuh["beat"][0]["shot"][0],
        "Dabbah": dabbah["beat"][1]["shot"][0],
    }
    hasil = {}
    with tempfile.TemporaryDirectory() as tmp, peramban() as pg:
        halaman = Path(tmp) / "ukur.html"
        halaman.write_text(dasar.html('<div id="k"></div>'), encoding="utf-8")
        pg.goto(halaman.as_uri())
        for nama, shot in sampel.items():
            # Pemanasan kedua jalur, lalu urutan dibalik tiap putaran untuk mengurangi bias urutan.
            ukur(pg, nama, shot, False, frames=3)
            ukur(pg, nama, shot, True, frames=3)
            sampel_tanpa, sampel_dengan = [], []
            for putaran in range(3):
                urutan = (False, True) if putaran % 2 == 0 else (True, False)
                for tekstur in urutan:
                    durasi = ukur(pg, nama, shot, tekstur)
                    (sampel_dengan if tekstur else sampel_tanpa).append(durasi)
            tanpa = statistics.median(sampel_tanpa)
            dengan = statistics.median(sampel_dengan)
            hasil[nama] = {
                "frames_per_mode_per_round": 36,
                "rounds_per_mode": 3,
                "tanpa_tekstur_seconds_samples": [round(x, 3) for x in sampel_tanpa],
                "dengan_tekstur_seconds_samples": [round(x, 3) for x in sampel_dengan],
                "tanpa_tekstur_median_seconds": round(tanpa, 3),
                "dengan_tekstur_median_seconds": round(dengan, 3),
                "tambahan_median_seconds": round(dengan - tanpa, 3),
                "overhead_median_percent": round((dengan / tanpa - 1) * 100, 2) if tanpa else None,
                "tambahan_median_ms_per_frame": round((dengan - tanpa) * 1000 / 36, 2),
            }
    laporan = {
        "metode": "Chromium yang sama, 3 putaran per mode, 36 frame per putaran, kualitas JPEG 88; urutan kondisi bergantian; mencakup susun SVG dan screenshot",
        "catatan": "Median CI lebih tahan terhadap noise, tetapi tetap dipengaruhi beban runner dan bukan jaminan perangkat pengguna.",
        "hasil": hasil,
    }
    tujuan = OUT / "benchmark-tekstur.json"
    tujuan.write_text(json.dumps(laporan, ensure_ascii=False, indent=2), encoding="utf-8")
    print("BENCHMARK_TEKSTUR_TANAH", json.dumps(laporan, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
