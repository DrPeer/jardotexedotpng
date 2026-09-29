#!/usr/bin/env python3
"""Sprawdza, czy strona z aplikacją jest PRYWATNA (za bramką logowania),
czy publicznie dostępna.

Uruchomienie:
    python3 tools/check_private.py https://moj-portfel.pages.dev

Jak to działa (bez żadnych zależności):
  * pobiera stronę jak anonimowy gość (bez ciasteczek, bez logowania),
  * jeśli dostanie 401/403 → bramka działa,
  * jeśli dostanie przekierowanie na domenę logowania (Cloudflare Access,
    Netlify, Vercel, GitHub) → bramka działa,
  * jeśli dostanie 200 i w treści widać naszą aplikację → strona jest PUBLICZNA.

Kod wyjścia: 0 = chroniona, 1 = publiczna, 2 = nie udało się sprawdzić.
"""
from __future__ import annotations

import re
import ssl
import sys
import urllib.error
import urllib.request

UA = "mObywatel-check-private/1.0 (+test prywatnosci wlasnej strony)"

# Domeny, na które przekierowuje bramka logowania
LOGIN_HOSTS = (
    "cloudflareaccess.com", "login.microsoftonline.com", "accounts.google.com",
    "github.com/login", "app.netlify.com", "vercel.com/sso", "auth0.com",
    "okta.com", "duosecurity.com",
)

# Charakterystyczne fragmenty naszej aplikacji
APP_MARKERS = ("mObywatel", "kopia poglądowa", "Cyfrowy portfel", "manifest.webmanifest")


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    ctx = ssl.create_default_context()
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    try:
        with opener.open(req, timeout=20) as resp:
            return resp.status, resp.geturl(), resp.read(200_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(200_000).decode("utf-8", "replace")
        except Exception:
            pass
        return e.code, e.geturl() if hasattr(e, "geturl") else url, body
    except Exception as e:  # noqa: BLE001
        return None, url, f"BŁĄD: {e}"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    url = sys.argv[1]
    if not re.match(r"^https?://", url):
        url = "https://" + url

    status, final_url, body = fetch(url)
    print(f"  adres         : {url}")
    print(f"  odpowiedź     : {status if status is not None else '—'}")
    print(f"  finalny adres : {final_url}")

    if status is None:
        print("\n  NIE UDAŁO SIĘ SPRAWDZIĆ — " + body)
        return 2

    if any(h in final_url for h in LOGIN_HOSTS):
        print("\n  ✅ CHRONIONE — ruch przekierowany na ekran logowania bramki.")
        return 0

    if status in (401, 403):
        print("\n  ✅ CHRONIONE — serwer odmawia dostępu bez hasła/logowania.")
        return 0

    if status == 200:
        found = [m for m in APP_MARKERS if m.lower() in body.lower()]
        if found:
            print(f"\n  ❌ PUBLICZNE — każdy może otworzyć aplikację (rozpoznane elementy: {', '.join(found)}).")
            print("     Zabezpiecz ją: deploy/PRYWATNY-HOSTING.md → Opcja A (Cloudflare Access).")
            return 1
        print("\n  ❓ Odpowiedź 200, ale nie rozpoznaję aplikacji w treści. Sprawdź stronę ręcznie")
        print("     w oknie prywatnym: jeśli widzisz swój portfel, jest publiczna.")
        return 1

    print(f"\n  ❓ Nietypowa odpowiedź ({status}) — sprawdź ręcznie w oknie prywatnym.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
