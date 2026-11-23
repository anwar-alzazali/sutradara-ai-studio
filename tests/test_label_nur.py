"""Regresi label nabi: nama harus terbaca di depan tokoh dan aman sebagai teks SVG."""
from sutradara.paket_genre.kisah_islami import renderer
from sutradara.paket_genre.kisah_islami.visual import nur


def test_label_nama_diescape_dan_dijaga_di_dalam_batas_kanvas():
    svg = nur.label_nama(12, 1500, "Nabi <Nuh>")

    assert "&lt;Nuh&gt;" in svg
    assert 'class="label-nur"' in svg
    assert 'x="132.0"' in svg


def test_label_nabi_dipisah_dari_pilar_dan_masuk_lapisan_depan():
    hasil = renderer.render_adegan(
        {"tokoh": [], "nur": []},
        {"preset": "senja", "nur": [{"x": 165, "y": 1500, "nama": "Nabi Nuh"}]},
        0.0,
        0.0,
        {},
    )

    assert len(hasil.tengah) == 1
    assert "Nabi Nuh" not in hasil.tengah[0][1]
    assert any("Nabi Nuh" in lapis and 'class="label-nur"' in lapis for lapis in hasil.overlay)
