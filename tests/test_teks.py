from sutradara.gaya.teks import subtitle, subtitle_frasa


def test_subtitle_manual_membungkus_teks_panjang():
    svg = subtitle("Pengikut beriman membangun bahtera kaum penentang berdiri di seberang")
    assert svg.count("<text ") >= 2
    assert svg.count("<text ") <= 3
    assert "Pengikut" in svg and "seberang" in svg


def test_subtitle_manual_mempertahankan_sorotan():
    svg = subtitle("Nabi Nuh menyeru kaumnya", sorot="Nuh")
    assert '<tspan fill="#ffd27a">Nuh</tspan>' in svg


def test_subtitle_frasa_membungkus_teks_panjang_maksimal_tiga_baris():
    kata = ["Pada", "hari", "itu", "seluruh", "manusia", "dikumpulkan", "di", "padang", "mahsyar"]
    svg = subtitle_frasa(kata, aktif=5)
    assert svg.count("<text ") <= 3
    assert svg.count("</text>") == svg.count("<text ")
    assert 'fill="#ffd27a">dikumpulkan</tspan>' in svg


def test_subtitle_frasa_kosong_tidak_menghasilkan_svg():
    assert subtitle_frasa([]) == ""


def test_subtitle_frasa_menghindari_pemotongan_kata_panjang():
    kata = ["Ketidakberkesinambungan", "perjalanan", "kehidupan", "manusia"]
    svg = subtitle_frasa(kata)
    assert "Ketidakberkesinambungan" in svg
    assert svg.count("<text ") <= 3
