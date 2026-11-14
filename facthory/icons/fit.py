#!/usr/bin/env python3
"""Fit each app's glyph to its platform's icon frame, without touching the glyph.

The glyph is `facthory/icons/<product>.svg`, unchanged: `notepad-text`, `table` and `presentation`
from with icons in their Chrome style (MIT, `LICENSE-withicons.txt`), recoloured for the product.
It is drawn small inside its own 512-unit canvas, so an icon made of that file as it is looks small
in the Dock. This script measures the glyph, then writes three files that place it:

  <product>-macos.svg  Apple's grid: a 1024 canvas with an 824 x 824 rounded-square tile, tinted from
                       the glyph's colour, and the glyph's box at about 72 to 78% of the tile's
                       width (never more than 82% of its height), optically centred
  <product>-flat.svg   Windows, Linux and the scalable icon: no tile, the free-form glyph with its
                       cut-outs transparent, its longer side at 88% of the 1024 canvas
  <product>-layer.svg  The layer of the macOS appearance-aware icon (render.py's <base>.icon): the glyph
                       alone on a transparent 1024 canvas, at the same share of the canvas as the glyph
                       has of the macOS tile, so the system's tile (the light and the dark fill of
                       icon.json, which render.py writes from tile_colours() below) frames it as the
                       .icns tile does

The glyph is placed uniformly scaled and nothing else: not redrawn, recoloured or cropped.
`render.py` renders the platform files from the two.

  python3 facthory/icons/fit.py --product page        write the three files (needs resvg and Pillow)
  python3 facthory/icons/fit.py --product page --measure   print the glyph's box and the fit

The tiles' colours, light and dark, are made here (`tile_colours`), for the .icns tile, the .icon's fills
and the proofs alike, so the three cannot drift apart.
"""

from __future__ import annotations

import argparse
import colorsys
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANVAS = 1024
GLYPH_UNITS = 512  # every glyph file is drawn in a 512 x 512 viewBox
MACOS_BODY = 824.0
MACOS_X = 100.0
MACOS_WIDTH_SHARE = 0.76  # of the tile; the height cap below can lower it, to no less than 0.72
MACOS_HEIGHT_CAP = 0.82
FLAT_SHARE = 0.88  # of the canvas, the glyph's longer side
OPTICAL = 0.5  # how far the glyph's centre moves from its box's centre toward its centre of mass
ALPHA_EDGE = 24  # alpha above which a pixel is the glyph's (below it, the faint shadow's edge)

# The tile: white at the top, the product's tint at the bottom: the tiles main's macOS icons had.
TILE_BOTTOM = {"page": "#D3EBEE", "grid": "#D6E4DC", "deck": "#F1D8E5"}
TILE_EDGE = {"page": "#AFDBE1", "grid": "#BCD3C6", "deck": "#E3BFD2"}
# The dark tile: the product's hue (that of its light tile's edge) at low lightness, so the glyph's light
# parts stand out and its dark cut-outs read as the tile; saturation and lightness (top, bottom) are the same
# for every product, chosen by looking at Page's (facthory/icons/proof/page-appearances.png).
DARK_SATURATION = 0.45
DARK_LIGHTNESS = (0.19, 0.08)
DARK_EDGE_LIGHTNESS = 0.30
SHADOW = "#0B1F2A"


def hex_rgb(colour: str) -> tuple[int, int, int]:
    return int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16)


def rgb_hex(r: float, g: float, b: float) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(round(max(0.0, min(1.0, c)) * 255) for c in (r, g, b)))


def dark_colour(product: str, lightness: float) -> str:
    r, g, b = (c / 255 for c in hex_rgb(TILE_EDGE[product]))
    hue = colorsys.rgb_to_hls(r, g, b)[0]
    return rgb_hex(*colorsys.hls_to_rgb(hue, lightness, DARK_SATURATION))


