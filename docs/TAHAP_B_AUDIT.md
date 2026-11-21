# Swa-audit Tahap B

PR #18 tetap Draft sampai tinjauan visual pemilik selesai. Audit ini membedakan bukti implementasi/CI dari persetujuan estetika akhir.

**Commit yang diaudit:** `c652cd8eabcb602d1ae055f4f21e488c19ba02eb`  
**CI:** [Run #44894000068](https://github.com/anwar-alzazali/sutradara-ai-studio/actions/runs/44894000068) — sukses, 155 tes lulus.  
**Bukti visual:** cabang `bukti`, berkas `tahap-b/lembar-kontak-59f8486e7a4f1763ecfa657ce756de6c176783b3.jpg` (commit bukti `d8e5cc5c0862d625d088da860f482b152867f8aa`).

| Poin | Implementasi & bukti otomatis | Hasil audit teknis | Sisa verifikasi |
|---|---|---|---|
| 1. Arah tokoh depan/samping/belakang | `sutradara/gaya/tokoh.py`; transisi arah smoothstep; tes `test_arah_tokoh_memiliki_transisi_halus`, tes profil dan belakang pada `test_akhir_zaman.py` | Lulus | Tinjauan visual pemilik untuk konsistensi bentuk pada video utuh |
| 2. Ragam usia, zaman, dan perempuan | `tokoh.orang`: usia anak/dewasa/lansia, zaman Arab kuno/Mesir kuno/umum, kerudung; bukti panel perempuan berkerudung dan anak Mesir kuno + lansia pada lembar kontak | Implementasi dan render contoh tersedia | Tinjauan visual pemilik; cakupan pakaian tiap zaman belum diuji sebagai matriks lengkap |
| 3. Dajjal desain B dari belakang | `sutradara/gaya/dajjal.py`; contoh `contoh/dajjal_dua_sungai.json`; tes `test_dajjal_tampak_belakang_tidak_memperlihatkan_wajah_depan`, `test_jubah_dajjal_berubah_saat_berkibar`, dan render SVG valid | Lulus untuk fungsi belakang, gerak, jubah, serta pembukaan lengan terjadwal | Lembar kontak hanya membuktikan satu pose belakang; gerak utuh perlu tinjauan pemilik |
| 4. Ya'juj Ma'juj | `contoh/yajuj_majjuj.json`; manusia berpakaian, dinding berlubang, turun dari tempat tinggi, danau surut; tes `test_lubang_dinding_yajuj_membesar`, `test_danau_menyusut_dengan_keyframe`, `test_rencana_yajuj_memakai_manusia_biasa_dan_dalil_yang_ditandai_belum` | Lulus secara teknis; workflow memverifikasi QS Al-Anbiya 96 dan HR. Tirmidzi 2240 (sahih), tanpa temuan | Tinjauan visual pemilik untuk keterbacaan skala/jumlah manusia |
| 5. Buraq dan larangan penunggang | `sutradara/gaya/akhir_zaman.py:buraq`; tes putih/empat kaki tanpa sayap/wajah manusia; `test_buraq_guard.py` menguji penolakan penunggang eksplisit dan posisi di punggung | Lulus secara teknis; lembar kontak menampilkan Buraq putih dan pilar nur terpisah | Proporsi dan langkah masih perlu tinjauan visual pemilik |
| 6. Dabbatul Ard | `contoh/dabbah_dhuha.json` memakai `kabut_tanpa_wujud`; `test_dabbah_hanya_kabut_tanpa_wujud_tanpa_penanda_wajah`; lembar kontak menunjukkan gumpalan kabut tanpa anatomi | Lulus; tidak ada bentuk tubuh/kepala/mata atau tanda wajah yang dikarang | Tinjauan visual pemilik atas adegan lengkap dan sinkron dialog/narator |
| 7. Shot pembuka Nuh | `contoh/nuh_mengejek.json`; penyangga darat dimatikan, lambung dinaikkan ke `jadi=0.86`, kamera diarahkan ulang; lembar kontak terbaru memperlihatkan lambung/papan bahtera | Lulus secara teknis dan bentuk kapal lebih terbaca dibanding bukti sebelumnya | Pemilik perlu menyetujui komposisi akhir; contoh render bersuara memakai narasi tiruan |
| 8. Paralel render | Benchmark pada runner GitHub Actions yang sama: serial 284,53 dtk; paralel 250,64 dtk; 1,135x; sampel bingkai identik | Lulus; ada percepatan terukur tanpa perbedaan sampel piksel | Tidak ada perubahan kode untuk poin ini |

## Pemeriksaan CI tambahan

- Tes Python: **155 passed**.
- Render video bukti Nuh: berhasil, durasi 33,585 dtk.
- Audio hasil render: **-16,09 LUFS**, true peak **-3,27 dBTP**.
- Verifikasi dalil Ya'juj: `✓ QS AL-ANBYA 96`, `✓ HR. TIRMIDZI 2240 (sahih)`, `LULUS: tidak ada temuan`.
- JPG bukti saja disimpan ke cabang `bukti`; tidak menyimpan MP4 hasil render ke cabang PR.

## Keputusan swa-audit

Seluruh delapan area telah memiliki implementasi dan/atau bukti teknis sesuai tingkat yang dicatat di tabel. Ini **bukan persetujuan visual final**: beberapa aspek proporsi, gerak, dan komposisi masih memerlukan penilaian pemilik. Karena itu PR #18 tetap Draft sampai pemilik menyatakan hasil visual layak.


## Catatan pemilik: kapal Nuh, kesan buram, dan tanah bertekstur

- **Kapal Nuh:** kontur lambung dan papan tetap menjadi visual inti. Tekstur tanah ditempatkan pada lapisan tanah, sebelum benda, NPC, dan tokoh; detail kerikil tidak boleh menutupi siluet kapal atau mengurangi kontras kontur.
- **Catatan “terasa buram”:** batu foreground harus berupa siluet dengan tepi tegas. Filter `url(#kabur)` tidak dipakai sebagai bawaan; tes render memastikan filter itu tidak muncul pada adegan.
- **Tanah:** tekstur bawaan `tanah_berbatu` memakai bercak, guratan dan kerikil berkontras rendah. Rencana dapat memilih `pasir`, `tanah`, `batu`, atau `tanpa`, serta `seed_tanah` untuk pola yang dapat diulang.
- **Stabilitas visual:** geometri tekstur dibuat deterministik dan di-cache berdasarkan preset, batas tanah, jenis, dan seed. Tekstur berada di koordinat dunia sehingga mengikuti transform kamera/paralaks dan tidak berubah antar-frame.
- **Batas verifikasi:** CI akan menguji determinisme, pemilihan jenis, urutan lapisan, dan merender bukti Nuh/Dabbah sebelum-sesudah. Angka dampak waktu render dicatat oleh benchmark khusus; penilaian apakah detail tanah terlalu ramai tetap memerlukan tinjauan visual pemilik.
