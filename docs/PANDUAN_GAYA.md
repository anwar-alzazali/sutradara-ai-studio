# Panduan gaya visual (dikunci pemilik, 21 Nov 2026)

Perubahan pada keputusan di bawah butuh persetujuan pemilik. Contoh visual: jalankan `python -m sutradara gambar contoh/<berkas>.json`.

## 1. Siapa digambar bagaimana

| Peran | Cara tampil | Kode |
|---|---|---|
| Nabi, malaikat, sahabat | **Pilar cahaya putih** setinggi tokoh, kapsul tanpa lekuk kepala/bahu/tangan, semburan sinar halus, butiran cahaya, genangan cahaya di tanah. Nama kecil di bawah saat diperkenalkan/saat ucapannya dibacakan. Kehadiran terasa lewat cahaya yang jatuh ke orang sekitar & reaksi mereka. | `gaya/nur.py` |
| Allah | **Tidak pernah** digambar dalam bentuk apa pun. Firman = teks + cahaya dari atas tanpa sosok. | — |
| Manusia biasa, kaum, orang beriman | **Berpakaian** (bawaan): gamis berwarna, ikat pinggang, imamah/kain kepala/kopiah, wajah berekspresi. | `gaya/tokoh.py` mode `pakaian` |
| NPC / kerumunan jauh | Tetap berpakaian, **kecil, tanpa detail wajah, pudar oleh kabut** (perspektif udara). Bukan siluet. | `adegan.npc_jauh` + `latar.kabut_jauh` |
| Siluet | Hanya dengan alasan: misteri (belum terungkap), kilas balik/mimpi, kerumunan sangat jauh berskala besar, wajah sengaja disembunyikan. Tepi tersinari dari arah cahaya. Tokoh yang terungkap berubah dari siluet ke berpakaian. | mode `siluet` |
| Makhluk ghaib yang wujudnya **tidak** dijelaskan dalil sahih (Dabbatul Ard, jin) | **Kabut tanah gelap tanpa wujud**: bergulung, tepi selalu berubah, pendar keemasan redup, tanpa mata/kepala/ukuran jelas, ditangkap sebagian. Bukan hitam pekat "jahat", tidak simetris dengan pilar nur. "Berbicara" = teks + narator, tanpa suara makhluk. | `gaya/makhluk.py` |
| Makhluk yang wujudnya dijelaskan dalil | Digambar **hanya** dengan ciri dari dalil; sisanya netral. | per tokoh |
| Dajjal | **Desain B**: berpakaian penguasa (jubah merah tua bersulam emas = pilihan gaya), mata kanan buta menonjol seperti anggur & keruh tanpa pupil (Bukhari 7123), ك ف ر di antara kedua mata (Bukhari 7131, Muslim 2933), rambut sangat keriting, muda. Tanpa gore, tanpa taring/tanduk, tanpa ciri ras. Boleh siluet di awal untuk misteri. | `gaya/dajjal.py` |
| Ya'juj Ma'juj | **Manusia biasa** (keturunan Adam, Bukhari 3348): tinggi bervariasi, pakaian compang-camping, tanpa wajah bila siluet. Kengerian dari **jumlah & gerak** (turun dari setiap tempat tinggi, QS Al-Anbiya 96), bukan bentuk aneh. Tanpa telinga raksasa/tanduk (riwayat lemah) dan tanpa ciri ras. | fase 7 |
| Buraq | Hewan putih, lebih besar dari keledai & lebih kecil dari bagal, langkahnya sejauh pandangan. **Tanpa sayap, tanpa wajah manusia, tidak pernah digambar dengan penunggang** (penunggang = pilar cahaya). Agung, bukan kartun lucu. Komponen dasar dan penjaga penunggang tersedia; penilaian proporsi visual tetap diperlukan. | `gaya/akhir_zaman.py` |

## 1b. Gerak & ekspresi
- Arah tokoh memakai `arah`: `depan`, `samping`, `belakang`, atau jadwal `[[detik, arah], ...]`. Perubahan sudut memakai smoothstep; tampilan wajah memudar saat tokoh membelakangi kamera.
- Ragam anatomi memakai `usia`: `anak`, `dewasa`, `lansia`; busana memakai `zaman`: `arab_kuno`, `mesir_kuno`, `umum`. Semua pilihan memakai rangka bersendi yang sama.
- Gerak dan ekspresi melayani cerita: pilih yang dinyatakan narasi (yang "lewat" berjalan, yang "mengejek" tertawa/menunjuk
  dengan mulut bergerak, yang "takut" mundur/menutup telinga). Daftar lengkap: `python -c "from sutradara import gerak; print(gerak.SEMUA)"`.
- Tidak ada gerak tanpa alasan di latar: NPC jauh hanya bernapas/bergerak kecil.
- Pilar nur tidak pernah diberi gerak tubuh; hanya cahaya yang berdenyut.

## 2. Suasana & lapisan
- Preset suasana (`gaya/latar.py`): `senja`, `dhuha`, `malam`, `malam_merah`, `fajar`. Dipakai ulang, dipetakan ke busur emosi.
- Selalu 3 lapis: belakang (langit, gunung/kota) · tengah (visual inti, tokoh) · depan (batu kabur di pojok).
- Waktu kejadian mengikuti dalil (Dabbah keluar di waktu **dhuha**, Muslim 2941 → adegan terang, bukan malam).

