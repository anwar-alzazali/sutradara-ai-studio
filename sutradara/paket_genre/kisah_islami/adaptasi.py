"""Adapter aturan Kisah Islami ke atribut renderer karakter yang netral."""
import copy

from .peristiwa import analisis_peristiwa

def adaptasi_shot(rencana,shot):
    narasi=shot.pop("_narasi_visual","")
    peran_visual=shot.pop("_peran_visual",[])
    if narasi:
        # Renderer khusus hanya menerima peristiwa yang benar-benar disebut narasi.
        shot["peristiwa_visual"]=analisis_peristiwa(narasi,peran_visual)
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
