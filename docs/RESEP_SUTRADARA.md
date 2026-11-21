# Resep Sutradara — dibongkar dari video Nabi Nuh (nuh2) dan Ya'juj Ma'juj (yajuj2)

> Dipindahkan dari sesi analisis 21 Nov 2026. Rujukan berkas `papan/...` menunjuk repo lama **mesin-video** (arsip). Pola penyutradaraan di sini berlaku; cara menggambar tokoh mengikuti `docs/PANDUAN_GAYA.md` (lebih baru).

Sumber: `papan/kisah/nuh2_buat.py` (23 beat, ±128 dtk) dan `papan/kisah/yajuj2_buat.py` (13 beat, ±66 dtk), keduanya disutradarai manual oleh Claude di sesi chat dan dinilai bagus oleh pemilik. Resep ini adalah pola keputusan yang **berulang** di kedua video, supaya sutradara otomatis bisa menirunya. Ditulis 21 Nov 2026.

---

## A. Keputusan tingkat video (dibuat sekali, sebelum shot apa pun)

### A1. Satu VISUAL INTI yang berubah keadaan sepanjang video
Setiap video punya satu benda pusat dengan **parameter keadaan** yang dianimasikan dari awal sampai akhir. Penonton mengikuti cerita lewat perubahan benda itu.

| Video | Visual inti | Parameter yang berubah | Jalur keadaan |
|---|---|---|---|
| Nuh | bahtera | `jadi` (rangka→jadi), `goyang`, posisi laut `y` | rangka di darat → jadi → diterjang badai → tenang saat fajar |
| Ya'juj | dinding besi (`ngarai`) | `lubang` 0→1, `jebol` 0→1 | lubang kecil → hampir tembus → utuh lagi (×3, makin dalam) → jebol |

**Aturan:** sutradara wajib menetapkan `visual_inti` + `jalur_keadaan` (daftar keadaan per beat) sebelum menulis shot. Visual inti muncul di sebagian besar shot.

### A2. Babak suasana = 3–4 preset cahaya, bukan tiap shot beda
Kedua video memakai preset latar bernama yang dipakai ulang:

| Preset (Nuh) | Isi | Dipakai untuk |
|---|---|---|
| `DARAT` | palet senja, malam 0.35, debu | masa dakwah, kehidupan biasa |
| `MALAMD` | palet malam, bulan, bintang | kesendirian, doa, diam-diam |
| `BADAI` | malam 1, langit gelap, hujan, petir | azab, puncak ketegangan |
| `FAJAR` | senja terang, matahari naik | sesudah azab, pelajaran, penutup |

Ya'juj: `LATAR` gelap (di balik dinding) dan `LUAR` senja (dunia manusia).

