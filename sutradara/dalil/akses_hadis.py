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
    """Uji ketiga route Hadith References v4 yang didokumentasikan; tidak pernah mencetak kredensial/token."""
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

    # Klien lama dapat memakai scope payung content; tetap dicatat terpisah dari scope granular.
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
    headers = {"x-auth-token": token, "x-client-id": client_id}
    # Route dan bentuk respons mengikuti Content API v4 Hadith References docs.
    # Ayah contoh 1:1 sengaja dipakai untuk smoke test yang deterministik.
    pemeriksaan = (
        ("referensi", "/hadith_references/by_ayah/1:1?language=en", "hadith_references"),
        ("isi_hadis", "/hadith_references/by_ayah/1:1/hadiths?language=ar&page=1&limit=1", "hadiths"),
        ("jumlah_rentang", "/hadith_references/count_within_range?from=1:1&to=1:1", "counts"),
    )
    status_endpoint = {}
    semua_valid = True
    for nama, jalur, bentuk in pemeriksaan:
        http, body = _request(api_url + "/content/api/v4" + jalur, headers=headers)
        if not isinstance(body, dict):
            body = {}
        status_endpoint[nama] = http
        if http != 200:
            semua_valid = False
        elif bentuk == "hadith_references":
            semua_valid = semua_valid and isinstance(body.get("hadith_references"), list)
        elif bentuk == "hadiths":
            semua_valid = semua_valid and isinstance(body.get("hadiths"), list)
        else:
            # count-within-range mengembalikan map verse_key -> integer count.
            semua_valid = semua_valid and bool(body) and all(
                isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool)
                for k, v in body.items()
            )

    hasil["endpoint_http"] = status_endpoint
    granular = SCOPE in scope_diberi.split()
    if semua_valid and granular and not akses_legacy:
        hasil.update(status="akses_terbukti", alasan="Ketiga route resmi Hadith References v4 dapat diakses; ini hanya bukti akses API, bukan verifikasi hadis tertentu")
    elif semua_valid:
        hasil.update(status="akses_legacy_content", alasan="Ketiga route dapat dibaca, tetapi token tidak membuktikan scope granular content.hadith.read")
    else:
        hasil.update(status="endpoint_tidak_terbukti", alasan="Satu atau lebih route resmi gagal atau bentuk respons tidak sesuai; periksa kode HTTP per endpoint")
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
    return 0 if any(x["lingkungan"] == "production" and x["status"] == "akses_terbukti" for x in hasil) else 1


if __name__ == "__main__":
    raise SystemExit(main())
