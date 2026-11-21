"""Nilai beranimasi.

Angka mana pun di spesifikasi shot boleh ditulis sebagai keyframe `[[detik, nilai], ...]` (detik relatif awal shot).
Di antara dua keyframe nilai berpindah dengan kurva halus (ease in-out); sebelum keyframe pertama / sesudah terakhir
nilainya ditahan. Contoh: `"jadi": [[0, 0.0], [4, 0.3]]` -> kapal bertambah papan selama 4 detik.

Kunci peristiwa (`guncang`, `hentak`) juga berbentuk `[[detik, kuat], ...]` tetapi BUKAN keyframe, jadi dikecualikan.
"""
from __future__ import annotations

from typing import Any

PERISTIWA = {"guncang", "hentak"}


def adalah_kf(v: Any) -> bool:
    return (isinstance(v, list) and len(v) > 0 and
            all(isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(q, (int, float)) and not isinstance(q, bool) for q in p)
                for p in v))


def _halus(u: float) -> float:
    return u * u * (3 - 2 * u)


def interp(kf: list, t: float) -> float:
    kf = sorted(kf, key=lambda p: p[0])
    if t <= kf[0][0]:
        return float(kf[0][1])
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * _halus(u)
    return float(kf[-1][1])


def pada(spec: Any, t: float) -> Any:
    """Salinan `spec` dengan semua keyframe diganti nilainya pada detik `t`."""
    if isinstance(spec, dict):
        return {k: (v if k in PERISTIWA else pada(v, t)) for k, v in spec.items()}
    if adalah_kf(spec):
        return interp(spec, t)
    if isinstance(spec, list):
        return [pada(v, t) for v in spec]
    return spec
