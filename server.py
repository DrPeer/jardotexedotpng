#!/usr/bin/env python3
"""Lokalny serwer dla aplikacji mObywatel — wersja web (kopia poglądowa).

Dlaczego nie `python3 -m http.server`? Bo PWA wymaga poprawnych typów MIME
(m.in. application/manifest+json) i nagłówków, które pozwalają przeglądarce
zauważyć aktualizację plików podczas pracy.

Uruchomienie:
    python3 server.py            # port 8000
    python3 server.py --port 8080
    python3 server.py --no-cache # dewelopersko: zero cache po stronie serwera

Następnie otwórz http://localhost:8000 i użyj „Zainstaluj” (Chrome/Edge)
albo Plik → Dodaj do Docka (Safari), żeby mieć aplikację na pulpicie.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import socket
import socketserver
import sys
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


class Handler(http.server.SimpleHTTPRequestHandler):
    """Statyczny serwer z poprawnymi MIME i przyjaznym cache'em."""

    def __init__(self, *args, directory: str | None = None, no_cache: bool = False, **kwargs):
        self.no_cache = no_cache
        super().__init__(*args, directory=directory, **kwargs)

    def guess_type(self, path):  # noqa: D102
        suffix = Path(str(path)).suffix.lower()
        if suffix in EXTRA_TYPES:
            return EXTRA_TYPES[suffix]
        return super().guess_type(path)

    def end_headers(self):  # noqa: D102
        if self.no_cache:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        else:
            # Pliki statyczne: krótki cache w przeglądarce, żeby zmiany były widoczne.
            self.send_header("Cache-Control", "no-cache")
        self.send_header("Service-Worker-Allowed", "/")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        # Aplikacja nie łączy się z niczym na zewnątrz — twarda blokada w CSP.
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
            # celowo bez frame-ancestors/X-Frame-Options: aplikacja bywa podglądana w ramce
            "connect-src 'self'; form-action 'none'; base-uri 'none'",
        )
        super().end_headers()

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


def main() -> int:
    ap = argparse.ArgumentParser(description="Serwer lokalny — mObywatel (kopia poglądowa)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="0.0.0.0", help="0.0.0.0 = dostępny też z telefonu w tej samej sieci")
    ap.add_argument("--no-cache", action="store_true", help="wyłącz cache przeglądarki (praca nad kodem)")
    args = ap.parse_args()

    handler = functools.partial(Handler, directory=str(ROOT), no_cache=args.no_cache)
    with Server((args.host, args.port), handler) as httpd:
        print("═" * 62)
        print("  mObywatel — wersja web (kopia poglądowa)")
        print("═" * 62)
        print(f"  Na tym komputerze :  http://localhost:{args.port}")
        if args.host == "0.0.0.0":
            print(f"  W sieci lokalnej  :  http://{lan_ip()}:{args.port}   (telefon, tablet)")
        print("  Zatrzymanie       :  Ctrl+C")
        print("─" * 62)
        print("  Instalacja jako aplikacja: Chrome/Edge → ikona „Zainstaluj”")
        print("  w pasku adresu lub ⋮ → Zainstaluj. Safari → Plik → Dodaj do Docka.")
        print("─" * 62)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Zatrzymano. Dane użytkownika zostają w przeglądarce (localStorage).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
