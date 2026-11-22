"""Menyusun satu bingkai dari shot dengan lapisan netral genre."""
from __future__ import annotations
import random
from . import kamera as KM
from .gaya import dasar,latar as LT,teks as TX,tokoh as TK
from .genre import HasilAdegan,ambil
from .waktu import pada
DURASI_BAWAAN=3.0
def _npc_jauh(spec,tg):
    rnd=random.Random(spec.get("seed",11)); n,x0,x1,y=spec.get("n",10),spec.get("x0",80),spec.get("x1",1000),spec.get("y",1262); out=[]
    for k in range(n):
        x=x0+(x1-x0)*(k/max(n-1,1))+rnd.uniform(-14,14); yy=y+rnd.uniform(-6,10)
        s,g=rnd.uniform(.34,.42),rnd.choice(["silang","tertawa","tunjuk","angkat","berdiri","pinggang"]); kp=rnd.choice(["imamah","kain","kopiah"])
        out.append((yy,TK.orang(x,yy,s,gerak=spec.get("gerak",g),t=tg+k*.37,indeks=k+3,kepala=kp,rinci=False)))
    return [svg for _,svg in sorted(out)]
def _muncul(svg,mulai,t,cy):
    if t<mulai:return ""
    u=min(1.0,(t-mulai)/.15); s=.85+.15*(1-(1-u)**3)
    return f'<g opacity="{u:.3f}" transform="translate(540,{cy}) scale({s:.4f}) translate(-540,{-cy})">{svg}</g>'
def susun(shot,t=0.0,tg=None,data_render=None,sub=None,*,genre=None,**opsi_kompat):
    if opsi_kompat:
        if data_render is not None or len(opsi_kompat) != 1:
            raise TypeError("opsi kompatibilitas renderer hanya menerima satu peta data")
        data_render = next(iter(opsi_kompat.values()))
    tg=t if tg is None else tg; paket=ambil(genre); sp=pada(shot,t); preset=sp["preset"]
    hasil=paket.renderer_adegan(shot,sp,t,tg,data_render or {}) if paket.renderer_adegan else HasilAdegan()
    if not isinstance(hasil,HasilAdegan):raise TypeError(f"renderer paket {paket.nama!r} harus mengembalikan HasilAdegan")
    dunia=[LT.langit(preset,matahari=tuple(sp["matahari"]) if sp.get("matahari") else None)]
    for latar in sp.get("belakang",["gunung"]):dunia.append({"gunung":LT.gunung,"kota":LT.kota}[latar](preset))
    if sp.get("npc_jauh"):dunia.append(LT.kabut_jauh(preset))
    tanah_y=sp.get("tanah_y",1250);dunia.append(LT.tanah(preset,tanah_y))
    permukaan=sp.get("permukaan_tanah",LT.PERMUKAAN_BAWAAN[preset])
    if permukaan!="tanpa":dunia.append(LT.tekstur_tanah(preset,tanah_y,jenis=permukaan,seed=sp.get("seed_tanah",3)))
    dunia.extend(hasil.latar)
    if sp.get("npc_jauh"):dunia+=_npc_jauh(sp["npc_jauh"],tg)
    tengah=list(hasil.tengah)
    for i,(tk,asli) in enumerate(zip(sp.get("tokoh",[]),shot.get("tokoh",[]))):
        ident=tk.get("_identitas_render") or {}
        tengah.append((tk["y"],TK.orang(tk["x"],tk["y"],tk.get("s",1),gerak=asli.get("gerak",asli.get("pose","berdiri")),t=t+i*.37,
            indeks=tk.get("indeks",i),mode=tk.get("_mode_render",tk.get("mode","pakaian")),kepala=tk.get("kepala"),jenis=tk.get("jenis","pria"),
            wajah=asli.get("wajah","datar"),arah=asli.get("arah",tk.get("arah","depan")),usia=tk.get("usia","dewasa"),zaman=tk.get("zaman","arab_kuno"),
            bicara=asli.get("bicara"),detail_wajah=asli.get("detail_wajah"),balik=tk.get("balik",False),wajah_cahaya=bool(tk.get("_wajah_cahaya",False)),gambar_item=paket.komponen.get("aktor.item"),
            barang=hasil.barang_pemilik.get(asli.get("peran"),[]),target_tangan=hasil.target_tangan.get(asli.get("peran")),
            warna_kulit=ident.get("warna_kulit"),warna_baju=ident.get("warna_baju"),warna_aksen=ident.get("warna_aksen"),rambut=ident.get("rambut"),
            janggut=ident.get("janggut","pendek"),warna_janggut=ident.get("warna_janggut"))))
    dunia += [svg for _,svg in sorted(tengah,key=lambda a:a[0])];dunia.extend(hasil.overlay)
    lapis=[f'<g transform="{KM.transform(sp.get("kamera"),t)}">'+"\\n".join(dunia)+"</g>"]
    if sp.get("depan",False):
        kx=float((sp.get("kamera") or {}).get("x",540));lapis.append(f'<g transform="translate({-(kx-540)*.35:.1f},0)">{LT.batu_depan(sp.get("warna_depan","#120c16"))}</g>')
    teks=sp.get("teks") or {}
    if hasil.sembunyikan_judul:teks={k:v for k,v in teks.items() if k not in ("sumber","judul")}
    if teks.get("sumber"):lapis.append(TX.sumber(teks["sumber"]))
    if teks.get("judul") and t<teks.get("judul_sampai",1e9):lapis.append(_muncul(TX.judul(teks["judul"],warna=teks.get("warna","putih")),teks.get("judul_mulai",0.0),t,380))
    lapis.extend(hasil.overlay_ui)
    if sub:lapis.append(TX.subtitle_frasa(sub[0],sub[1]))
    elif teks.get("subtitle"):lapis.append(_muncul(TX.subtitle(teks["subtitle"],sorot=teks.get("sorot")),teks.get("subtitle_mulai",0.0),t,1700))
    return dasar.dokumen("\\n".join(lapis))
def durasi(shot,data_render=None,*,genre=None):
    if "durasi" in shot:return float(shot["durasi"])
    paket=ambil(genre)
    if paket.durasi_shot:
        hasil=paket.durasi_shot(shot,data_render or {})
        if hasil is not None:return float(hasil)
    return DURASI_BAWAAN
