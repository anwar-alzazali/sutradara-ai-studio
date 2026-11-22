"""Pemeriksaan kontinuitas yang netral terhadap genre.

Modul ini hanya membandingkan identitas stabil pada kartu pemeran dengan atribut
yang dipakai per shot. Aturan cara tokoh ditampilkan tetap menjadi tanggung jawab
paket genre.
"""
from __future__ import annotations

from typing import Any

from .penjaga import Temuan


_KUNCI_IDENTITAS = {
    "jenis": "jenis",
    "usia": "usia",
    "zaman": "zaman",
    "indeks": "indeks",
    "warna_kulit": "warna_kulit",
    "warna_baju": "warna_baju",
    "warna_aksen": "warna_aksen",
    "rambut": "rambut",
    "janggut": "janggut",
    "warna_janggut": "warna_janggut",
    "aksesori": "aksesori",
    "suara": "suara",
    "ciri_wajah": "ciri_wajah",
    "kepala": "penutup_kepala",
}



def periksa_kedekatan_pelaku(
    *,
    visual_x: float,
    visual_y: float,
    setengah_lebar: float,
    pelaku: list[tuple[str, str, float, float]],
    tokoh_lain: list[tuple[str, float, float]],
    jarak_maks: float,
    pita_kedalaman: float,
    label_visual: str,
    lokasi: str,
) -> list[Temuan]:
    """Periksa kedekatan pelaku terhadap objek dengan geometri netral-genre.

    Koordinat dan ukuran visual diberikan oleh pemanggil; inti tidak mengetahui
    nama benda, kategori tokoh, atau cara representasi karakter.
    """
    def jarak_tepi(x: float) -> float:
        return max(0.0, abs(x - visual_x) - setengah_lebar)

    hasil: list[Temuan] = []
    jarak_pelaku = {pid: jarak_tepi(x) for pid, _nama, x, _y in pelaku}
    jauh = [(pid, nama) for pid, nama, x, _y in pelaku
            if jarak_tepi(x) > jarak_maks]
    if jauh:
        nama = ", ".join(n for _pid, n in jauh)
        hasil.append(Temuan(
            "PERIKSA", "PELAKU_JAUH",
            f"{lokasi}: {nama} berbuat pada {label_visual} tetapi terlalu jauh dari tepinya",
        ))

    if jarak_pelaku:
        terdekat = min(jarak_pelaku.values())
        lebih_dekat = [
            pid for pid, x, y in tokoh_lain
            if jarak_tepi(x) + 1 < terdekat
            and abs(y - visual_y) < pita_kedalaman
        ]
        if lebih_dekat:
            hasil.append(Temuan(
                "PERIKSA", "BUKAN_PELAKU_DEKAT",
                f"{lokasi}: {len(lebih_dekat)} tokoh non-pelaku lebih dekat ke "
                f"{label_visual} daripada pelaku terdekat",
            ))
    return hasil


