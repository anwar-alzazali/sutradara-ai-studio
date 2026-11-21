# Asal dan status lisensi aset suara

Status dokumen ini: inventaris minimum untuk PR #14, bukan pernyataan bahwa seluruh aset sudah lolos pemeriksaan hukum.

## Aset yang sudah ada di repo

- Kode pencampur menyebut koleksi lama sebagai 47 efek dari ElevenLabs (sutradara/suara/campur.py).
- Repo tidak menyimpan prompt asal, tanggal pembuatan, ID generasi, bukti paket/akun, atau salinan ketentuan lisensi yang berlaku saat aset dibuat.
- Karena bukti tersebut tidak tersedia, lisensi dan hak redistribusi tiap MP3 lama **belum dapat diverifikasi** hanya dari isi repo ini.
- Jangan menyatakan koleksi lama sebagai public domain, CC0, atau bebas redistribusi. Pemilik perlu mencocokkan aset dengan riwayat akun/ketentuan ElevenLabs dan mengganti atau menghapus aset yang tidak memiliki hak penggunaan yang sesuai sebelum distribusi di luar repo.

## Rekaman baru melalui workflow

- prompt_efek.json menyimpan prompt dan target file, sedangkan workflow efek.yml hanya berjalan manual (workflow_dispatch) dengan secret pemilik.
- Workflow tidak mengunduh atau menyalin sampel pihak ketiga; hasilnya dibuat oleh layanan ElevenLabs. Hak penggunaan, batasan komersial, dan ketentuan atribusi tetap mengikuti paket dan ketentuan ElevenLabs yang berlaku pada saat generasi.
- Catat tanggal generasi, model/layanan, akun/paket, dan bukti ketentuan yang berlaku sebelum menyatakan aset baru siap untuk redistribusi publik. Jangan menyimpan API key, token, atau data akun privat di repo/log.
- Sampai verifikasi itu dilakukan, rekaman baru juga tidak boleh diberi label public domain atau bebas lisensi.

## Keputusan PR #14

Implementasi Tahap A tetap memakai aset fallback yang telah ada agar render lokal/CI tidak gagal karena belum ada rekaman khusus. Penggunaan fallback ini adalah kompatibilitas teknis, **bukan** pengesahan lisensi. Status pemeriksaan lisensi aset lama dan rekaman baru tetap perlu ditindaklanjuti pemilik sebelum publikasi/redistribusi.
