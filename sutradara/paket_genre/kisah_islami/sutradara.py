"""Aturan penyutradaraan Kisah Islami dari resep yang disimpan sebagai data."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from sutradara.gaya.latar import PRESET

_RESEP = json.loads(Path(__file__).with_name("resep_adegan.json").read_text(encoding="utf-8"))["resep"]
_KATA_EMOSI = {
    "badai": ("malam_merah", "takut", "kaget"), "angin": ("malam_merah", "takut", "mundur"),
    "mengejek": ("senja", "ejek", "tertawa"), "mengolok": ("senja", "ejek", "tertawa"),
    "doa": ("malam", "sedih", "berdoa"), "memohon": ("malam", "sedih", "berdoa"),
    "selamat": ("fajar", "senyum", "berdiri"), "beriman": ("fajar", "senyum", "berdiri"),
}
_GERAK = {"membangun": "palu", "membuat": "palu", "menggali": "gali", "mengejek": "tertawa",
          "tertawa": "tertawa", "berjalan": "jalan", "melintas": "jalan", "berlari": "lari",
          "lari": "lari", "berdoa": "berdoa", "memohon": "berdoa", "mundur": "mundur"}
_JUDUL = {
    "rangka": "MULAI MEMBANGUN", "jadi": "KAPAL SELESAI", "badai": "BANJIR DATANG", "tenang": "SELAMAT",
    "seruan": "MENYERU", "menolak": "MEREKA MENOLAK", "angin": "ANGIN DATANG", "selamat": "DISELAMATKAN",
    "menggali": "TERUS MENGGALI", "hampir": "HAMPIR TEMBUS", "terbuka": "DINDING TERBUKA",
}


def _polos(teks: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", teks.lower()) if not unicodedata.combining(c))


def _slug(teks: str) -> str:
    hasil = re.sub(r"[^a-z0-9]+", "_", _polos(teks)).strip("_")
    return hasil or "peran"


_AKHIRAN_NAMA_SAKRAL = {"as", "ra", "saw", "pbuh", "radi", "anhu", "anha", "alaihi", "wasallam", "sallallahu"}
_NABI_NAMA = {
    "adam", "idris", "nuh", "noah", "hud", "saleh", "salih", "shaleh", "ibrahim", "lut", "luth",
    "ismail", "ishmael", "ishaq", "ishak", "yaqub", "yusuf", "ayyub", "ayub", "syuaib", "shuaib",
    "musa", "harun", "dzulkifli", "dhul kifl", "dawud", "daud", "sulaiman", "suleiman", "ilyas",
    "alyasa", "al yasa", "yunus", "zakariya", "zakaria", "yahya", "isa", "muhammad",
}
_SAHABAT_NAMA = {
    "aisyah", "aisha", "khadijah", "hafsah", "fatimah", "fatima", "umm salamah", "asma bint abu bakr",
    "abu bakr", "umar", "uthman", "usman", "ali", "bilal", "hamzah", "hamza", "abu hurairah",
    "zaid", "zayd", "salman al farisi", "khalid bin walid",
}
_SAHABIYAH_NAMA = {"aisyah", "aisha", "khadijah", "hafsah", "fatimah", "fatima", "umm salamah", "asma bint abu bakr"}


def _nama_kunci(nama: str) -> str:
    kata = re.sub(r"[^a-z0-9]+", " ", _polos(nama)).split()
    return " ".join(k for k in kata if k not in _AKHIRAN_NAMA_SAKRAL)


def _kategori_peran(nama: str) -> tuple[str, str]:
    """Kenali gelar dan nama sakral umum agar tidak dirender sebagai manusia biasa."""
    kunci = _nama_kunci(nama)
    kata = set(kunci.split())
    if "malaikat" in kata:
        return "malaikat", "cahaya_malaikat"
    if kata & {"nabi", "prophet", "rasul", "rasulullah"} or kunci in _NABI_NAMA:
        return "nabi", "nur"
    if kata & {"sahabat", "sahabiyah"} or kunci in _SAHABAT_NAMA:
        return "sahabat", "wajah_cahaya"
    return "manusia", "pakaian"


def _inti(naskah: dict, semua: str) -> tuple[str, list[str], float]:
    if any(x in semua for x in ("nabi nuh", "bahtera", "kapal nuh")):
        return "bahtera", ["rangka", "dibangun", "badai", "selamat"], .96
    if any(x in semua for x in ("yajuj", "ya juj", "majuj", "dinding")):
        return "dinding_yajuj", ["utuh", "dilubangi", "hampir_terbuka", "terbuka"], .90
    if any(x in semua for x in ("nabi hud", "kaum 'ad", "kaum ad", "hud 50", "hud50")):
        return "kota_kuno", ["seruan", "penolakan", "angin", "selamat"], .94
    # Latar kota adalah jangkar visual yang netral. Ambiguitas rendah keyakinan
    # meminta tinjauan model opsional; jalur aturan tetap dapat menghasilkan rencana.
    return "kota_kuno", ["awal", "peristiwa", "akibat", "pelajaran"], .42


def _peran(naskah: dict) -> tuple[list[dict], dict[str, str]]:
    nama_ke_id: dict[str, str] = {}
    for beat in naskah["beat"]:
        for nama in beat.get("peran", []):
            if nama not in nama_ke_id:
                dasar = _slug(nama)
                nama_ke_id[nama] = dasar if dasar not in nama_ke_id.values() else f"{dasar}_{len(nama_ke_id)+1}"
    if not nama_ke_id:
        raise ValueError("naskah belum menyebut peran; isi beat.peran atau buat satu peran narator visual")
    hasil = []
    for nama, pid in nama_ke_id.items():
        polos = _polos(nama)
        kategori, tampil = _kategori_peran(nama)
        kolektif = any(k in polos for k in ("kaum", "rombongan", "pengikut", "orang-orang", "pemuka"))
        p = {"id": pid, "nama": nama, "kategori": kategori, "tampil": tampil}
        if kolektif:
            p["kolektif"] = True
        if kategori in {"manusia", "sahabat"}:
            jenis = "wanita" if _nama_kunci(nama) in _SAHABIYAH_NAMA else "pria"
            p["identitas"] = {"jenis": jenis, "usia": "dewasa", "zaman": "arab_kuno",
                              "indeks": len(hasil), "warna_baju": ["#76513a", "#405d66", "#786341"][len(hasil)%3]}
        hasil.append(p)
    return hasil, nama_ke_id


def _resep_untuk(teks: str) -> dict:
    polos = _polos(teks)
    terpilih = []
    for resep in _RESEP:
        nilai = sum(1 for kata in resep["kata"] if _polos(kata) in polos)
        if nilai:
            terpilih.append((nilai, resep))
    return max(terpilih, key=lambda x: (x[0], x[1]["id"]))[1] if terpilih else {
        "id": "adegan_umum", "suasana": "senja", "gerak": "berdiri", "wajah": "datar", "fokus": "visual_inti"}


def _keadaan(inti: str, jalur: list[str], teks: str, indeks: int, jumlah: int) -> tuple[str, dict]:
    polos = _polos(teks)
    p = indeks / max(1, jumlah - 1)
    if inti == "bahtera":
        if any(k in polos for k in ("banjir", "badai", "gelombang")):
            return "badai", {"jenis": "bahtera", "x": 650, "y": 1260, "s": .78, "jadi": 1.0,
                              "goyang": .65, "cahaya": .15, "darat": False}
        state = "rangka" if p < .34 else ("dibangun" if p < .72 else "selamat")
        return state, {"jenis": "bahtera", "x": 650, "y": 1260, "s": .78,
                       "jadi": .18 + .82*p, "goyang": 0, "cahaya": .25 + .45*p, "darat": True}
    if inti == "dinding_yajuj":
        lubang = min(1.0, p)
        state = jalur[min(len(jalur)-1, round(p*(len(jalur)-1)))]
        return state, {"jenis": "dinding_yajuj", "x": 540, "y": 1120, "s": 1.0, "lubang": lubang}
    if any(k in polos for k in ("angin", "badai", "azab")):
        return "angin", {"jenis": "kota_kuno", "x": 540, "y": 1300, "s": .72, "runtuh": min(.7, .18+p*.55)}
    return jalur[min(len(jalur)-1, round(p*(len(jalur)-1)))], {
        "jenis": "kota_kuno", "x": 540, "y": 1300, "s": .72, "runtuh": 0.0}


def _preset(beat: dict, resep: dict, teks: str) -> str:
    eksplisit = beat.get("suasana")
    if eksplisit in PRESET:
        return eksplisit
    saran = resep.get("suasana", "senja")
    for kata, (preset, _wajah, _gerak) in _KATA_EMOSI.items():
        if kata in _polos(teks):
            saran = preset
    return saran if saran in PRESET else "senja"


def _aktor(pid: str, peran: dict, x: float, *, y: float = 1510, fokus: bool = False,
           wajah: str = "datar", gerak: str = "berdiri", durasi: float = 3.0,
           bicara: bool = False, arah: str = "depan", balik: bool = False, skala: float = 1.0) -> dict:
    p = peran[pid]
    a = {"peran": pid, "x": x, "y": y, "s": (1.0 if fokus else .68) * skala,
         "arah": arah, "balik": balik, "wajah": wajah, "gerak": gerak}
    if p["kategori"] in {"manusia", "sahabat"}:
        ident = p.get("identitas", {})
        a.update({k:v for k,v in ident.items() if k in {"jenis","usia","zaman","kepala","warna_baju","warna_kulit"}})
        a.setdefault("kepala", "imamah")
    if bicara and p["kategori"] not in {"nabi", "malaikat"}:
        a["bicara"] = [[.15, max(.25, durasi-.15)]]
    return a


def _shot(inti: str, keadaan: dict, preset: str, judul: list[str], narasi: str,
          dalil: list[str], dalil_label: dict[str, str], semua_peran: list[dict], nama_ke_id: dict[str, str],
          hadir: list[str], resep: dict, *, fokus: str | None = None, dialog: dict | None = None,
          pelaku: list[str] | None = None, durasi: float = 3.8, perjalanan: bool = False) -> dict:
    peta = {p["id"]: p for p in semua_peran}
    benda = [dict(keadaan)]
    if inti == "kota_kuno" and resep.get("id") == "azab_datang":
        benda.append({"jenis":"angin", "x":0, "y":1280, "kuat":.8, "seed":19})
    shot = {"preset": preset, "belakang": ["kota"] if inti == "kota_kuno" else ["gunung"],
            "benda": benda, "tokoh": [], "nur": [], "durasi": durasi,
            "kamera": {"zoom": 1.42 if fokus else 1.08, "x": 540, "y": 1240},
            "teks": {"judul": judul[:2], "warna": "kuning", "subtitle": narasi,
                     "sorot": (judul[0].lower() if judul else ""), "judul_mulai": .12}}
    if dalil:
        shot["teks"]["sumber"] = " · ".join(dalil_label[x] for x in dalil if x in dalil_label)
    posisi: dict[str, float] = {}
    gerak = resep.get("gerak", "berdiri")
    if dialog:
        p1, p2 = dialog["pembicara"], dialog.get("penjawab")
        for pid in (p1, p2):
            if pid and pid not in hadir:
                hadir.append(pid)
        posisi[p1] = 285 if peta[p1]["kategori"] == "nabi" else 380
        if p2:
            posisi[p2] = 820
    else:
        for i, pid in enumerate(hadir):
            posisi[pid] = 250 if peta[pid]["kategori"] == "nabi" else (775 + i*45 if i else 430)
    for pid in hadir:
        p = peta[pid]
        x = posisi.get(pid, 740)
        bicara = bool(dialog and pid == dialog.get("pembicara"))
        if p["kategori"] == "nabi":
            shot["nur"].append({"peran":pid,"x":x,"y":1370,"sinar_ke":"kanan" if x<540 else "kiri",
                                "nama":p["nama"],"bicara":[[.15,max(.25,durasi-.15)]] if bicara else []})
        elif p["kategori"] == "malaikat":
            shot["nur"].append({"peran":pid,"x":x,"y":1300,"_kategori_peran":"malaikat"})
        else:
            arah="samping" if dialog and dialog.get("penjawab") else "depan"
            balik=bool(dialog and pid == dialog.get("penjawab"))
            kelompok = p.get("kolektif") is True and pid != fokus and dialog is None
            xs = [x - 86, x, x + 86] if kelompok else [x]
            for xi in xs:
                a=_aktor(pid,peta,xi,fokus=(pid==fokus),wajah=resep.get("wajah","datar"),
                         gerak=resep.get("gerak","berdiri"),durasi=durasi,bicara=bicara,arah=arah,balik=balik,
                         skala=.78 if kelompok else 1.0)
                if perjalanan and pid == fokus:
                    dx = -1 if x > 540 else 1
                    ujung = max(110, min(970, x + 280*dx))
                    kecepatan = abs(ujung - x) / max(durasi, .1)
                    dasar = 120.0 if gerak == "lari" else 74.0
                    faktor = max(.45, min(2.5, kecepatan / dasar))
                    a.update(x=[[0, x],[durasi, ujung]], arah="samping", balik=(dx < 0),
                             tujuan=f"tepi:{'kiri' if dx < 0 else 'kanan'}",
                             gerak=gerak, faktor_gerak=round(faktor, 3))
                shot["tokoh"].append(a)
    if dialog and dialog.get("penjawab"):
        # Kedua lawan tetap menatap satu sama lain pada two-shot; reverse shot
        # memakai fokus tokoh masing-masing pada giliran yang sama.
        for a in shot["tokoh"]:
            a["arah"]="samping"
            a["balik"]=(a["peran"]==dialog["penjawab"])
    return shot


def rancang(naskah: dict) -> tuple[dict, float]:
    semua_teks = " ".join([naskah.get("judul",""), naskah.get("inti",""),
                           *(b.get("narasi","") for b in naskah["beat"]),
                           *(k for b in naskah["beat"] for k in b.get("kata_kunci",[])),
                           *(d.get("label", "") for d in naskah.get("dalil", []))]).lower()
    inti, jalur, yakin = _inti(naskah, semua_teks)
    peran, nama_ke_id = _peran(naskah)
    peran_map = {p["id"]:p for p in peran}
    dalil = []
    for d in naskah.get("dalil", []):
        item = dict(d)
        item.setdefault("status", "belum")
        item.setdefault("makna", "perlu_tinjauan_pemilik")
        dalil.append(item)
    label = {d["id"]:d["label"] for d in dalil}
    beat_hasil=[]
    hooks=[]
    for i, b in enumerate(naskah["beat"]):
        teks = b["narasi"]
        resep = _resep_untuk(teks)
        preset = _preset(b,resep,teks)
        hadir = [nama_ke_id[n] for n in b.get("peran",[]) if n in nama_ke_id]
        if not hadir:
            hadir = [peran[0]["id"]]
        refs = [did for did in b.get("dalil",[]) if did in label]
        tindakan = _polos(teks)
        gerak = next((v for k,v in _GERAK.items() if k in tindakan),resep.get("gerak","berdiri"))
        resep = dict(resep); resep["gerak"] = gerak
        cuts=[]
        for kata in b.get("kata_kunci",[]):
            if _polos(kata) in tindakan and len(cuts)<2:
                cuts.append(kata)
        dialog = []
        for giliran in b.get("dialog",[]):
            if not isinstance(giliran,dict):
                continue
            pembicara=nama_ke_id.get(giliran.get("pembicara"))
            penjawab=nama_ke_id.get(giliran.get("penjawab")) if giliran.get("penjawab") else None
            if pembicara:
                dialog.append({"pembicara":pembicara,"penjawab":penjawab,"ucapan":giliran.get("ucapan","")})
        if dialog:
            # Dialog membawa cerita lewat reverse shot; kata kunci tetap menjadi
            # label makna, tidak menambah potongan di luar cakupan percakapan.
            cuts=[]
        keadaan,_obj=_keadaan(inti,jalur,teks,i,len(naskah["beat"]))
        jdl=_JUDUL.get(keadaan, " ".join((cuts or b.get("kata_kunci",[]) or [keadaan])[:2]).upper())
        judul=[w for w in re.sub(r"[^A-Z0-9' ]"," ",jdl.upper()).split()[:3]]
        shots=[]
        if dialog:
            for giliran in dialog:
                for pid in ([giliran["pembicara"], giliran["penjawab"]] if giliran.get("penjawab") else [giliran["pembicara"]]):
                    g=dict(giliran); g["pembicara"]=pid
                    shots.append(_shot(inti,_obj,preset,judul,teks,refs,label,peran,nama_ke_id,list(hadir),resep,
                                       fokus=pid,dialog=g,pelaku=None))
        else:
            jumlah=1+len(cuts)
            for si in range(jumlah):
                fokus = hadir[min(si,len(hadir)-1)] if cuts else None
                shots.append(_shot(inti,_obj,preset,judul,teks,refs,label,peran,nama_ke_id,list(hadir),resep,
                                   fokus=fokus,pelaku=None,perjalanan=(gerak in {"jalan","lari"} and fokus is not None)))
        pelaku = [pid for pid in hadir if peran_map[pid]["kategori"] in {"manusia","nabi"}] if any(v in tindakan for v in ("membangun","membuat","menggali")) else None
        if pelaku:
            for s in shots:
                s["pelaku"] = pelaku
        beat_rencana={"narasi":teks,"preset":preset,"keadaan":keadaan,"potong_di":cuts,
                      "dalil":refs,"peran_tampil":hadir,"shot":shots,
                      "resep":resep["id"],"dialog":dialog}
        if pelaku:
            beat_rencana["pelaku"] = pelaku
        beat_hasil.append(beat_rencana)
        skor=sum(1 for kata in ("badai","banjir","menolak","mengejek","hancur","angin") if kata in tindakan)
        hooks.append((skor,i,judul))
    hook=max(hooks,key=lambda h:(h[0],-h[1]))
    visual={"bahtera":"bahtera","kota_kuno":"kota_kuno","dinding_yajuj":"dinding_yajuj"}[inti]
    hasil={"judul":naskah["judul"],"catatan":"Disusun otomatis dari naskah antrean dengan resep aturan lokal; periksa makna dalil dan kelayakan artistik.",
           "genre":"kisah_islami","dibuat_otomatis":True,
           "visual_inti":{"benda":visual,"jalur_keadaan":jalur},"peran":peran,
           "hook":{"dari_beat":hook[1],"teks":hook[2][:2]},"dalil":dalil,"beat":beat_hasil}
    return hasil,yakin