def periksa_lintasan_dan_interaksi(rencana: dict[str, Any]) -> list[Temuan]:
    """Periksa lintasan gerak dan arah interaksi tanpa mengasumsikan genre.

    Koordinat x/y multi-keyframe adalah lintasan yang sudah didukung renderer;
    lintasan eksplisit boleh dipakai saat arah gerak harus terdokumentasi.
    Gerak di tempat tetap memerlukan alasan supaya siklus kaki tak menyiratkan
    perjalanan yang tidak terlihat.
    """
    hasil: list[Temuan] = []
    arah_tujuan: dict[tuple[str, str], int] = {}
    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            lokasi = f"beat {bi} shot {si}"
            tokoh = shot.get("tokoh", [])
            nama_peran = {p.get("id"): p.get("nama", p.get("id")) for p in rencana.get("peran", [])}

            def bergerak_mendatar(aktor: dict[str, Any]) -> int:
                lintasan = aktor.get("lintasan")
                if isinstance(lintasan, list) and len(lintasan) >= 2:
                    try:
                        return (float(lintasan[-1][1]) > float(lintasan[0][1])) - (float(lintasan[-1][1]) < float(lintasan[0][1]))
                    except (TypeError, ValueError, IndexError):
                        return 0
                x = aktor.get("x")
                if isinstance(x, list) and len(x) >= 2:
                    try:
                        a = float(x[0][1]); b = float(x[-1][1])
                        return (b > a) - (b < a)
                    except (TypeError, ValueError, IndexError):
                        return 0
                return 0

            for aktor in tokoh:
                gerak = aktor.get("gerak", aktor.get("pose", "berdiri"))
                gerak_awal = gerak[0][1] if isinstance(gerak, list) and gerak else gerak
                if gerak_awal not in {"jalan", "lari"}:
                    continue
                pid = aktor.get("peran", "tokoh")
                alasan = aktor.get("alasan_di_tempat")
                ada_lintasan = (isinstance(aktor.get("lintasan"), list) and len(aktor["lintasan"]) >= 2) or bergerak_mendatar(aktor) != 0
                if aktor.get("di_tempat") is True and isinstance(alasan, str) and alasan.strip():
                    continue
                tujuan = aktor.get("tujuan")
                if not isinstance(tujuan, str) or not tujuan.strip():
                    hasil.append(Temuan("GAGAL", "TUJUAN_GERAK_TAK_ADA",
                                        f"{lokasi}: {nama_peran.get(pid, pid)} bergerak {gerak_awal} tanpa tujuan; rujuk tokoh/benda atau tepi layar"))
                if not ada_lintasan:
                    hasil.append(Temuan("GAGAL", "LINTASAN_TAK_ADA",
                                        f"{lokasi}: {nama_peran.get(pid, pid)} bergerak {gerak_awal} tanpa lintasan; tetapkan lintasan/koordinat keyframe atau di_tempat dengan alasan"))
                    continue
                arah = aktor.get("arah", "samping")
                arah_awal = arah[0][1] if isinstance(arah, list) and arah else arah
                dx = bergerak_mendatar(aktor)
                if dx and arah_awal in {"depan", "belakang"}:
                    hasil.append(Temuan("PERIKSA", "ARAH_GERAK", f"{lokasi}: {nama_peran.get(pid, pid)} bergerak mendatar tetapi arah hadapnya {arah_awal}; pastikan lintasan dan orientasi cocok"))
                elif dx and arah_awal == "samping":
                    if bool(aktor.get("balik", False)) == (dx > 0):
                        hasil.append(Temuan("PERIKSA", "ARAH_GERAK", f"{lokasi}: arah hadap {nama_peran.get(pid, pid)} mungkin berlawanan dengan lintasan; periksa balik/arah"))
                    if dx:
                        kunci = (str(pid), tujuan)
                        lama = arah_tujuan.get(kunci)
                        if lama is not None and lama != dx and not aktor.get("berbalik_sesuai_cerita"):
                            hasil.append(Temuan("PERIKSA", "ARAH_LAYAR_BERUBAH",
                                                f"{lokasi}: arah menuju {tujuan!r} berubah untuk {nama_peran.get(pid, pid)}; jaga kaidah 180 derajat atau tandai putar balik yang diceritakan"))
                        arah_tujuan[kunci] = dx

            # Dialog yang terstruktur harus memperoleh potongan pada pihak yang bicara.
            dialog = beat.get("dialog") or []
            if isinstance(dialog, dict):
                dialog = [dialog]
            for di, giliran in enumerate(dialog):
                pembicara = giliran.get("pembicara") if isinstance(giliran, dict) else None
                penjawab = giliran.get("penjawab") if isinstance(giliran, dict) else None
                if not pembicara:
                    hasil.append(Temuan("GAGAL", "DIALOG_TANPA_PEMBICARA", f"{lokasi}: dialog ke-{di + 1} perlu id pembicara"))
                    continue
                cakupan = [pembicara, *([penjawab] if penjawab else [])]
                ada_closeup = False
                for pid in cakupan:
                    ditemukan = any(t.get("peran") == pid and t.get("bicara") for s in beat.get("shot", []) for t in s.get("tokoh", []))
                    cahaya = any(n.get("peran") == pid and n.get("bicara") for s in beat.get("shot", []) for n in s.get("nur", []))
                    for s in beat.get("shot", []):
                        subjek = next((t for t in s.get("tokoh", []) if t.get("peran") == pid), None)
                        zoom = (s.get("kamera") or {}).get("zoom", 1.0)
                        zoom = zoom[-1][1] if isinstance(zoom, list) and zoom else zoom
                        ada_closeup = ada_closeup or bool(subjek and isinstance(zoom, (int, float)) and zoom >= 1.3)
                    if not (ditemukan or cahaya):
                        hasil.append(Temuan("PERIKSA", "DIALOG_TANPA_LIPUTAN", f"{lokasi}: {nama_peran.get(pid, pid)} tercatat dalam dialog tetapi tidak punya cakupan ucapan/bicara pada shot"))
                if not ada_closeup:
                    hasil.append(Temuan("PERIKSA", "DIALOG_TANPA_CLOSEUP", f"{lokasi}: dialog ke-{di + 1} belum punya shot dekat yang menekankan pembicara/penjawab"))

            # Interaksi eksplisit: pasangan tidak boleh sama-sama menghadap lensa
            # tanpa alasan yang menjelaskan pilihan artistik tersebut.
            pasangan = []
            for giliran in dialog if isinstance(dialog, list) else []:
                if isinstance(giliran, dict) and giliran.get("pembicara") and giliran.get("penjawab"):
                    pasangan.append((giliran["pembicara"], giliran["penjawab"]))
            for s in beat.get("shot", []):
                for item in s.get("barang", []):
                    if item.get("aksi") == "ulurkan" and item.get("pemilik") and item.get("penerima"):
                        pasangan.append((item["pemilik"], item["penerima"]))
                tampil = {t.get("peran"): t for t in s.get("tokoh", [])}
                for a, b in pasangan:
                    ta, tb = tampil.get(a), tampil.get(b)
                    if ta and tb and ta.get("arah", "depan") == "depan" and tb.get("arah", "depan") == "depan":
                        alasan = ta.get("alasan_arah") or tb.get("alasan_arah")
                        if not (isinstance(alasan, str) and alasan.strip()):
                            hasil.append(Temuan("PERIKSA", "INTERAKSI_MENGHADAP_KAMERA", f"{lokasi}: pasangan {nama_peran.get(a, a)} dan {nama_peran.get(b, b)} sama-sama menghadap kamera; arahkan ke lawan atau jelaskan alasannya"))
    return hasil