**Aturan:** busur emosi video dipetakan ke urutan preset. Penutup selalu di preset paling terang yang tersedia (jalan keluar / harapan), kecuali pesannya justru peringatan yang belum selesai (Ya'juj ditutup tetap gelap, tapi dengan kalimat kunci "INSYA ALLAH" berwarna kuning).

### A3. Hook = momen paling dramatis dipindah ke depan
- Nuh dibuka dengan badai: ayah di kapal, anak di tebing ("AYAH MEMANGGIL / ANAKNYA MENOLAK"), lalu beat 1 kembali ke awal kisah.
- Ya'juj dibuka di tengah penggalian, langsung pada visual inti, teks besar sejak frame 0.

**Aturan:** shot pertama = keadaan paling tegang dari `jalur_keadaan`, teks layar muncul di detik 0. Setelah itu boleh mundur ke awal kronologi.

### A4. Peran tokoh → cara menggambar (pagar keselamatan + daya cerita)
| Peran dalam kisah | Cara gambar | Contoh |
|---|---|---|
| Nabi / malaikat / sahabat | di video lama: `nur` lampu sorot; **sekarang: pilar cahaya** (`gaya/nur.py`) + nama di bawah, nama tampil di shot pengenalan dan saat ucapannya dibacakan, disembunyikan di shot lebar | Nabi Nuh |
| Kaum / massa | di video lama: `kerumunan` siluet; **sekarang: berpakaian, yang jauh pudar oleh kabut**; **pose mengikuti kata kerja di narasi** (`telinga`, `wajah`, `berdiri`), atau `arus` (lari, lereng, cahaya) | kaum Nuh, Ya'juj Ma'juj |
| Tokoh penting yang bukan tokoh suci | di video lama: siluet; **sekarang: berpakaian** (siluet hanya dengan alasan, lihat PANDUAN_GAYA) | anak Nuh di tebing |
| Pemimpin / juru bicara pihak lawan | benda khusus siluet besar di depan (`pemimpin`) | pemimpin Ya'juj |
| Suara Allah / wahyu | **tanpa sosok**: cahaya dari atas + teks | "Dia bukan keluargamu" |
| Penonton ("kamu") | **tidak digambar**. Penonton disapa lewat teks dan narasi, bukan avatar | — |

### A5. Jarak dan hubungan antartokoh jadi komposisi
Nuh: ayah (kapal, kanan) dan anak (tebing, kiri) dipertahankan di posisi yang sama setiap kali muncul. Jarak keduanya adalah inti emosi. **Aturan:** kalau kisah punya dua pihak, beri masing-masing sisi layar yang tetap.

---

## B. Keputusan tingkat shot

### B1. Potongan shot jatuh tepat di kata kunci
Semua pergantian shot dihitung dari waktu kata TTS (`W(beat, "kata")`), bukan dibagi rata. Satu beat bisa berisi beberapa shot bila narasinya berisi **daftar/enumerasi**:
- Nuh beat 3: "siang | malam | terang-terangan | diam-diam" → 4 shot, palet berganti siang/malam.
- Nuh beat 4: "menyumbat telinga | menutupi wajah" → pose kerumunan berganti tepat di kata.
- Ya'juj: "Hari 1 | Hari 2 | Hari 3" → 3 shot.

**Aturan:** cari kata kunci di tiap beat (kata kerja peristiwa, angka, nama, kata kontras "tapi/bukan"). Potong shot 0,1 dtk sebelum kata itu diucapkan.

### B2. Pengulangan dengan eskalasi
Saat narasi mengulang (setiap hari, berkali-kali), setiap putaran dibuat **lebih intens**: zoom makin dekat (1.12 → 1.95 → 2.7), keadaan makin jauh (lubang 0.72 → 0.88 → 1.0), warna teks naik dari kuning ke merah, volume efek naik.

### B3. Kosakata kamera (`K(zoom, x, y)`)
| Jenis | Nilai | Kapan |
|---|---|---|
| Dorong pelan | zoom 1.0→1.08–1.15 | bawaan hampir semua shot (tidak ada shot benar-benar diam) |
| Dekat emosi | 1.3–1.75 | ucapan tokoh, doa, keputusan |
| Sangat dekat | 1.95–2.7 | puncak detail (lubang tembus, eskalasi terakhir) |
| Tarik mundur / reveal | 1.2→0.62 sambil naik | memperlihatkan skala (seluruh dinding) |
| Menjauh | 1.3→1.08 | sesudah ledakan/jebol, memperlihatkan akibat |
| `guncang` | 30–46 | tepat di kata dampak (ombak, petir, jebol) |
| `hentak` | 0.06–0.1 | tepat di kata kontras/janji ("Dia BUKAN keluargamu", "INSYA ALLAH") |

### B4. Lapisan kedalaman (selalu 3)
- **Belakang:** gunung, awan, bulan, bintang, matahari (`belakang=True`).
- **Tengah:** visual inti + tokoh.
- **Depan:** ombak depan, batu kabur (`kabur=True`), arus orang di depan (`depan=True`).

Lapis depan bergerak beda kecepatan → rasa kedalaman. Ini yang membuat video "punya kedalaman" menurut pemilik.

### B5. Gerak hidup di dalam shot
Selain kamera, selalu ada yang bergerak: hujan bertingkat (`hujan` dianimasikan 0→1), petir dengan `saat=[detik]`, air naik (`laut y` berubah), kerumunan `arus` dengan `maju`, kapal `goyang`, opasitas anak memudar saat tenggelam.

---

## C. Teks layar

- **1–3 kata, huruf kapital, maksimal 2 baris**, muncul tepat saat kata itu diucapkan. Teks menamai *makna* adegan, bukan menyalin narasi ("950 TAHUN", "HANYA SEDIKIT", "UTUH KEMBALI").
- **Warna punya arti:** kuning `#ffd27a` = fakta kunci / janji / harapan; putih = netral; merah `#ff6a4a` = azab, ancaman, kesombongan ("DITENGGELAMKAN", "BESOK KITA TEMBUS").
- **Ucapan langsung** pakai tanda kutip: “KAMI PUN AKAN MENGEJEK KALIAN”.
- **Sumber dalil** selalu kecil gaya neon di atas (`QS HUD 42`, `HR. TIRMIDZI 3153 · IBNU MAJAH 4080, disahihkan Al-Albani`), muncul di setiap shot yang isinya berasal dari dalil itu.
- **Subtitle** terpisah di bawah: dipecah per tanda baca atau maks 4 kata, satu baris.

---

## D. Suara (rekaman efek)

| Lapisan | Contoh | Aturan |
|---|---|---|
| Ambience panjang per babak | `laut_malam`, `drone_gelap`, `angin_gurun`, `jangkrik`, `malam_hening` | satu bed per preset suasana, `ulang=True`, sampai babak berganti |
| Hentakan di kata kunci | `braam`, `hentak_serius`, `guntur_hujan` | sinkron dengan `guncang`/`hentak` kamera |
| Diegetik sinkron gerak | `satu/palu`, `satu/gali`, `satu/langkah`, `satu/langkah_lari` | satu ketukan pada titik kena; posisi, ukuran, keterlihatan, dan bahan dinilai saat kejadian |
| Bahan langkah/pukulan | `aksi/langkah_pasir`, `aksi/langkah_kayu`, `aksi/langkah_air`, `aksi/langkah_batu_besi`, `aksi/palu_kayu`, `aksi/palu_batu_besi` | pakai rekaman khusus bila tersedia; fallback ke aset lama tanpa menggagalkan render |
| Aksi/lingkungan lain | `aksi/tawa_ejekan`, `aksi/kerumunan_jauh`, `aksi/kabut_keluar`, `aksi/tanah_retak` | satu tawa kelompok, ambience NPC jauh, dan tekstur hanya saat kabut/retakan benar-benar berkembang |
| Kilau / wahyu | `kilau_cahaya` | saat nur muncul, cahaya dari atas, kalimat harapan |
| Emosi penutup | `dengung_haru`, `senandung_haru` | dari pelajaran sampai akhir video |
| Ketegangan | `detak_jantung` | adegan menunggu keputusan (anak di tebing) |

Volume 0,3–0,9: bed rendah (0,2–0,45), hentakan tinggi (0,6–0,9).
Gerak diam seperti berdiri/bernapas/menunjuk tidak diberi bunyi tanpa kontak yang terdengar. Ketukan berulang
divariasikan ringan secara deterministik; satu ketukan per tokoh yang paling terlihat diprioritaskan sebelum
slot berikutnya dibagikan. Efek satu-kali dekat batas shot mendapat ekor minimum + fade pendek.

---

## E. Penutup
1. Pelajaran dalam satu kontras besar ("BUKAN NASAB / TAPI IMAN & PILIHANMU").
2. Pertanyaan pribadi yang menempatkan penonton di kisah ("KALAU KAMU DI SANA, KAMU MEMILIH NAIK?").
3. Ajakan komentar + ajakan kirim ke orang tertentu ("Kirim ke yang merasa sendirian di jalan benar").
4. Visual inti masih tampil dalam keadaan akhirnya; ekor suara ±2,6–3,6 dtk.

---

## F. Selisih dengan Direktur rule-based yang sekarang (`papan/direktur.py` + `arah_visual.py`)

Diuji 21 Nov dengan naskah `tests/naskah_direktur/banjir_nuh_uji.json`:

| Resep video bagus | Direktur rule-based sekarang |
|---|---|
| Tidak ada avatar penonton; tokoh kisah digambar sesuai A4 | Boneka "kamu" berdiri di tengah hampir di setiap shot |
| Visual inti berubah keadaan (A1) | Tidak ada visual inti; kapal hanya hiasan latar |
| Kaum digambar sebagai kerumunan berpose | Tidak ada kerumunan; "ditertawakan" tidak terlihat |
| Shot dipotong di kata kunci, enumerasi dipecah (B1) | ±1 shot per adegan |
| Hook = momen paling dramatis | Shot pertama tenang, teks label "Kapal di daratan" |
| 3 lapis kedalaman (B4) | Latar datar + tokoh, ada bercak hitam di pojok bawah |

**Kesimpulan:** perbaikan Direktur bukan menambah variasi pose/kamera "kamu", tetapi mengganti tulang punggungnya: rencanakan **A1–A4 dulu**, lalu turunkan shot dari kata kunci (B1) dengan kosakata kamera B3, lapisan B4, teks C, dan suara D.

---

## G. Bentuk keluaran yang diharapkan dari sutradara otomatis (tahap rencana)

```json
{
  "visual_inti": {"benda": "bahtera", "jalur_keadaan": ["rangka_darat", "jadi", "badai", "tenang_fajar"]},
  "preset": {"DARAT": {...}, "BADAI": {...}, "FAJAR": {...}},
  "peran": {"Nabi Nuh": "nur", "kaum": "kerumunan", "anak": "siluet_kiri", "kapal": "kanan"},
  "hook": {"dari_beat": 16, "teks": ["AYAH MEMANGGIL", "ANAKNYA MENOLAK"]},
  "beat": [
    {"i": 3, "preset": "DARAT", "keadaan": "rangka_darat",
     "potong_di": ["malam", "terang", "diam"], "teks": ["SIANG", "MALAM", "TERANG-TERANGAN", "DIAM-DIAM"],
     "kamera": "dorong_pelan", "sumber": "QS NUH 5-9", "suara": ["jangkrik@malam", "pop_teks@terang"]}
  ]
}
```

Bentuk resmi rencana kini ada di `sutradara/rencana/rencana.schema.json`; contoh lengkap di `contoh/`. Nama fungsi `shot`, `K`, `T`, `R`, `Bd` di atas merujuk kode repo lama `mesin-video` (rujukan konsep, tidak disalin).