def tile_colours(product: str, tile: str = "light") -> tuple[str, str, str]:
    """The tile's colours as (top, bottom, edge), for "light" (the default tile) or "dark"."""
    if tile == "light":
        return "#FFFFFF", TILE_BOTTOM[product], TILE_EDGE[product]
    return dark_colour(product, DARK_LIGHTNESS[0]), dark_colour(product, DARK_LIGHTNESS[1]), dark_colour(product, DARK_EDGE_LIGHTNESS)


def resvg(args: list[str]) -> None:
    subprocess.run(["resvg", *args], check=True, stdin=subprocess.DEVNULL)


def measure(glyph: Path) -> dict[str, float]:
    """The glyph's box and its centre of mass, in its 512-unit canvas, from a 2048 px render."""
    from PIL import Image

    px = 2048
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "glyph.png"
        resvg(["-w", str(px), "-h", str(px), str(glyph), str(png)])
        alpha = Image.open(png).convert("RGBA").getchannel("A")
    mask = alpha.point(lambda v: 255 if v > ALPHA_EDGE else 0)
    box = mask.getbbox()
    if box is None:
        raise SystemExit(f"error: {glyph} draws nothing")
    k = GLYPH_UNITS / px
    # Centre of mass of the opaque pixels, row by row on a quarter-size copy.
    small = mask.resize((px // 4, px // 4))
    data, w = small.load(), px // 4
    sx = sy = n = 0
    for y in range(w):
        for x in range(w):
            if data[x, y]:
                sx += x
                sy += y
                n += 1
    cx, cy = (sx / n + 0.5) * 4 * k, (sy / n + 0.5) * 4 * k
    return {"x0": box[0] * k, "y0": box[1] * k, "x1": box[2] * k, "y1": box[3] * k, "mx": cx, "my": cy}


def inner(glyph: Path) -> str:
    """The inside of the glyph's SVG, exactly as it is."""
    text = glyph.read_text(encoding="utf-8")
    body = re.sub(r"^\s*<svg[^>]*>", "", text, count=1)
    return re.sub(r"</svg>\s*$", "", body).strip()


def optical_centre(m: dict[str, float]) -> tuple[float, float]:
    """The point of the glyph that goes to the middle of its frame: between its box's centre and its centre of mass."""
    bx, by = (m["x0"] + m["x1"]) / 2, (m["y0"] + m["y1"]) / 2
    return bx + OPTICAL * (m["mx"] - bx), by + OPTICAL * (m["my"] - by)


def placed(glyph: Path, m: dict[str, float], scale: float, cx: float, cy: float) -> str:
    """The glyph scaled by `scale` (pixels per unit), its optical centre at (cx, cy) of the canvas."""
    ox, oy = optical_centre(m)
    size = GLYPH_UNITS * scale
    x, y = cx - ox * scale, cy - oy * scale
    return f'<svg x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" viewBox="0 0 {GLYPH_UNITS} {GLYPH_UNITS}">{inner(glyph)}</svg>'


def macos_scale(m: dict[str, float]) -> float:
    bw, bh = m["x1"] - m["x0"], m["y1"] - m["y0"]
    return min(MACOS_WIDTH_SHARE * MACOS_BODY / bw, MACOS_HEIGHT_CAP * MACOS_BODY / bh)


def flat_scale(m: dict[str, float]) -> float:
    return FLAT_SHARE * CANVAS / max(m["x1"] - m["x0"], m["y1"] - m["y0"])


def macos_svg(product: str, glyph: Path, m: dict[str, float], tile: str = "light") -> str:
    x0 = MACOS_X
    r = round(MACOS_BODY * 0.2237, 2)  # Apple's corner, near enough
    top, bottom, edge = tile_colours(product, tile)
    scale = macos_scale(m)
    cx = cy = x0 + MACOS_BODY / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">\n'
        f"<!-- Facthory {product.capitalize()} app icon for macOS: {product}.svg (with icons, Chrome style, MIT; LICENSE-withicons.txt),\n"
        f"     recoloured by Bandpey GmbH, scaled and placed on Apple's grid by facthory/icons/fit.py: an 824 x 824 tile in the\n"
        f"     1024 canvas, the glyph's box {100 * scale * (m['x1'] - m['x0']) / MACOS_BODY:.0f}% of the tile's width. The glyph itself is unchanged. -->\n"
        f'<defs><linearGradient id="tile" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'
        f'<filter id="drop" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="10" stdDeviation="11" flood-color="{SHADOW}" flood-opacity=".30"/></filter></defs>\n'
        f'<rect x="{x0}" y="{x0}" width="{MACOS_BODY}" height="{MACOS_BODY}" rx="{r}" fill="url(#tile)" filter="url(#drop)"/>\n'
        f'<rect x="{x0 + 1.5}" y="{x0 + 1.5}" width="{MACOS_BODY - 3}" height="{MACOS_BODY - 3}" rx="{r - 1.5:.2f}" fill="none" stroke="{edge}" stroke-width="3"/>\n'
        f"{placed(glyph, m, scale, cx, cy)}\n</svg>\n"
    )


def flat_svg(product: str, glyph: Path, m: dict[str, float]) -> str:
    scale = flat_scale(m)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">\n'
        f"<!-- Facthory {product.capitalize()} app icon for Windows and Linux: {product}.svg (with icons, Chrome style, MIT; LICENSE-withicons.txt),\n"
        f"     recoloured by Bandpey GmbH, scaled by facthory/icons/fit.py so its longer side is {int(FLAT_SHARE * 100)}% of the canvas.\n"
        f"     No tile; the glyph's cut-outs stay transparent. The glyph itself is unchanged. -->\n"
        f"{placed(glyph, m, scale, CANVAS / 2, CANVAS / 2)}\n</svg>\n"
    )


