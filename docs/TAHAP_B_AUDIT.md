# Audit Tahap B — siap ditinjau

**Status implementasi:** seluruh 8 area Tahap B sudah memiliki implementasi, tes, dan/atau bukti render sesuai cakupan di bawah. Tidak ada pekerjaan fitur Tahap B yang sengaja ditinggalkan.
**Pull request:** [PR #18](https://github.com/anwar-alzazali/sutradara-ai-studio/pull/18)
**Bukti visual:** cabang `bukti`, direktori [`tahap-b/`](https://github.com/anwar-alzazali/sutradara-ai-studio/tree/bukti/tahap-b).
**CI:** gunakan status check pada HEAD PR terbaru; workflow menguji tes lengkap, render Nuh, tekstur tanah, benchmark paralel, lembar kontak, dan verifikasi dalil Ya'juj.

| Poin | Hasil implementasi dan bukti | Tes / verifikasi |
|---|---|---|
| 1. Arah tokoh depan/samping/belakang | Transisi arah smoothstep; tampilan profil dan belakang tersedia pada panel tokoh | Tes transisi arah, profil, dan belakang pada `test_akhir_zaman.py` |
| 2. Ragam usia, zaman, dan perempuan | Anak/dewasa/lansia; busana Arab kuno/Mesir kuno/umum; tokoh perempuan berkerudung. Panel perempuan, anak Mesir kuno, dan lansia ada pada lembar kontak | Tes anatomi/variasi tokoh dan render contoh |
| 3. Dajjal desain B dari belakang | Jubah, punggung, gerak berjalan, dan pembukaan lengan terjadwal; lembar kontak menunjukkan komposisi air/api dan tokoh dari belakang | Tes tampak belakang tanpa wajah depan, gerak jubah, lengan terjadwal, dan SVG |
| 4. Ya'juj Ma'juj | Dinding berlubang, proses terbuka, manusia turun dari tempat tinggi, dan danau surut. Dalil QS Al-Anbiya 96 dan HR. Tirmidzi 2240 diverifikasi workflow tanpa temuan | Tes lubang membesar, danau menyusut, tokoh manusia biasa; artefak verifikasi dalil |
| 5. Buraq dan larangan penunggang | Buraq putih berkaki empat, tanpa sayap/wajah manusia; pilar nur dipisahkan dan tidak ditempatkan sebagai penunggang | `test_buraq_guard.py` memverifikasi penolakan penunggang eksplisit; panel Buraq + nur |
| 6. Dabbatul Ard | Hanya kabut/debu tanpa anatomi atau penanda wajah; contoh berlangsung pada preset Dhuha | Tes `kabut_tanpa_wujud`; panel render Dabbah dan verifikasi dalil terkait |
| 7. Shot Nuh, kapal, dan tanah | Lambung bahtera dan pilar tetap terbaca. Pilar pembuka berada dalam bingkai dan di belakang kapal. Kabut cakrawala kini berada di belakang tanah/benda/NPC/tokoh. Kerikil membentuk gerombol dengan sela kosong dan ukuran bervariasi. Foreground dekoratif mati sebagai bawaan | Tes batas pilar, urutan lapisan kabut, urutan pilar/bahtera, sebaran kerikil, determinisme tekstur, dan foreground |
| 8. Render paralel | Benchmark serial/paralel dijalankan pada runner yang sama; pembandingan sampel bingkai memastikan hasil piksel identik | `scripts/benchmark_render_tahap_b.py`; hasil benchmark disimpan sebagai artefak CI |

## Catatan audit visual dan keputusan pemilik

- Pemilik menyatakan kapal pembuka Nuh, pilar shot terakhir, tekstur tanah Dabbah, pilar pembuka, kerikil, dan foreground sudah baik.
- Dua temuan terakhir pada render `0ebcd2e` sudah ditangani: kabut merah muda tidak lagi dirender di atas lambung; sebaran batu tidak lagi seragam.
- Lembar kontak menampilkan Nuh, Dabbah, Buraq + nur, Ya'juj, Dajjal, variasi arah tokoh, perempuan berkerudung, serta anak/lansia.
- Komponen gerak Dajjal dan transisi arah tokoh juga memiliki tes perilaku; lembar kontak merupakan bukti komposisi, bukan pengganti tes gerak.
- Foreground hanya boleh diminta per shot dengan `depan: true` dan alasan artistik; kedalaman standar berasal dari tekstur tanah, skala tokoh, dan kabut jauh.
- Kabut jauh adalah lapisan atmosfer belakang. Ia tidak boleh menutupi kontur kapal, benda, NPC, atau tokoh.
- Kerikil menggunakan pola deterministik berbasis gerombol dan area renggang/kosong. `seed_tanah` mempertahankan konsistensi antar-frame.

## Kriteria penutupan

- [x] Delapan area Tahap B memiliki implementasi dan cakupan pemeriksaan.
- [x] Bukti render dan lembar kontak disimpan pada cabang `bukti`; MP4 tidak dimasukkan ke cabang PR.
- [x] Koreksi kabut dan sebaran batu diterapkan dengan tes regresi.

**Gerbang merge:** status check CI pada HEAD PR harus tetap hijau. Status terkini dapat dilihat langsung pada bagian Checks PR; jangan mengandalkan hasil dari commit terdahulu.

**Keputusan:** tidak ada celah implementasi Tahap B yang tersisa untuk dikerjakan dalam PR ini. PR dibuka untuk peninjauan akhir; merge tetap menunggu CI hijau pada HEAD terakhir.
