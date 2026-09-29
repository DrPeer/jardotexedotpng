#!/usr/bin/env python3
"""Lokalny serwer / prywatny hosting dla aplikacji mObywatel — wersja web.

Dlaczego nie `python3 -m http.server`? Bo PWA wymaga poprawnych typów MIME,
nagłówków CSP i — gdy chcesz udostępnić aplikację poza swój komputer — bramki
z hasłem. Ten serwer potrafi jedno i drugie.

Przykłady
---------
# 1. Tylko na tym komputerze (domyślnie, nic nie wychodzi na zewnątrz)
python3 server.py

# 2. Otwórz od razu przeglądarkę
python3 server.py --open

# 3. Z hasłem (przydatne, gdy wystawiasz aplikację w sieci lokalnej)
python3 server.py --auth anna:moje-tajne-haslo

# 4. Dostęp z telefonu w tej samej sieci Wi-Fi (serwer nasłuchuje na 0.0.0.0)
python3 server.py --auth anna:moje-tajne-haslo
#    (adres LAN wypisze się w konsoli)

# 5. Dostęp z dowolnego miejsca, bez konfiguracji routera:
#    szybki tunel Cloudflare + hasło. Wymaga programu `cloudflared`.
python3 server.py --auth anna:moje-tajne-haslo --tunnel

Bezpieczeństwo: hasło działa jak zwykłe HTTP Basic Auth. W sieci lokalnej to
wystarczające minimum (chroni przed domownikami/gośćmi). Publicznie (tunel)
używaj go tylko z `--auth` i pamiętaj, że pojedyncze hasło nie jest tak mocne
jak prawdziwy login (np. Cloudflare Access z kodem e-mail — patrz
deploy/PRYWATNY-HOSTING.md).
"""
from __future__ import annotations

import argparse
import base64
import functools
import hmac
import http.server
import os
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EXTRA_TYPES = {
    ".webmanifest": "application/manifest+json",
    ".json": "application/json",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}

# Uwaga: celowo BEZ frame-ancestors / X-Frame-Options — aplikacja bywa
# podglądana w ramce (podgląd edytora, panel hostingu).
CSP = (
    "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
    "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
    "connect-src 'self'; form-action 'none'; base-uri 'none'"
)

