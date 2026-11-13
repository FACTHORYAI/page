#!/usr/bin/env python3
"""Compose Facthory's app icons: a light tile, Facthory's mark, and the product's own glyph.

The mark is Facthory's (`facthory/icons/brand/mark.svg`, unmodified: placed uniformly scaled,
never recoloured, stretched, cropped or redrawn). The glyphs (text lines, a cell grid, a slide)
are original work drawn here. Every app of the family has the same body; the product is told
apart by its glyph and its colour, taken from the mark's own blues.

Two candidates:

  a  the mark is the hero; the product's glyph is a badge at the lower right
  b  the product's glyph is the hero; the mark is the badge

Four files per product, each a 1024 x 1024 canvas:

  <product>.svg              the tile at the edge of the canvas with a hairline edge (Windows, Linux)
  <product>-macos.svg        Apple's grid: an 824 x 824 body, the margin around it, a soft shadow
  <product>-small.svg        the same at 16 to 24 pixels: the hero alone, larger
  <product>-macos-small.svg  macOS's, at 16 to 32 pixels

  python3 facthory/icons/compose.py --product page --variant a [--out DIR]

`render.py` renders these into the platform files; `proof.py` draws the contact sheet.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANVAS = 1024
MARK_W, MARK_H = 960, 1016

# The product colours: the mark's own blues (#00BBEC, #2756A9, #224684), one lightness each.
PRODUCTS = {
    "page": {"name": "Page", "colour": "#0A8FCB", "light": "#27B4EA", "dark": "#0A6FA3"},
    "grid": {"name": "Grid", "colour": "#2A62B8", "light": "#4A82D6", "dark": "#1F4B94"},
    "deck": {"name": "Deck", "colour": "#26407F", "light": "#3D5CA3", "dark": "#1B2F63"},
}

TILE_TOP, TILE_BOTTOM = "#FFFFFF", "#E1E9F4"
EDGE = "#0B2347"  # the hairline edge and the shadow: the mark's navy, darkened


def mark_inner() -> str:
    """Facthory's mark: the inside of brand/mark.svg exactly as it is."""
    text = (HERE / "brand" / "mark.svg").read_text(encoding="utf-8")
    inner = re.sub(r"^\s*<svg[^>]*>", "", text, count=1)
    return re.sub(r"</svg>\s*$", "", inner).strip()


