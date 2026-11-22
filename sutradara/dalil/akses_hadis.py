"""Pemeriksaan akses Quran Foundation untuk endpoint hadis; tidak pernah mencetak kredensial/token."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

ENVIRONMENTS = {
    "production": ("https://oauth2.quran.foundation", "https://apis.quran.foundation"),
    "prelive": ("https://prelive-oauth2.quran.foundation", "https://apis-prelive.quran.foundation"),
}
SCOPE = "content.hadith.read"
UA = "sutradara-ai-studio/0.1"


def _request(url: str, *, headers: dict, data: bytes | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read()[:4096] or b"{}")
        except (ValueError, OSError):
            body = {}
        return exc.code, body
    except urllib.error.URLError:
        return 0, {"error": "network_unavailable"}


def periksa_lingkungan(env: str) -> dict:
    """Minta scope hadis granular; deteksi akses legacy content tanpa menyamakannya dengan scope granular."""
    if env not in ENVIRONMENTS:
        raise ValueError(f"Lingkungan tidak dikenal: {env}")
    client_id = os.environ.get("QURAN_FOUNDATION_CLIENT_ID", "")
    secret = os.environ.get("QURAN_FOUNDATION_CLIENT_SECRET", "")
    if not client_id or not secret:
        return {"lingkungan": env, "status": "terblokir", "alasan": "GitHub Secrets QURAN_FOUNDATION_CLIENT_ID/SECRET kosong"}
    auth_url, api_url = ENVIRONMENTS[env]
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()

    def minta_token(scope: str) -> tuple[int, dict]:
        payload = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": scope}).encode()
        return _request(
            auth_url + "/oauth2/token",
            headers={"Authorization": "Basic " + basic, "Content-Type": "application/x-www-form-urlencoded"},
            data=payload,
        )

    status, token_body = minta_token(SCOPE)
    if not isinstance(token_body, dict):
        token_body = {}
    hasil = {"lingkungan": env, "scope_diminta": SCOPE, "token_http": status}
    token = token_body.get("access_token")
    scope_diberi = token_body.get("scope") or ""
    akses_legacy = False

    # Klien Quran Foundation lama dapat memakai scope payung content; laporkan terpisah,
    # jangan menganggapnya sebagai bukti bahwa scope granular sudah terpasang.
    if not token and token_body.get("error") == "invalid_scope":
        hasil["scope_cadangan"] = "content (legacy)"
        status, token_body = minta_token("content")
        if not isinstance(token_body, dict):
            token_body = {}
        hasil["token_legacy_http"] = status
        token = token_body.get("access_token")
        scope_diberi = token_body.get("scope") or "content"
        akses_legacy = bool(token)

    if not token:
        hasil.update(status="tidak_terbukti", alasan=str(token_body.get("error") or "token tidak diberikan"))
        return hasil

    hasil["scope_diberi"] = scope_diberi or "(tidak dikembalikan)"
    endpoint_status, endpoint_body = _request(
        api_url + "/content/api/v4/hadiths/by_ayah/1:1?language=ar&page=1&limit=1",
        headers={"x-auth-token": token, "x-client-id": client_id},
    )
    if not isinstance(endpoint_body, dict):
        endpoint_body = {}
    hasil["endpoint_hadis_http"] = endpoint_status
    if endpoint_status == 200 and isinstance(endpoint_body.get("hadiths"), list):
        if akses_legacy or (scope_diberi and "content" in scope_diberi.split() and SCOPE not in scope_diberi.split()):
            hasil.update(status="akses_legacy_content", alasan="Endpoint hadis dapat dibaca melalui scope payung legacy; scope granular belum terbukti")
        else:
            hasil.update(status="lulus", alasan="Token diterima dan endpoint hadis mengembalikan struktur yang sah")
    else:
        error = endpoint_body.get("error")
        jenis = endpoint_body.get("type") or (error.get("code") if isinstance(error, dict) else error)
        hasil.update(status="tidak_terbukti", alasan=f"Endpoint hadis menolak/gagal (HTTP {endpoint_status}; {jenis or 'tanpa kode'})")
    return hasil

def main() -> int:
    if not os.environ.get("QURAN_FOUNDATION_CLIENT_ID") or not os.environ.get("QURAN_FOUNDATION_CLIENT_SECRET"):
        print("TERBLOKIR: isi GitHub Secrets QURAN_FOUNDATION_CLIENT_ID dan QURAN_FOUNDATION_CLIENT_SECRET.")
        return 2
    hasil = [periksa_lingkungan(env) for env in ENVIRONMENTS]
    for item in hasil:
        print(" | ".join(f"{k}={v}" for k, v in item.items()))
    # Hanya scope granular di production yang meluluskan pemeriksa ini. Akses legacy
    # tetap dilaporkan, tetapi bukan bukti bahwa content.hadith.read telah diberikan.
    return 0 if any(x["lingkungan"] == "production" and x["status"] == "lulus" for x in hasil) else 1


if __name__ == "__main__":
    raise SystemExit(main())