## 3. Penataan panggung (siapa berdiri di mana)
- **Pelaku aksi berdiri di dekat visual inti yang ia kerjakan** (yang membangun kapal di samping kapal). Tidak boleh ada
  tokoh lain yang lebih dekat ke visual inti daripada pelaku, kecuali lewat jelas di depan (lebih dekat ke kamera).
- Pihak yang berseberangan (yang mengejek, yang menolak) datang dari sisi lain atau melintas di depan, menghadap pelaku.
- Posisi tiap pihak dipertahankan antar-shot (resep A5) supaya penonton tidak bingung arah.
- Dicek otomatis: tulis `pelaku` di beat → penjaga memberi `PELAKU_JAUH` / `BUKAN_PELAKU_DEKAT`.

## 3b. Suara mengikuti aksi
- Efek suara terikat pada apa yang SEDANG DILAKUKAN di layar, bukan ditempel menurut detik. Palu mengikuti gerak
  `palu`, menggali mengikuti `gali`, dan langkah mengikuti `jalan`/`lari`/`lompat`.
- Keterlihatan dievaluasi pada waktu setiap bunyi: proyeksi posisi tokoh memakai keyframe `x/y/s`, zoom dan pusat
  kamera, serta guncang/hentak. Tokoh yang keluar bingkai atau tertutup hampir seluruhnya oleh tokoh di depan/lapis
  depan tidak diberi bunyi. Kotak tubuh dan sampel area adalah pendekatan konservatif, bukan pelacakan piksel.
- Posisi kiri-kanan dan volume mengikuti posisi serta ukuran tampak pada waktu bunyi. Variasi kecil deterministik
  pada waktu, gain, dan kecepatan mencegah ketukan identik terdengar seperti mesin. Jika slot ketukan terbatas,
  tokoh terdekat/terlihat mendapat prioritas; satu ketukan per tokoh dipilih sebelum ketukan tambahan.
- Bahan dapat dinyatakan lewat `permukaan` pada tokoh atau shot: `tanah`/`pasir`, `kayu`/`dek`,
  `air`, atau `batu_besi`. Dek bahtera dan sungai juga dapat dikenali dari posisi tokoh. Rekaman khusus dipakai
  bila ada; sampai tersedia, kode memakai aset cadangan yang sudah ada.
- Aksi lain yang memang terdengar: wajah/gerak `tertawa` atau `ejek` menjadi tawa kelompok satu kali;
  `npc_jauh` menjadi ambience kerumunan jauh; kabut yang nilai `keluar`-nya meningkat dan retakan tanah
  mendapat gemuruh/retak; perubahan `jadi` bahtera mendapat bunyi pembangunan. Bunyi palu pembangunan sebaiknya
  bersumber dari tokoh yang terlihat memalu, bukan hanya kapal yang berubah.
- Tidak semua gerak perlu bunyi: berdiri, bernapas, menoleh, menunjuk, mengangkat tangan, dan gerak ekspresi kecil
  tetap diam bila tidak ada kontak atau sumber bunyi yang masuk akal. Keheningan menjaga fokus dan mencegah
  setiap perubahan pose terdengar seperti efek.
- Efek yang tidak terlihat sumbernya (mis. guntur) dipasang di `beat.efek` pada kata (`"kata"`).
  Efek satu-kali yang mendekati potongan shot diberi ekor minimum dan fade pendek agar tidak putus menjadi klik;
  tandai `"lewat": true` bila memang disengaja menyambung.
- Workflow rekaman `.github/workflows/efek.yml` hanya `workflow_dispatch`, membaca `aset/suara/prompt_efek.json`,
  melewati berkas yang sudah ada, dan memakai `ELEVENLABS_API_KEY` dari GitHub Secrets. Tidak ada panggilan
  berbayar di tes/CI. Pemilik menjalankan workflow dengan memilih cabang PR di pemilih branch Actions, bukan
  `main`, agar hasil rekaman masuk ke cabang yang sedang diaudit.

## 4. Teks
- Judul layar 1–3 kata kapital yang menamai makna, maksimal 2 baris.
- Warna: **kuning** = fakta kunci/janji/harapan · **putih** = netral · **merah** = azab/ancaman/kesombongan.
- Sumber dalil kecil di atas (`QS HUD 38`, `HR. MUSLIM 2934`) di setiap shot yang isinya dari dalil itu.
- Subtitle satu baris di bawah, kata penting disorot kuning.
- **Kartu dalil bertahap**: pita ATAS yang tembus pandang (warna mengikuti preset suasana: senja, malam, malam_merah, fajar, dhuha), satu potongan Arab + terjemah (masing-masing <= 2 baris) sekaligus; Arab disapu,
  terjemah diketik, lalu diganti potongan berikutnya. Adegan tetap terlihat di bawahnya; judul & label sumber disembunyikan selama kartu tampil. Hadis: matan saja (kutipan persis).

## 5. Yang dilarang
Boneka "kamu" sebagai avatar penonton · siluet sebagai bawaan · nur berbentuk lampu sorot kerucut · sosok manusia dari cahaya
untuk tokoh suci · wujud ghaib yang dikarang · ciri ras/etnis pada tokoh jahat · logo/merek asli.