def place_mark(cx: float, cy: float, h: float) -> str:
    """The mark centred on (cx, cy), `h` tall, in its own proportions."""
    w = h * MARK_W / MARK_H
    return (f'<svg x="{cx - w / 2:.2f}" y="{cy - h / 2:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'viewBox="0 0 {MARK_W} {MARK_H}">{mark_inner()}</svg>')


def glyph(product: str, fg: str, bg: str, detail: bool = True) -> str:
    """The product's glyph in a 100 x 100 box: a shape in `fg` with marks in `bg`."""
    if product == "page":
        # A page with a folded corner and lines of text.
        lines = [(36, 70), (52, 70), (68, 70), (84, 54)] if detail else [(40, 70), (58, 70), (76, 54)]
        rows = "".join(f'<path d="M31,{y} H{x}" stroke="{bg}" stroke-width="8" stroke-linecap="round"/>' for y, x in lines)
        return (f'<path d="M26,4 H60 L84,28 V87 a9,9 0 0 1 -9,9 H26 a9,9 0 0 1 -9,-9 V13 a9,9 0 0 1 9,-9 Z" fill="{fg}"/>'
                f'<path d="M60,4 V19 a9,9 0 0 0 9,9 H84 Z" fill="{bg}" fill-opacity=".38"/>{rows}')
    if product == "grid":
        # A sheet of cells: a header row, then rows and columns.
        cuts = ('<path d="M35.5,12 V88 M64.5,12 V88 M6,39 H94 M6,63 H94" ' f'stroke="{bg}" stroke-width="5.5"/>' if detail
                else f'<path d="M50,12 V88 M6,50 H94" stroke="{bg}" stroke-width="7"/>')
        return (f'<defs><clipPath id="gridclip"><rect x="6" y="12" width="88" height="76" rx="11"/></clipPath></defs>'
                f'<rect x="6" y="12" width="88" height="76" rx="11" fill="{fg}"/>'
                f'<g clip-path="url(#gridclip)"><rect x="6" y="12" width="88" height="27" fill="{bg}" fill-opacity=".34"/>{cuts}</g>')
    if product == "deck":
        # A slide on a stand: a title, lines of text and a chart.
        body = (f'<rect x="14" y="26" width="44" height="9" rx="4.5" fill="{bg}"/>'
                f'<rect x="14" y="43" width="28" height="6" rx="3" fill="{bg}" fill-opacity=".6"/>'
                f'<rect x="14" y="54" width="20" height="6" rx="3" fill="{bg}" fill-opacity=".6"/>'
                f'<rect x="63" y="46" width="8" height="14" rx="2" fill="{bg}" fill-opacity=".85"/>'
                f'<rect x="74" y="38" width="8" height="22" rx="2" fill="{bg}" fill-opacity=".85"/>'
                f'<rect x="85" y="30" width="8" height="30" rx="2" fill="{bg}" fill-opacity=".85"/>' if detail else
                f'<rect x="14" y="26" width="46" height="11" rx="5.5" fill="{bg}"/>'
                f'<rect x="64" y="42" width="11" height="22" rx="2.5" fill="{bg}" fill-opacity=".85"/>'
                f'<rect x="80" y="30" width="11" height="34" rx="2.5" fill="{bg}" fill-opacity=".85"/>')
        stand = f'<rect x="45" y="72" width="10" height="11" fill="{fg}"/><rect x="30" y="81" width="40" height="6" rx="3" fill="{fg}"/>'
        return f'<rect x="4" y="12" width="92" height="62" rx="8" fill="{fg}"/>{body}{stand}'
    raise ValueError(f"unknown product {product!r}")


def place_glyph(product: str, cx: float, cy: float, size: float, fg: str, bg: str, detail: bool = True) -> str:
    s = size / 100
    return f'<g transform="translate({cx - size / 2:.2f},{cy - size / 2:.2f}) scale({s:.4f})">{glyph(product, fg, bg, detail)}</g>'


def tile_geometry(macos: bool) -> tuple[float, float, float]:
    """(x, y, side) of the tile body on the canvas."""
    return (100.0, 100.0, 824.0) if macos else (32.0, 32.0, 960.0)


def icon(product: str, variant: str, macos: bool, small: bool) -> str:
    p = PRODUCTS[product]
    x0, y0, t = tile_geometry(macos)
    r = round(t * 0.2237, 2)  # Apple's corner, near enough, for both
    cx0, cy0 = x0 + t / 2, y0 + t / 2
    defs = [
        f'<linearGradient id="tile" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TILE_TOP}"/><stop offset="1" stop-color="{TILE_BOTTOM}"/></linearGradient>',
        f'<linearGradient id="prod" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p["light"]}"/><stop offset="1" stop-color="{p["dark"]}"/></linearGradient>',
        f'<filter id="drop" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="{t * 0.012:.2f}" stdDeviation="{t * 0.014:.2f}" flood-color="{EDGE}" flood-opacity=".30"/></filter>',
        f'<filter id="badge" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="{t * 0.008:.2f}" stdDeviation="{t * 0.01:.2f}" flood-color="{EDGE}" flood-opacity=".28"/></filter>',
    ]
    body = []
    shadow = ' filter="url(#drop)"' if macos else ""
    body.append(f'<rect x="{x0}" y="{y0}" width="{t}" height="{t}" rx="{r}" fill="url(#tile)"{shadow}/>')
    edge = 2 if macos else 4
    body.append(f'<rect x="{x0 + edge / 2}" y="{y0 + edge / 2}" width="{t - edge}" height="{t - edge}" rx="{r - edge / 2:.2f}" '
                f'fill="none" stroke="{EDGE}" stroke-opacity="{.16 if macos else .26}" stroke-width="{edge}"/>')
    d = t * 0.38  # the badge's diameter: more than a third of the body
    inset = t * 0.075
    bx, by = x0 + t - inset - d / 2, y0 + t - inset - d / 2
    if small:
        # 16 to 32 pixels: the hero alone, larger and centred.
        if variant == "a":
            body.append(place_mark(cx0, cy0, t * 0.70))
        else:
            body.append(place_glyph(product, cx0, cy0, t * 0.74, "url(#prod)", "#FFFFFF", detail=False))
    else:
        hx, hy = cx0 - t * 0.04, cy0 - t * 0.05
        if variant == "a":
            body.append(place_mark(hx, hy, t * 0.62))
            body.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{d / 2:.2f}" fill="url(#prod)" stroke="#FFFFFF" stroke-width="{t * 0.022:.2f}" filter="url(#badge)"/>')
            body.append(place_glyph(product, bx, by, d * 0.58, "#FFFFFF", p["dark"]))
        else:
            body.append(place_glyph(product, hx, hy, t * 0.64, "url(#prod)", "#FFFFFF"))
            body.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{d / 2:.2f}" fill="#FFFFFF" stroke="{EDGE}" stroke-opacity=".18" stroke-width="{t * 0.006:.2f}" filter="url(#badge)"/>')
            body.append(place_mark(bx, by, d * 0.66))
    label = f"Facthory {p['name']}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">\n'
            f'<!-- {label} app icon, candidate {variant.upper()}{" (small sizes)" if small else ""}: drawn by Bandpey GmbH from Facthory\'s mark\n'
            f'     (facthory/icons/brand/mark.svg, unmodified) and an original {p["name"]} glyph (facthory/icons/compose.py). -->\n'
            f'<defs>{"".join(defs)}</defs>\n{chr(10).join(body)}\n</svg>\n')


def write_all(product: str, variant: str, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for macos, small, name in [(False, False, ""), (True, False, "-macos"), (False, True, "-small"), (True, True, "-macos-small")]:
        path = out / f"{product}{name}.svg"
        path.write_text(icon(product, variant, macos, small), encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--product", required=True, choices=sorted(PRODUCTS))
    ap.add_argument("--variant", default="a", choices=["a", "b"])
    ap.add_argument("--out", type=Path, default=HERE)
    args = ap.parse_args()
    for p in write_all(args.product, args.variant, args.out):
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
