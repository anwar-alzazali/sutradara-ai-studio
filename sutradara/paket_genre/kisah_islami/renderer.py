"""Renderer elemen adegan khusus Kisah Islami."""
from sutradara.genre import HasilAdegan
from .visual import akhir_zaman,benda,dajjal,kartu,malaikat,makhluk,nur

def _cahaya(n,t):
    if n.get("_kategori_peran")=="malaikat":return malaikat.berkas(n["x"],n["y"],tinggi=n.get("tinggi",620),lebar=n.get("lebar",260),t=t,seed=n.get("seed",17))
    return nur.pilar(n["x"],n["y"],nama=n.get("nama"),sinar_ke=n.get("sinar_ke","kanan"),tinggi=n.get("tinggi",400),lebar=n.get("lebar",118),pendar_rx=n.get("pendar_rx",155),pendar_ry=n.get("pendar_ry",190),t=t)

def render_adegan(shot,sp,t,tg,data):
    latar=[];tengah=[];overlay=[];barang_pemilik={};target_tangan={}
    for n in sp.get("nur",[]):
        if n.get("di_belakang_benda"):latar.append(_cahaya(n,tg))
    for b in sp.get("buraq",[]):latar.append(akhir_zaman.buraq(b["x"],b["y"],b.get("s",1),t=tg))
    for b in sp.get("akhir_zaman",[]):
        j=b["jenis"]
        if j=="dinding_yajuj":latar.append(akhir_zaman.dinding_yajuj(b["x"],b["y"],b.get("s",1),lubang=b.get("lubang",0)))
        elif j=="danau_surut":latar.append(akhir_zaman.danau_surut(b["x"],b["y"],b.get("s",1),surut=b.get("surut",0)))
        elif j=="tanda_wajah":overlay.append(akhir_zaman.tanda_wajah(b["x"],b["y"],b.get("s",1)))
        else:raise ValueError(f"komponen akhir zaman tak dikenal: {j}")
    for b in sp.get("benda",[]):
        j=b["jenis"]
        if j=="bahtera":latar.append(benda.bahtera(b["x"],b["y"],b.get("s",1),jadi=b.get("jadi",1),goyang=b.get("goyang",0),cahaya=b.get("cahaya",.8),pintu=b.get("pintu",0),orang=int(b.get("orang",0)),darat=b.get("darat",True),t=tg))
        elif j=="lapak":latar.append(benda.lapak(b["x"],b["y"],b.get("warna","#b8452e")))
        elif j=="sungai":latar.append(benda.sungai(b["isi"],sisi=b["sisi"],t=tg))
        elif j=="bukit":latar.append(f'<path d="M300 1260 Q 540 1060 780 1260Z" fill="{b.get("warna","#160e18")}"/>')
        elif j=="kota_kuno":latar.append(benda.kota_kuno(b["x"],b["y"],b.get("s",1),runtuh=b.get("runtuh",0)))
        elif j=="angin":latar.append(benda.angin(b["x"],b["y"],b.get("kuat",0),t=tg,seed=b.get("seed",19)))
        elif j=="dinding_yajuj":latar.append(akhir_zaman.dinding_yajuj(b["x"],b["y"],b.get("s",1),lubang=b.get("lubang",0)))
        else:raise ValueError(f"benda tak dikenal: {j}")
    for item in sp.get("barang",[]):
        owner=item.get("pemilik")
        if not owner:raise ValueError(f"barang {item.get('id','?')} wajib memiliki pemilik")
        aksi=item.get("aksi","pegang");hand=item.get("tangan","ka")
        if item.get("posisi_genggam") is not None:
            pos=item["posisi_genggam"]
            if not isinstance(pos,(list,tuple)) or len(pos)!=2:raise ValueError(f"barang {item.get('id','?')} posisi_genggam harus [x, y]")
            target_tangan.setdefault(owner,{})[hand]=tuple(pos)
        if aksi in {"ulurkan","terima"}:
            titik=item.get("titik_serah")
            if not isinstance(titik,(list,tuple)) or len(titik)!=2:raise ValueError(f"barang {item.get('id','?')} aksi {aksi} wajib memiliki titik_serah [x, y]")
            target_tangan.setdefault(owner,{})[hand]=tuple(titik);pasangan=item.get("penerima") if aksi=="ulurkan" else item.get("pemberi")
            if pasangan:target_tangan.setdefault(pasangan,{})[item.get("tangan_pasangan","ka")]=tuple(titik)
        kategori=next((x.get("_kategori_peran") for x in shot.get("tokoh",[]) if x.get("peran")==owner),None)
        kategori=kategori or next((x.get("_kategori_peran") for x in shot.get("nur",[]) if x.get("peran")==owner),None)
        if kategori=="nabi":
            pilar=next((x for x in sp.get("nur",[]) if x.get("peran")==owner),None)
            if pilar is None:raise ValueError(f"barang {item.get('id','?')} milik nabi {owner} tetapi pilar tidak ada di shot")
            svg=benda.barang(pilar["x"]+item.get("sisi_x",105),pilar["y"]+item.get("sisi_y",-65),item["jenis"],angle=item.get("angle",-35),s=item.get("skala",.8),warna=item.get("warna"),cahaya=True)
            tengah.append((pilar["y"]+item.get("sisi_y",-65),svg))
        else:barang_pemilik.setdefault(owner,[]).append({"jenis":item["jenis"],"tangan":hand,"skala":item.get("skala",.72),"warna":item.get("warna")})
    for m in sp.get("kabut_tanpa_wujud",[]):
        svg=(makhluk.retakan(m["x"],m["y"]) if m.get("retakan",True) else "")+makhluk.kabut_tanpa_wujud(m["x"],m["y"],tinggi=m.get("tinggi",820),keluar=m.get("keluar",1),t=tg);tengah.append((m["y"]-1,svg))
    for n in sp.get("nur",[]):
        if not n.get("di_belakang_benda"):tengah.append((n["y"],_cahaya(n,tg)))
    for d in sp.get("dajjal",[]):
        svg=dajjal.belakang(d["x"],d["y"],d.get("s",1),t=tg,jalan=d.get("jalan",False),jubah_berkibar=d.get("jubah_berkibar",0),buka=d.get("buka",0)) if d.get("arah")=="belakang" else dajjal.sosok(d["x"],d["y"],d.get("s",1),lengan=d.get("lengan","terbuka"));tengah.append((d["y"],svg))
    ui=[];kd=sp.get("kartu_dalil");aktif=bool(kd) and t>=kd.get("mulai",0)
    if kd:
        entri=data.get(kd["dalil"])
        if entri is None:raise ValueError(f"kartu merujuk entri {kd['dalil']!r} yang tidak ada dalam data rencana")
        ui.append(kartu.kartu(entri,kartu.potongan(entri),t,mulai=kd.get("mulai",0),idx_uid=f"kd{kd['dalil']}",preset=sp["preset"]))
    return HasilAdegan(latar=tuple(latar),tengah=tuple(tengah),overlay=tuple(overlay),barang_pemilik={k:tuple(v) for k,v in barang_pemilik.items()},target_tangan=target_tangan,overlay_ui=tuple(ui),sembunyikan_judul=aktif)

def durasi_shot(shot,data):
    if "durasi" in shot:return float(shot["durasi"])
    kd=shot.get("kartu_dalil")
    if kd and kd["dalil"] in data:return kartu.durasi_total(kartu.potongan(data[kd["dalil"]]),kd.get("mulai",0))
    return None