def periksa_kontinuitas_identitas(rencana: dict[str, Any]) -> list[Temuan]:
    """Tandai pemeran yang tidak terdaftar dan perubahan ciri stabil antar-shot.

    Peran kolektif tidak dibandingkan dengan satu identitas contoh. Individu
    dalam kelompok tetap diaudit melalui pemeran_id yang stabil.
    """
    hasil: list[Temuan] = []
    peta_peran = {p["id"]: p for p in rencana.get("peran", [])}
    kartu_pemeran = {p["id"]: p for p in rencana.get("pemeran", [])}
    kartu = {pid: p.get("identitas", {}) for pid, p in peta_peran.items()}
    kartu.update({pid: p.get("identitas", {}) for pid, p in kartu_pemeran.items()})

    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            for tokoh in shot.get("tokoh", []):
                pid = tokoh.get("pemeran_id") or tokoh.get("peran")
                if tokoh.get("pemeran_id") and pid not in kartu_pemeran:
                    hasil.append(Temuan(
                        "GAGAL",
                        "PEMERAN_TAK_TERDAFTAR",
                        f"beat {bi} shot {si}: pemeran_id {pid!r} tidak memiliki kartu identitas",
                    ))
                    continue

                id_peran = tokoh.get("peran")
                definisi_peran = peta_peran.get(id_peran, {})
                if not tokoh.get("pemeran_id") and definisi_peran.get("kolektif", False):
                    identitas = {}
                else:
                    identitas = kartu.get(pid) or {}
                if not identitas:
                    continue

                beda = [
                    (field, identitas[acuan], tokoh[field])
                    for field, acuan in _KUNCI_IDENTITAS.items()
                    if field in tokoh and acuan in identitas and tokoh[field] != identitas[acuan]
                ]
                if beda:
                    rincian = ", ".join(f"{field}: {lama!r} -> {baru!r}" for field, lama, baru in beda)
                    hasil.append(Temuan(
                        "PERIKSA",
                        "IDENTITAS_BERUBAH",
                        f"beat {bi} shot {si} {pid}: ciri kartu pemeran berubah ({rincian}); "
                        "perbarui kartu hanya bila perubahan memang menjadi desain baru",
                    ))
    return hasil


