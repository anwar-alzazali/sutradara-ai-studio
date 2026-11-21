from sutradara.dalil.quran import QuranBertingkat, QuranFoundation


def test_none_eksplisit_melewati_klien_quran_berkunci():
    cadangan = object()
    quran = QuranBertingkat(None, cadangan)
    assert quran.utama is None
    assert quran.cadangan is cadangan


def test_tanpa_argumen_tetap_memakai_klien_quran_bawaan():
    quran = QuranBertingkat(cadangan=object())
    assert isinstance(quran.utama, QuranFoundation)
