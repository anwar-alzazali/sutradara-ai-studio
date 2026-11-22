"""Ayat Al-Qur'an dari API resmi Quran Foundation (Content API v4, OAuth2 client credentials).

Asal: motion-studio-ai/providers/quran_foundation.py (19 Nov 2026), disederhanakan menjadi kelas mandiri.
- Kunci dari env QURAN_FOUNDATION_CLIENT_ID / QURAN_FOUNDATION_CLIENT_SECRET (GitHub Secrets). Tidak pernah dicetak.
- Teks Arab (uthmani) & terjemahan dipakai APA ADANYA; hanya tanda catatan kaki/markup yang dibuang.
- Terjemahan: Indonesia, utamakan Kemenag bila tersedia. Cache berkas maks. 7 hari (data/cache, tidak masuk git).
- Kunci baru sering hanya aktif di lingkungan prelive -> dicoba otomatis.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .unduh_hadis import AKAR

AUTH = {"production": "https://oauth2.quran.foundation", "prelive": "https://prelive-oauth2.quran.foundation"}
API = {"production": "https://apis.quran.foundation", "prelive": "https://apis-prelive.quran.foundation"}
CACHE = AKAR / "data/cache/quran"
UMUR_CACHE = 7 * 24 * 3600
# Keputusan Tahap C: bacaan latin belum boleh tampil sebelum diminta pemilik.
FITUR_BACAAN_LATIN = False
UA = "sutradara-ai-studio/0.1 (python-urllib)"
# Klien baru Quran Foundation memegang scope RINCI (datar, tidak saling mewarisi); klien lama memegang `content`.
# Diminta berurutan: rinci -> content -> tanpa scope. Ayat butuh quran.read, terjemah butuh translations.read.
SCOPE_RINCI = "content.quran.read content.translations.read content.metadata.read"
URUTAN_SCOPE = (SCOPE_RINCI, "content.quran.read content.translations.read", "content", "")


@dataclass
class Ayat:
    surah: int
    ayat: int
    nama_surah: str
    ar: str
    terjemah: str
    sumber_terjemah: str
    kata: list[dict] = field(default_factory=list)

    @property
    def kunci(self) -> str:
        return f"{self.surah}:{self.ayat}"

    @property
    def tautan(self) -> str:
        return f"https://quran.com/{self.surah}/{self.ayat}"


def _http(metode: str, url: str, kepala: dict, data: bytes | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(url, data, {"User-Agent": UA, "Accept": "application/json", **kepala}, method=metode)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read()[:400] or b"{}")
        except ValueError:
            return e.code, {}


def bersihkan(teks: str) -> str:
    teks = re.sub(r"<sup[^>]*>.*?</sup>", "", teks or "", flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", teks)).strip()


class QuranFoundation:
    def __init__(self, *, transport: Callable[..., tuple[int, dict]] | None = None, cache: Path | None = CACHE,
                 lingkungan: str = "production", bahasa: str = "indonesian"):
        self.transport, self.cache, self.env, self.bahasa = transport or _http, cache, lingkungan, bahasa
        self._token, self._habis, self._terjemah, self._surah = None, 0.0, None, None

    def _kunci(self) -> tuple[str, str]:
        cid, sec = os.environ.get("QURAN_FOUNDATION_CLIENT_ID", ""), os.environ.get("QURAN_FOUNDATION_CLIENT_SECRET", "")
        if (not cid or not sec) and self.transport is _http:
            raise RuntimeError("QURAN_FOUNDATION_CLIENT_ID / _SECRET belum diisi (GitHub Secrets)")
        return cid, sec

    def _akses(self, paksa: bool = False) -> str:
        if self._token and not paksa and time.time() < self._habis - 60:
            return self._token
        cid, sec = self._kunci()
        basic = base64.b64encode(f"{cid}:{sec}".encode()).decode()
        gagal = []
        for env in [self.env] + [e for e in AUTH if e != self.env]:
            for scope in URUTAN_SCOPE:
                form = ("grant_type=client_credentials" + (f"&scope={urllib.parse.quote(scope)}" if scope else "")).encode()
                st, body = self.transport("POST", AUTH[env] + "/oauth2/token",
                                          {"Authorization": "Basic " + basic, "Content-Type": "application/x-www-form-urlencoded"}, form)
                if st == 200 and body.get("access_token"):
                    self.env, self._token = env, body["access_token"]
                    self._habis = time.time() + float(body.get("expires_in", 3600))
                    return self._token
                gagal.append(f"{env}: HTTP {st} {body.get('error', '')}")
                if body.get("error") != "invalid_scope":
                    break
        raise RuntimeError("token Quran Foundation gagal (" + "; ".join(gagal) + ")")

    def _get(self, jalur: str) -> dict | None:
        for coba in (0, 1):
            token = self._akses(paksa=coba == 1)
            st, body = self.transport("GET", API[self.env] + "/content/api/v4" + jalur, {"x-auth-token": token, "x-client-id": self._kunci()[0]}, None)
            if st == 401 and coba == 0:
                continue
            if st == 404:
                return None
            if st != 200:
                raise RuntimeError(f"Quran Foundation {jalur.split('?')[0]} gagal (HTTP {st})")
            return body
        return None

    def _tersimpan(self, nama: str, ambil):
        f = self.cache / f"{nama}.json" if self.cache else None
        if f and f.exists() and time.time() - f.stat().st_mtime < UMUR_CACHE:
            return json.loads(f.read_text(encoding="utf-8"))
        data = ambil()
        if f and data is not None:
            f.parent.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def diagnosa(self) -> list[dict]:
        """Status tiap lingkungan x scope TANPA mencetak token/rahasia (untuk mencari penyebab 401/403)."""
        cid, sec = self._kunci()
        basic = base64.b64encode(f"{cid}:{sec}".encode()).decode()
        hasil = []
        for env in AUTH:
            for scope in URUTAN_SCOPE:
                form = ("grant_type=client_credentials" + (f"&scope={urllib.parse.quote(scope)}" if scope else "")).encode()
                st, body = self.transport("POST", AUTH[env] + "/oauth2/token",
                                          {"Authorization": "Basic " + basic, "Content-Type": "application/x-www-form-urlencoded"}, form)
                baris = {"env": env, "scope_diminta": scope or "(tanpa)", "token_http": st, "token": bool(body.get("access_token")),
                         "scope_diberi": body.get("scope"), "error": body.get("error")}
                if body.get("access_token"):
                    for nama, jalur in (("ayat", "/verses/by_key/1:1"), ("terjemahan", "/resources/translations"), ("surah", "/chapters/1")):
                        s2, b2 = self.transport("GET", API[env] + "/content/api/v4" + jalur, {"x-auth-token": body["access_token"], "x-client-id": cid}, None)
                        baris[nama] = f"HTTP {s2} {str(b2.get('message') or b2.get('error') or '')[:80]}".strip()
                hasil.append(baris)
        return hasil

    def terjemahan(self) -> dict:
        if self._terjemah is None:
            daftar = (self._tersimpan("terjemahan", lambda: self._get("/resources/translations")) or {}).get("translations", [])
            bhs = [t for t in daftar if (t.get("language_name") or "").lower() == self.bahasa]
            pilih = next((t for t in bhs if any(p in ((t.get("name") or "") + " " + (t.get("author_name") or "")).lower()
                                                 for p in ("ministry", "kementerian", "kemenag", "islamic affairs"))), None) or (bhs[0] if bhs else None)
            if not pilih:
                raise RuntimeError(f"tidak ada terjemahan {self.bahasa}")
            self._terjemah = {"id": pilih["id"], "nama": pilih.get("name") or pilih.get("author_name") or ""}
        return self._terjemah

    def nama_surah(self, n: int) -> str:
        if self._surah is None:
            daftar = (self._tersimpan("surah", lambda: self._get("/chapters?language=id")) or {}).get("chapters", [])
            self._surah = {c["id"]: c.get("name_simple", "") for c in daftar}
        return self._surah.get(n, "")

    def ayat(self, surah: int, ayat: int) -> Ayat | None:
        if not (1 <= surah <= 114 and ayat >= 1):
            return None
        tr = self.terjemahan()
        body = self._tersimpan(f"ayat_{surah}_{ayat}_{tr['id']}_wbw",
                               lambda: self._get(f"/verses/by_key/{surah}:{ayat}?translations={tr['id']}&fields=text_uthmani&words=true&language=id&word_fields=text_uthmani"))
        v = (body or {}).get("verse")
        if not v or not v.get("text_uthmani"):
            return None
        t = next((bersihkan(x.get("text", "")) for x in v.get("translations", []) if x.get("resource_id") == tr["id"]), None) \
            or next((bersihkan(x.get("text", "")) for x in v.get("translations", [])), "")
        kata_api = v.get("words") or []
        pasangan = []
        for kata in kata_api:
            ar_kata = kata.get("text_uthmani", "").strip()
            terjemah_kata = kata.get("translation") or {}
            id_kata = bersihkan(terjemah_kata.get("text", "")) if isinstance(terjemah_kata, dict) else ""
            if ar_kata and id_kata:
                pasangan.append({"ar": ar_kata, "id": id_kata})
        # Jangan membuat pasangan proporsional lalu menyebutnya word-by-word.
        if len(pasangan) != len(kata_api):
            pasangan = []
        return Ayat(surah, ayat, self.nama_surah(surah), v["text_uthmani"], t, tr["nama"], pasangan)


class QuranComPublik(QuranFoundation):
    """API publik quran.com v4 (tanpa kunci) dari penyedia yang sama (Quran Foundation). Dipakai OTOMATIS hanya bila
    klien Content API berkunci ditolak karena belum diberi scope `content`. Bentuk data & aturan sama; sumber ditandai."""
    DASAR = "https://api.quran.com/api/v4"

    def _kunci(self):
        return "", ""

    def _get(self, jalur: str) -> dict | None:
        st, body = self.transport("GET", self.DASAR + jalur, {}, None)
        if st == 404:
            return None
        if st != 200:
            raise RuntimeError(f"quran.com {jalur.split('?')[0]} gagal (HTTP {st})")
        return body

    def ayat(self, surah: int, ayat: int):
        a = super().ayat(surah, ayat)
        if a:
            a.sumber_terjemah = f"{a.sumber_terjemah} via quran.com API publik"
        return a


_UTAMA_BAWAAN = object()


class QuranBertingkat:
    """Coba Quran Foundation berkunci; bila tidak tersedia/ditolak, gunakan API publik quran.com."""

    def __init__(self, utama=_UTAMA_BAWAAN, cadangan=None):
        # None eksplisit berarti sengaja melewati klien berkunci (mis. CI publik tanpa secret).
        self.utama = QuranFoundation() if utama is _UTAMA_BAWAAN else utama
        self.cadangan = cadangan if cadangan is not None else QuranComPublik()
        self.catatan = None

    def ayat(self, surah: int, ayat: int):
        if self.utama is not None:
            try:
                return self.utama.ayat(surah, ayat)
            except RuntimeError as e:
                if "HTTP 403" not in str(e) and "HTTP 401" not in str(e):
                    raise
                self.catatan = f"Quran Foundation berkunci ditolak ({e}); memakai API publik quran.com"
                self.utama = None
        return self.cadangan.ayat(surah, ayat)
