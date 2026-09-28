#!/usr/bin/env python3
"""Generator ikon aplikacji (PNG) — mObywatel, kopia poglądowa.

Wymaga Pillow:  python3 -m pip install pillow
Uruchomienie:   python3 tools/make_icons.py

Kolory marki: granat #1B2B45, akcent #CC2430 (publiczna paleta design systemu).
Rysujemy w 4x i zmniejszamy — dzięki temu krawędzie są gładkie.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    sys.exit("Brak Pillow. Zainstaluj: python3 -m pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
NAVY = (27, 43, 69, 255)
RED = (204, 36, 48, 255)
WHITE = (255, 255, 255, 255)
LIGHT = (228, 234, 243, 255)
SS = 4  # supersampling


def rounded(draw: ImageDraw.ImageDraw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


def card_icon(size: int, *, bleed: bool, glyph_scale: float) -> Image.Image:
    """Ikona: granatowe tło + biała karta dokumentu z czerwonym paskiem.

    bleed=True  -> tło na całym kwadracie (maskable / apple-touch-icon)
    bleed=False -> zaokrąglony kafelek z przezroczystymi narożnikami
    """
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0) if not bleed else NAVY)
    d = ImageDraw.Draw(img)

    if not bleed:
        rounded(d, (0, 0, S - 1, S - 1), int(S * 0.219), NAVY)

    # Karta — wymiary 3.125 : 2 (jak dowód osobisty 1.586 po skróceniu na wysokość)
    cw = S * 0.62 * glyph_scale
    ch = cw / 1.586
    cx, cy = S / 2, S / 2
    x0, y0, x1, y1 = cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2

    r = cw * 0.085
    rounded(d, (x0, y0, x1, y1), r, WHITE)

    # Czerwony pasek nagłówka (przycięty do zaokrąglenia karty)
    band = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.rectangle((x0, y0, x1, y0 + ch * 0.30), fill=RED)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((x0, y0, x1, y1), radius=r, fill=255)
    img.paste(band, (0, 0), mask)

    # Linie tekstu + pole na zdjęcie
    d = ImageDraw.Draw(img)
    lw = cw * 0.40
    lh = ch * 0.085
    ly = y0 + ch * 0.47
    rounded(d, (x0 + cw * 0.09, ly, x0 + cw * 0.09 + lw, ly + lh), lh / 2, (27, 43, 69, 60))
    rounded(d, (x0 + cw * 0.09, ly + lh * 1.9, x0 + cw * 0.09 + lw * 0.7, ly + lh * 2.9), lh / 2, (27, 43, 69, 60))
    pr = ch * 0.20
    px, py = x1 - cw * 0.19, y0 + ch * 0.70
    d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=LIGHT)
    d.ellipse((px - pr * 0.62, py - pr * 0.62, px + pr * 0.62, py + pr * 0.62), fill=(27, 43, 69, 90))

    return img.resize((size, size), Image.LANCZOS)


def main() -> int:
    outputs = [
        ("icon-512.png", 512, False, 1.0),
        ("icon-192.png", 192, False, 1.0),
        ("icon-maskable-512.png", 512, True, 0.72),  # strefa bezpieczna maskable
        ("apple-touch-icon.png", 180, True, 0.80),
        ("apple-touch-icon-152.png", 152, True, 0.80),
    ]
    for name, size, bleed, scale in outputs:
        im = card_icon(size, bleed=bleed, glyph_scale=scale)
        path = ROOT / name
        im.save(path, "PNG", optimize=True)
        print(f"  zapisano {path.name:26s} {size}x{size}")

    # favicon.ico z kilkoma rozmiarami
    ico = card_icon(64, bleed=False, glyph_scale=1.0).convert("RGBA")
    ico.save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"  zapisano {'favicon.ico':26s} 16/32/48/64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
