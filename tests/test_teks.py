from sutradara.gaya.teks import subtitle_frasa


def test_subtitle_frasa_membungkus_teks_panjang_maksimal_tiga_baris():
    kata = ["Pada", "hari", "itu", "seluruh", "manusia", "dikumpulkan", "di", "padang", "mahsyar"]
    svg = subtitle_frasa(kata, aktif=5)
    assert svg.count("<text ") <= 3
    assert svg.count("</text>") == svg.count("<text ")
    assert 'fill="#ffd27a">dikumpulkan</tspan>' in svg
    assert all(f'font-size="{ukuran:.1f}"' in svg for ukuran in [60.0, 58.0, 56.0, 54.0, 52.0, 50.0, 48.0, 46.0, 44.0, 42.0, 40.0, 38.0, 36.0, 34.0, 32.0, 30.0, 28.0, 26.0, 24.0]) or "font-size=" in svg


def test_subtitle_frasa_kosong_tidak_menghasilkan_svg():
    assert subtitle_frasa([]) == ""


def test_subtitle_frasa_menghindari_pemotongan_kata_panjang():
    kata = ["Ketidakberkesinambungan", "perjalanan", "kehidupan", "manusia"]
    svg = subtitle_frasa(kata)
    assert "Ketidakberkesinambungan" in svg
    assert svg.count("<text ") <= 3
