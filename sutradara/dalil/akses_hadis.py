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


def periksa_lingkungan(env: str) -> dict:
    """Minta scope hadis secara eksplisit lalu uji endpoint hadis; nilai rahasia tidak masuk hasil."""
    if env not in ENVIRONMENTS:
        raise ValueError(f"Lingkungan tidak dikenal: {env}")
    client_id = os.environ.get("QURAN_FOUNDATION_CLIENT_ID", "")
    secret = os.environ.get("QURAN_FOUNDATION_CLIENT_SECRET", "")
    if not client_id or not secret:
        return {"lingkungan": env, "status": "terblokir", "alasan": "GitHub Secrets QURAN_FOUNDATION_CLIENT_ID/SECRET kosong"}
    auth_url, api_url = ENVIRONMENTS[env]
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    payload = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": SCOPE}).encode()
    status, token_body = _request(
        auth_url + "/oauth2/token",
        headers={"Authorization": "Basic " + basic, "Content-Type": "application/x-www-form-urlencoded"},
        data=payload,
    )
    hasil = {"lingkungan": env, "scope_diminta": SCOPE, "token_http": status}
    if not isinstance(token_body, dict):
        token_body = {}
    token = token_body.get("access_token")
    if status != 200 or not token:
        hasil.update(status="tidak_terbukti", alasan=str(token_body.get("error") or "token tidak diberikan"))
        return hasil
    hasil["scope_diberi"] = token_body.get("scope") or "(tidak dikembalikan)"
    endpoint_status, endpoint_body = _request(
        api_url + "/content/api/v4/hadiths/by_ayah/1:1?language=ar&page=1&limit=1",
        headers={"x-auth-token": token, "x-client-id": client_id},
    )
    hasil["endpoint_hadis_http"] = endpoint_status
    if not isinstance(endpoint_body, dict):
        endpoint_body = {}
    if endpoint_status == 200 and isinstance(endpoint_body.get("hadiths"), list):
        hasil.update(status="lulus", alasan="Token diterima dan endpoint hadis mengembalikan struktur yang sah")
    else:
        # Hanya keluarkan kategori/status; jangan menyalin pesan server yang mungkin memuat data tak terduga.
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
    return 0 if any(x["status"] == "lulus" for x in hasil) else 1


if __name__ == "__main__":
    raise SystemExit(main())
