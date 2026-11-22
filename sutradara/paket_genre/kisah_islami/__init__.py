"""Paket genre Kisah Islami: aturan, skema, data, dan komponen domain."""
from sutradara.genre import PaketGenre
from .adaptasi import adaptasi_shot,data_render
from .penjaga import periksa_khusus
from .renderer import durasi_shot,render_adegan
from .skema import SKEMA_TAMBAHAN
from .visual import akhir_zaman,benda,dajjal,kartu,malaikat,makhluk,nur

def buat_paket():
    return PaketGenre(nama="kisah_islami",validator=periksa_khusus,renderer_adegan=render_adegan,adaptasi_shot=adaptasi_shot,durasi_shot=durasi_shot,data_render=data_render,skema_tambahan=SKEMA_TAMBAHAN,
      komponen={"nur.pilar":nur.pilar,"kartu_dalil.potongan":kartu.potongan,"kartu_dalil.durasi_total":kartu.durasi_total,"malaikat.berkas":malaikat.berkas,"makhluk.kabut_tanpa_wujud":makhluk.kabut_tanpa_wujud,"makhluk.retakan":makhluk.retakan,"dajjal.sosok":dajjal.sosok,"dajjal.belakang":dajjal.belakang,"akhir_zaman.buraq":akhir_zaman.buraq,"akhir_zaman.dinding_yajuj":akhir_zaman.dinding_yajuj,"akhir_zaman.danau_surut":akhir_zaman.danau_surut,"akhir_zaman.tanda_wajah":akhir_zaman.tanda_wajah,"benda.bahtera":benda.bahtera,"benda.sungai":benda.sungai,"kartu_dalil.kartu":kartu.kartu},
      modul_dalil="sutradara.paket_genre.kisah_islami.dalil",panduan_gaya="sutradara/paket_genre/kisah_islami/PANDUAN_GAYA.md",resep="sutradara/paket_genre/kisah_islami/RESEP_SUTRADARA.md",
      bawaan={"genre_lama":"kisah_islami","kepala_tokoh_pria":"imamah","kepala_tokoh_wanita":"kerudung","bacaan_arab_tts":False,"terjemah_kartu_utuh":True})