def periksa_kontinuitas_barang(rencana: dict[str, Any]) -> list[Temuan]:
    """Periksa invarians barang lintas-shot tanpa asumsi kategori atau genre.

    Kepemilikan hanya berubah melalui pasangan aksi ulurkan/terima. Pemeriksaan
    ini tidak menentukan bagaimana pemilik divisualkan atau apakah ia hadir
    sebagai tubuh, cahaya, maupun representasi lain.
    """
    hasil: list[Temuan] = []
    sebelumnya: dict[str, dict[str, Any]] = {}
    peran = {p["id"]: p for p in rencana.get("peran", [])}
    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            lokasi = f"beat {bi} shot {si}"
            sekarang: dict[str, dict[str, Any]] = {}
            for item in shot.get("barang", []):
                iid, pemilik = item.get("id"), item.get("pemilik")
                if not iid or iid in sekarang:
                    hasil.append(Temuan("GAGAL", "ID_BARANG",
                                        f"{lokasi}: id barang kosong atau duplikat ({iid})"))
                    continue
                sekarang[iid] = item
                if pemilik not in peran:
                    hasil.append(Temuan("GAGAL", "PEMILIK_BARANG",
                                        f"{lokasi}: pemilik {pemilik!r} tidak terdaftar"))
                    continue
                if item.get("tangan", "ka") not in {"ka", "ki"}:
                    hasil.append(Temuan("GAGAL", "TANGAN_BARANG",
                                        f"{lokasi} {iid}: tangan harus ka/ki"))
                aksi = item.get("aksi", "pegang")
                if aksi in {"ulurkan", "terima"}:
                    titik = item.get("titik_serah")
                    if not titik or len(titik) != 2:
                        hasil.append(Temuan("GAGAL", "TITIK_SERAH_BARANG",
                                            f"{lokasi} {iid}: aksi {aksi} perlu titik_serah [x,y]"))
                    pasangan = item.get("penerima") if aksi == "ulurkan" else item.get("pemberi")
                    if pasangan not in peran:
                        hasil.append(Temuan("GAGAL", "PASANGAN_SERAH_TERIMA",
                                            f"{lokasi} {iid}: pasangan serah-terima tidak terdaftar"))
                if iid in sebelumnya:
                    lama = sebelumnya[iid]
                    pemilik_lama = lama.get("pemilik")
                    if pemilik_lama != pemilik:
                        sah = (lama.get("aksi") == "ulurkan" and lama.get("penerima") == pemilik
                               and aksi == "terima" and item.get("pemberi") == pemilik_lama)
                        if not sah:
                            hasil.append(Temuan("GAGAL", "PEMILIK_BARANG_BERUBAH",
                                                f"{lokasi} {iid}: pemilik berubah {pemilik_lama} -> {pemilik} tanpa pasangan ulurkan/terima"))
                elif aksi == "terima":
                    hasil.append(Temuan("PERIKSA", "BARANG_TANPA_ADEGAN_ULUR",
                                        f"{lokasi} {iid}: adegan terima tidak punya shot ulurkan sebelumnya"))
            for iid in sebelumnya:
                if iid not in sekarang:
                    hasil.append(Temuan("PERIKSA", "BARANG_TIDAK_DIBAWA",
                                        f"{lokasi}: barang {iid} dari shot sebelumnya tidak dicantumkan; periksa kesinambungan"))
            sebelumnya = sekarang
    return hasil


