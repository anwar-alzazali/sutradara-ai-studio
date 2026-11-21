"""Komponen visual akhir zaman yang dapat dipakai ulang."""
from __future__ import annotations
import math

def buraq(x: float, y: float, s: float = 1.0, *, t: float = 0.0) -> str:
    """Hewan putih berkaki empat; tanpa sayap, wajah manusia, atau penunggang."""
    langkah = math.sin(t * 2.2) * 24
    return (f'<g class="buraq" transform="translate({x:.1f},{y:.1f}) scale({s})">'
            '<ellipse cx="0" cy="4" rx="112" ry="13" fill="#000" opacity=".22"/>'
            '<path d="M-92 -118 Q-130 -190 -76 -230 Q-30 -255 42 -218 L88 -166 Q105 -116 64 -78 L-62 -76Z" fill="#f7f4e9" stroke="#b9b5aa" stroke-width="5"/>'
            '<path d="M42 -212 Q74 -286 128 -270 Q153 -245 120 -198 L92 -150Z" fill="#f7f4e9" stroke="#b9b5aa" stroke-width="5"/>'
            '<path d="M112 -264 Q94 -318 70 -302 L83 -260 M128 -263 Q158 -306 169 -284 L145 -250" fill="#f7f4e9" stroke="#b9b5aa" stroke-width="5"/>'
            f'<path d="M-60 -85 L{-72+langkah:.1f} -8 L{-92+langkah:.1f} 0 M-12 -82 L{-2-langkah:.1f} -12 L{-4-langkah:.1f} 0 M42 -92 L{52+langkah:.1f} -10 L{54+langkah:.1f} 0 M70 -125 L{82-langkah:.1f} -12 L{84-langkah:.1f} 0" fill="none" stroke="#e8e3d7" stroke-width="17" stroke-linecap="round"/>'
            '<path d="M-92 -150 Q-150 -170 -158 -122 Q-142 -110 -105 -124" fill="none" stroke="#d9d3c6" stroke-width="12" stroke-linecap="round"/>'
            '<circle cx="142" cy="-235" r="4" fill="#51483f"/></g>')

def dinding_yajuj(x: float, y: float, s: float = 1.0, *, lubang: float = 0.0) -> str:
    """Tembok raksasa dari balok besi yang dicor tembaga (QS Al-Kahfi 96).

    Jauh lebih tinggi dari manusia (puncaknya keluar bingkai pada skala biasa) dan
    selebar lembah, supaya penggali tampak kecil di kakinya. Lubang ada di dasar,
    setinggi tangan penggali, dan menembus ketebalan dinding.
    """
    u = max(0.0, min(1.0, float(lubang)))
    rx = 8 + 178 * u
    ry = 7 + 112 * u
    L, T = 640, 1500  # setengah lebar, tinggi
    # Bidang besi padat; tidak memakai jeruji, kisi, atau batang vertikal penuh.
    dinding = f'M-{L} 0 L-{L} -{T} L{L} -{T} L{L} 0Z'
    lapis = range(90, T, 120)
    sambungan = ''.join(
        f'<path d="M-{L-20} -{yy} H{L-20}" stroke="#202a30" stroke-width="6" opacity=".42"/>'
        for yy in lapis
    )
    # Sambungan balok pendek berselang-seling (susunan bata besi, bukan kisi).
    balok = ''.join(
        f'<path d="M{xx + (110 if i % 2 else 0)} -{yy} v-120" stroke="#202a30" '
        f'stroke-width="5" opacity=".3"/>'
        for i, yy in enumerate(lapis) for xx in range(-L + 110, L - 60, 220)
    )
    lapis_tembaga = (
        f'<path d="M-{L} -18 H{L}" fill="none" stroke="#a95f32" stroke-width="18"/>'
        + ''.join(f'<path d="M-{L} -{yy} H{L}" fill="none" stroke="#c77b43" '
                  f'stroke-width="12" opacity=".75"/>' for yy in (450, 930, 1410))
        + f'<path d="M-{L-30} -{T-60} H{L-30}" fill="none" stroke="#e4a36a" stroke-width="6" opacity=".5"/>'
    )
    lubang_dinding = (
        f'<ellipse cx="0" cy="-178" rx="{rx:.1f}" ry="{ry:.1f}" '
        'fill="#100d0b" stroke="#c77b43" stroke-width="18"/>'
        f'<ellipse cx="0" cy="-178" rx="{max(1, rx-13):.1f}" ry="{max(1, ry-13):.1f}" '
        'fill="#050505"/>'
    )
    return (f'<g class="dinding-yajuj" transform="translate({x:.1f},{y:.1f}) scale({s})">'
            f'<path d="{dinding}" fill="#59636a" stroke="#252d32" stroke-width="22"/>'
            + sambungan + balok + lapis_tembaga + lubang_dinding + '</g>')

def danau_surut(x: float, y: float, s: float = 1.0, *, surut: float = 0.0) -> str:
    """Danau menyusut menuju garis air tipis."""
    u=max(0.0,min(1.0,float(surut))); h=100*(1-u)+5
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})"><path d="M-420 0 Q-250 {-h:.1f} 0 0 Q250 {-h:.1f} 420 0 Q250 {h*.35:.1f} 0 18 Q-250 {h*.35:.1f} -420 0Z" fill="#5ba6c7" opacity=".9"/>'
            f'<path d="M-360 {-h*.45:.1f} Q0 {-h:.1f} 360 {-h*.45:.1f}" stroke="#d9f4ff" stroke-width="7" fill="none"/></g>')

def tanda_wajah(x: float, y: float, s: float = 1.0) -> str:
    """Tanda abstrak berlabel ilustrasi, bukan rincian hadis."""
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})"><path d="M-26 -8 Q0 -34 26 -8 Q0 12 -26 -8Z" fill="none" stroke="#c34b35" stroke-width="7" opacity=".8"/>'
            '<text x="0" y="48" text-anchor="middle" font-size="18" fill="#fff0d0">ILUSTRASI TANDA</text></g>')
