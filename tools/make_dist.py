#!/usr/bin/env python3
"""Buduje katalog dist/ gotowy do wrzucenia na dowolny hosting statyczny
(Cloudflare Pages, Netlify, Vercel, własny serwer) — przeciągnij-i-upuść.

Uruchomienie:  python3 tools/make_dist.py
Efekt:         dist/ zawiera wyłącznie pliki potrzebne do działania aplikacji.

Dist celowo NIE zawiera: tools/, server.py, .git, dokumentacji deweloperskiej.
Zawiera natomiast _headers (CSP) i _redirects, które rozumie Cloudflare Pages
i Netlify.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# Pliki aplikacji (kolejność bez znaczenia)
FILES = [
    "index.html",
    "manifest.webmanifest",
    "sw.js",
    "icon.svg",
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-512.png",
    "apple-touch-icon.png",
    "apple-touch-icon-152.png",
    "favicon.ico",
    "_headers",
    "_redirects",
    "LICENSE",
]

EXTRA_README = """mObywatel — wersja web (kopia poglądowa)
=======================================

Ten katalog to gotowa strona statyczna. Jak ją opublikować PRYWATNIE:

  * Cloudflare Pages + Cloudflare Access (darmowe, login kodem e-mail)
    → patrz deploy/PRYWATNY-HOSTING.md w repozytorium.

  * Własny serwer / sieć lokalna:
    python3 server.py --auth uzytkownik:haslo --open

UWAGA: GitHub Pages NIE udostępnia prywatnych stron (poza GitHub Enterprise
Cloud). Strona opublikowana przez GitHub Pages jest publiczna, nawet gdy
repozytorium jest prywatne.

Ta strona nie jest oficjalną aplikacją mObywatel i nie służy do okazywania
dokumentów. Dane wpisane w aplikacji zostają wyłącznie w przeglądarce
(localStorage) — nic nie jest wysyłane na serwer.
"""


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    missing = []
    for name in FILES:
        src = ROOT / name
        if not src.exists():
            if name in ("_headers", "_redirects"):
                missing.append(name)
                continue
            missing.append(name)
            continue
        shutil.copy2(src, DIST / name)

    (DIST / "CZYTAJ-TO.txt").write_text(EXTRA_README, encoding="utf-8")

    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"  dist/ gotowe: {len(list(DIST.iterdir()))} plików, {total / 1024:.0f} kB")
    for f in sorted(DIST.iterdir()):
        print(f"    {f.name}")
    if missing:
        print("\n  ! Pominięto brakujące pliki: " + ", ".join(missing))
        return 1
    print("\n  Dalej: wrzuć CAŁĄ zawartość dist/ na hosting (przeciągnij-i-upuść),")
    print("  albo przetestuj lokalnie:  python3 server.py --dist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