def periksa_kontinuitas_panggung(rencana: dict[str, Any]) -> list[Temuan]:
    """Periksa tumpang-tindih tokoh dan kestabilan blocking antar-shot dalam satu beat.

    Tokoh kolektif diringkas ke pusat kelompok (median x). Ambang bersifat
    heuristik dan hanya menghasilkan PERIKSA agar tidak menghalangi variasi
    komposisi yang memang disengaja.
    """
    hasil: list[Temuan] = []
    for bi, beat in enumerate(rencana.get("beat", [])):
        posisi_shot: list[dict[str, float]] = []
        for si, shot in enumerate(beat.get("shot", [])):
            tokoh = [t for t in shot.get("tokoh", []) if isinstance(t.get("peran"), str)]
            pusat: dict[str, list[float]] = {}
            for t in tokoh:
                x = t.get("x")
                if isinstance(x, list) and x:
                    try:
                        x = float(x[0][1])
                    except (TypeError, ValueError, IndexError):
                        continue
                if isinstance(x, (int, float)):
                    pusat.setdefault(t["peran"], []).append(float(x))
            ringkas = {pid: sorted(xs)[len(xs)//2] for pid, xs in pusat.items() if xs}
            posisi_shot.append(ringkas)

            # Anggota dalam satu kelompok (peran sama) memang boleh berdekatan.
            # Hanya bandingkan pemeran berbeda pada bidang kedalaman yang sama.
            daftar = []
            for t in tokoh:
                x, y = t.get("x"), t.get("y")
                if isinstance(x, list) and x:
                    try:
                        x = float(x[0][1])
                    except (TypeError, ValueError, IndexError):
                        continue
                if isinstance(y, list) and y:
                    try:
                        y = float(y[0][1])
                    except (TypeError, ValueError, IndexError):
                        continue
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    daftar.append((t["peran"], float(x), float(y), float(t.get("s", .68))))
            sudah: set[tuple[str, str]] = set()
            for i, a in enumerate(daftar):
                for b in daftar[i+1:]:
                    if a[0] == b[0]:
                        continue
                    pasangan = tuple(sorted((a[0], b[0])))
                    if pasangan in sudah:
                        continue
                    sudah.add(pasangan)
                    ambang_x = 92.0 * (a[3] + b[3]) / 1.36
                    if abs(a[1]-b[1]) < ambang_x and abs(a[2]-b[2]) < 105:
                        hasil.append(Temuan(
                            "PERIKSA", "TOKOH_BERTUMPUK",
                            f"beat {bi} shot {si}: {a[0]} dan {b[0]} terlalu berdekatan; atur jarak atau kedalaman, kecuali memang disengaja",
                        ))
        for si in range(1, len(posisi_shot)):
            sebelumnya, sekarang = posisi_shot[si-1], posisi_shot[si]
            for pid in set(sebelumnya) & set(sekarang):
                if abs(sebelumnya[pid] - sekarang[pid]) > 90:
                    hasil.append(Temuan(
                        "PERIKSA", "POSISI_BERUBAH_ANTAR_SHOT",
                        f"beat {bi} shot {si}: posisi {pid} berubah {sebelumnya[pid]:.0f} -> {sekarang[pid]:.0f}; pertahankan blocking atau jelaskan perpindahan",
                    ))
    return hasil