def layer_scale(m: dict[str, float]) -> float:
    """Pixels per unit on the 1024 canvas that is the whole tile: the glyph has the same share of it as of the macOS tile."""
    return macos_scale(m) * CANVAS / MACOS_BODY


def layer_svg(product: str, glyph: Path, m: dict[str, float]) -> str:
    scale = layer_scale(m)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">\n'
        f"<!-- Facthory {product.capitalize()} icon layer for macOS: {product}.svg (with icons, Chrome style, MIT; LICENSE-withicons.txt),\n"
        f"     recoloured by Bandpey GmbH, scaled and placed by facthory/icons/fit.py on the canvas that is the whole tile of the\n"
        f"     appearance-aware icon: the glyph's box {100 * scale * (m['x1'] - m['x0']) / CANVAS:.0f}% of its width, as on the .icns tile.\n"
        f"     The glyph itself is unchanged; the tile is the system's, filled by icon.json. -->\n"
        f"{placed(glyph, m, scale, CANVAS / 2, CANVAS / 2)}\n</svg>\n"
    )


def write_all(product: str, out: Path = HERE) -> list[Path]:
    glyph = HERE / f"{product}.svg"
    m = measure(glyph)
    paths = [out / f"{product}-macos.svg", out / f"{product}-flat.svg", out / f"{product}-layer.svg"]
    paths[0].write_text(macos_svg(product, glyph, m), encoding="utf-8")
    paths[1].write_text(flat_svg(product, glyph, m), encoding="utf-8")
    paths[2].write_text(layer_svg(product, glyph, m), encoding="utf-8")
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--product", required=True, choices=sorted(TILE_BOTTOM))
    ap.add_argument("--measure", action="store_true")
    args = ap.parse_args()
    if args.measure:
        m = measure(HERE / f"{args.product}.svg")
        bw, bh = m["x1"] - m["x0"], m["y1"] - m["y0"]
        sm, sf = macos_scale(m), flat_scale(m)
        print(f"glyph box {bw:.1f} x {bh:.1f} of {GLYPH_UNITS} units; optical centre {optical_centre(m)[0]:.1f}, {optical_centre(m)[1]:.1f}")
        print(f"macOS: x{sm:.3f}: {100 * sm * bw / MACOS_BODY:.1f}% of the tile's width, {100 * sm * bh / MACOS_BODY:.1f}% of its height")
        print(f"flat:  x{sf:.3f}: {100 * sf * bw / CANVAS:.1f}% of the canvas's width, {100 * sf * bh / CANVAS:.1f}% of its height")
        return 0
    for p in write_all(args.product):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
