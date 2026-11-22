"""Adapter data Kisah Islami menuju bentuk karakter netral."""
import copy

def adaptasi_shot(rencana,shot):
    peran={p["id"]:p for p in rencana.get("peran",[])};pemeran={p["id"]:p for p in rencana.get("pemeran",[])}
    for tokoh in shot.get("tokoh",[]):
        p=peran.get(tokoh.get("peran"))
        if not p:continue
        tokoh["_kategori_peran"]=p["kategori"];tokoh["_mode_render"]="siluet" if p.get("tampil")=="siluet" else "pakaian";tokoh["_wajah_cahaya"]=p.get("kategori")=="sahabat"
        kartu=pemeran.get(tokoh.get("pemeran_id"));tokoh["_identitas_render"]=copy.deepcopy(kartu.get("identitas",{}) if kartu else p.get("identitas",{}))
        if kartu:tokoh["_id_pemeran"]=kartu["id"]
    for cahaya in shot.get("nur",[]):
        p=peran.get(cahaya.get("peran"))
        if p is None and cahaya.get("nama"):p=next((v for v in peran.values() if v.get("nama")==cahaya["nama"]),None)
        if p:cahaya["_kategori_peran"]=p["kategori"];cahaya["_cara_tampil"]=p["tampil"]
    return shot

def data_render(rencana):return {d["id"]:d for d in rencana.get("dalil",[])}