LOGIN_PAGE = """<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<title>Wymagane hasło — mObywatel (kopia poglądowa)</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#1B2B45;color:#fff;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;text-align:center;padding:24px}
h1{font-size:1.3rem;margin:0 0 8px}p{color:#C7D2E4;max-width:34ch;margin:0 auto;font-size:.92rem;line-height:1.5}</style>
</head><body><div><h1>Ta aplikacja jest prywatna</h1>
<p>Podaj nazwę użytkownika i hasło ustawione przy uruchomieniu serwera, żeby zobaczyć swój portfel.</p>
</div></body></html>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    """Statyczne pliki + poprawny CSP + opcjonalny login (HTTP Basic)."""

    auth: tuple[str, str] | None = None
    no_cache = False

    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    # ---------------------------------------------------------------- MIME
    def guess_type(self, path):  # noqa: D102
        suffix = Path(str(path)).suffix.lower()
        if suffix in EXTRA_TYPES:
            return EXTRA_TYPES[suffix]
        return super().guess_type(path)

    # -------------------------------------------------------------- nagłówki
    def end_headers(self):  # noqa: D102
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate" if self.no_cache else "no-cache")
        self.send_header("Service-Worker-Allowed", "/")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        super().end_headers()

    # ------------------------------------------------------------------ auth
    def _authorized(self) -> bool:
        if not self.auth:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            raw = base64.b64decode(header[6:], validate=True).decode("utf-8")
        except Exception:
            return False
        user, sep, password = raw.partition(":")
        if not sep:
            return False
        return hmac.compare_digest(user, self.auth[0]) and hmac.compare_digest(password, self.auth[1])

    def _ask_for_password(self):  # noqa: D102
        body = LOGIN_PAGE.encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="mObywatel (kopia pogladowa)", charset="UTF-8"')
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):  # noqa: D102
        if not self._authorized():
            return self._ask_for_password()
        return super().do_GET()

    def do_HEAD(self):  # noqa: D102
        if not self._authorized():
            return self._ask_for_password()
        return super().do_HEAD()

    # ------------------------------------------------------------------ logi
    def log_message(self, fmt, *args):  # noqa: D102
        sys.stderr.write("  %s\n" % (fmt % args))


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def start_tunnel(port: int) -> subprocess.Popen | None:
    """Uruchamia szybki tunel Cloudflare (losowy adres https://...trycloudflare.com)."""
    exe = shutil.which("cloudflared")
    if not exe:
        print("  ! Nie znalazłem programu `cloudflared` — tunel pominięty.")
        print("    Windows: winget install --id Cloudflare.cloudflared")
        print("    macOS  : brew install cloudflared")
        print("    Linux  : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        return None

    try:
        proc = subprocess.Popen(
            [exe, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
    except OSError as exc:
        print(f"  ! Nie udało się uruchomić tunelu: {exc}")
        return None

    found = threading.Event()

    def pump():
        url_re = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
        for line in proc.stdout or []:  # type: ignore[union-attr]
            sys.stdout.write("    [tunel] " + line.rstrip() + "\n")
            sys.stdout.flush()
            if not found.is_set():
                m = url_re.search(line)
                if m:
                    found.set()
                    print("\n" + "═" * 62)
                    print("  Adres z zewnątrz (ważny, dopóki to okno działa):")
                    print(f"    {m.group(0)}")
                    print("  Otwórz go na telefonie lub w pracy — poprosi o hasło.")
                    print("═" * 62 + "\n")

    threading.Thread(target=pump, daemon=True).start()
    time.sleep(4)
    if not found.is_set():
        print("  … czekam jeszcze na adres tunelu (zajrzyj wyżej za chwilę).")
    return proc


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Serwer lokalny — mObywatel (kopia poglądowa). Domyślnie widoczny tylko dla Ciebie.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    ap.add_argument("--host", default="0.0.0.0",
                    help="0.0.0.0 = dostępny też z telefonu w tej samej sieci (użyj wtedy --auth!)")
    ap.add_argument("--auth", metavar="UŻYTKOWNIK:HASŁO",
                    help="włącz pytanie o hasło (HTTP Basic Auth), np. --auth anna:tajne1")
    ap.add_argument("--tunnel", action="store_true",
                    help="wystaw aplikację przez szybki tunel Cloudflare (używaj razem z --auth)")
    ap.add_argument("--open", action="store_true", help="otwórz przeglądarkę po starcie")
    ap.add_argument("--no-cache", action="store_true", help="wyłącz cache przeglądarki (praca nad kodem)")
    ap.add_argument("--dist", action="store_true", help="serwuj katalog dist/ (zbudowany przez tools/make_dist.py)")
    args = ap.parse_args()

    auth = None
    if args.auth:
        if ":" not in args.auth:
            ap.error("--auth wymaga formatu UŻYTKOWNIK:HASŁO, np. --auth anna:tajne1")
        user, _, password = args.auth.partition(":")
        if not user or not password:
            ap.error("--auth: użytkownik i hasło nie mogą być puste")
        if len(password) < 8:
            print("  ! Hasło krótsze niż 8 znaków — rozważ dłuższe.")
        auth = (user, password)

    directory = ROOT / "dist" if args.dist else ROOT
    if args.dist and not (directory / "index.html").exists():
        print("  ! Brak dist/index.html — uruchom najpierw: python3 tools/make_dist.py")
        return 1

    Handler.auth = auth
    Handler.no_cache = args.no_cache
    handler = functools.partial(Handler, directory=str(directory))

    if args.tunnel and not auth:
        print("  ! Uwaga: tunel bez --auth wystawi aplikację publicznie. Dodaj hasło!")
    if args.host == "0.0.0.0" and not auth:
        print("  ! Uwaga: serwer słucha na wszystkich interfejsach bez hasła (sieć lokalna).")

    with Server((args.host, args.port), handler) as httpd:
        print("═" * 62)
        print("  mObywatel — wersja web (kopia poglądowa)")
        print("═" * 62)
        print(f"  Katalog           :  {directory}")
        print(f"  Na tym komputerze :  http://localhost:{args.port}")
        if args.host == "0.0.0.0":
            print(f"  W sieci lokalnej  :  http://{lan_ip()}:{args.port}   (telefon, tablet)")
        print(f"  Hasło             :  {'tak (Basic Auth, użytkownik ' + auth[0] + ')' if auth else 'BRAK — dostęp swobodny'}")
        print("  Zatrzymanie       :  Ctrl+C")
        print("─" * 62)
        print("  Instalacja jako aplikacja: Chrome/Edge → ikona „Zainstaluj”")
        print("  w pasku adresu lub ⋮ → Zainstaluj. Safari → Plik → Dodaj do Docka.")
        print("─" * 62)

        tunnel = start_tunnel(args.port) if args.tunnel else None

        if args.open:
            threading.Thread(
                target=lambda: (time.sleep(0.6), webbrowser.open(f"http://localhost:{args.port}")),
                daemon=True,
            ).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Zatrzymano. Dane użytkownika zostają w przeglądarce (localStorage).")
        finally:
            if tunnel:
                tunnel.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
