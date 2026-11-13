#!/usr/bin/env python3
"""The contact sheet of an app's icon (`facthory/icons/proof/<product>.png`, at 2x).

Rows (bands), each at 16, 32, 64, 128, 256 and 512 points (twice that in pixels), on a light ground
on the left and a dark one on the right:

  main's macOS icon                 the glyph at 55% of the tile's width, the old fit
  macOS, light tile (the default)   the glyph at about 75% of an 824-point tile, tinted from its colour
  macOS, dark tile                  the same on a near-black tile, for the owner to choose
  main's Windows and Linux icon     the glyph at 70% of the canvas, cut-outs transparent
  Windows and Linux, transparent    the glyph at 88% of the canvas, cut-outs transparent (the default)
  Windows and Linux, backed         the same with a light fill behind the cut-outs
  reference                         a plain rounded square at Apple's grid size, to judge size against

  python3 facthory/icons/proof.py --product page [--out FILE]

Needs resvg and Pillow, and a git history with origin/main for main's icons.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import fit  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    raise SystemExit("error: Pillow is needed (pip install pillow)")

SIZES = [16, 32, 64, 128, 256, 512]
SCALE = 2
GROUNDS = {"light": (244, 246, 249), "dark": (30, 32, 38)}
PAD = 40
BACKING = (238, 244, 246, 255)
# Main's macOS files were drawn full-bleed on 512 and padded to Apple's grid when rendered.
OLD_MACOS_VIEWBOX = "-62.136 -62.136 636.272 636.272"


def git_show(path: str) -> str:
    r = subprocess.run(["git", "show", f"origin/main:{path}"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"error: origin/main has no {path} (fetch origin first)")
    return r.stdout


def raster(svg_text: str, px: int, tmp: Path, name: str) -> Image.Image:
    src = tmp / f"{name}.svg"
    src.write_text(svg_text, encoding="utf-8")
    out = tmp / f"{name}-{px}.png"
    subprocess.run(["resvg", "-w", str(px), "-h", str(px), str(src), str(out)], check=True, stdin=subprocess.DEVNULL)
    return Image.open(out).convert("RGBA")


def backed(glyph_png: Image.Image) -> Image.Image:
    """The glyph with a light fill behind its cut-outs: its silhouette, holes filled, under it."""
    alpha = glyph_png.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    flooded = alpha.copy()
    ImageDraw.floodfill(flooded, (0, 0), 128)  # the transparent outside
    silhouette = flooded.point(lambda v: 0 if v == 128 else 255)
    base = Image.new("RGBA", glyph_png.size, (0, 0, 0, 0))
    base.paste(Image.new("RGBA", glyph_png.size, BACKING), (0, 0), silhouette)
    base.alpha_composite(glyph_png)
    return base


def reference() -> str:
    x0, t = fit.MACOS_X, fit.MACOS_BODY
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">'
            f'<rect x="{x0}" y="{x0}" width="{t}" height="{t}" rx="{t * 0.2237:.1f}" fill="#8A94A6"/></svg>')


def bands(product: str) -> list[tuple[str, callable]]:
    glyph = HERE / f"{product}.svg"
    m = fit.measure(glyph)
    macos_light = (HERE / f"{product}-macos.svg").read_text(encoding="utf-8")
    macos_dark = fit.macos_svg(product, glyph, m, tile="dark")
    flat = (HERE / f"{product}-flat.svg").read_text(encoding="utf-8")
    old_mac = git_show(f"facthory/icons/{product}-macos.svg").replace('viewBox="0 0 512 512"', f'viewBox="{OLD_MACOS_VIEWBOX}"', 1)
    old_flat = git_show(f"facthory/icons/{product}.svg")

    def plain(svg: str, name: str):
        return lambda points, tmp: raster(svg, points * SCALE, tmp, name)

    def with_backing(points: int, tmp: Path) -> Image.Image:
        # Backed at the size it is shown, from a render twice as large, so the fill is not blurred.
        return backed(raster(flat, points * SCALE, tmp, "flatb"))

    return [
        ("main's macOS icon (old fit)", plain(old_mac, "oldmac")),
        ("macOS, light tile (default)", plain(macos_light, "maclight")),
        ("macOS, dark tile", plain(macos_dark, "macdark")),
        ("main's Windows/Linux icon (old fit)", plain(old_flat, "oldflat")),
        ("Windows/Linux, cut-outs transparent (default)", plain(flat, "flat")),
        ("Windows/Linux, cut-outs backed by a light fill", with_backing),
        ("reference: plain rounded square at Apple's grid", plain(reference(), "ref")),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--product", required=True, choices=sorted(fit.TILE_BOTTOM))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    out = args.out or HERE / "proof" / f"{args.product}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = bands(args.product)
    cell = lambda s: s * SCALE + PAD  # noqa: E731
    panel_w = sum(cell(s) for s in SIZES) + PAD
    head, band_h = 70, SIZES[-1] * SCALE + PAD
    sheet = Image.new("RGB", (panel_w * len(GROUNDS), head + band_h * len(rows)), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=30)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for g, (gname, rgb) in enumerate(GROUNDS.items()):
            x_off = g * panel_w
            d.rectangle([x_off, 0, x_off + panel_w, sheet.height], fill=rgb)
            fg = (20, 24, 32) if gname == "light" else (230, 234, 242)
            d.text((x_off + PAD, 20), f"Facthory {args.product.capitalize()}: {gname} ground, 2x, sizes {', '.join(map(str, SIZES))}", fill=fg, font=font)
            for r, (label, make) in enumerate(rows):
                y_base = head + r * band_h + band_h - PAD // 2
                d.text((x_off + PAD, head + r * band_h + 6), label, fill=fg, font=font)
                x = x_off + PAD
                for s in SIZES:
                    im = make(s, tmp)
                    sheet.paste(im, (x, y_base - im.height), im)
                    x += cell(s)
    sheet.save(out, optimize=True)
    print(out, sheet.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
