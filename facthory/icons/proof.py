#!/usr/bin/env python3
"""The contact sheet of an app's icon candidates (`facthory/icons/proof/<product>.png`, at 2x).

Rows are the sizes 16, 32, 64, 128, 256 and 512 points (twice that in pixels); the columns, on a
light ground and then on a dark one: candidate A for macOS and for Windows and Linux, candidate B
for both, and two reference shapes of our own drawing: a plain rounded square at Apple's grid size
and one at the flat tile's size. The sizes of 24 points and under are drawn from the small files.

  python3 facthory/icons/proof.py --product page [--out FILE]

Needs resvg and Pillow.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compose  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    raise SystemExit("error: Pillow is needed (pip install pillow)")

SIZES = [16, 32, 64, 128, 256, 512]
SCALE = 2
GROUNDS = {"light": (244, 246, 249), "dark": (30, 32, 38)}
# Up to this size (points) the small file is used, as render.py does.
SMALL_UP_TO = 24
PAD = 40


def raster(svg: str, px: int, tmp: Path, name: str) -> Image.Image:
    src = tmp / f"{name}.svg"
    src.write_text(svg, encoding="utf-8")
    out = tmp / f"{name}-{px}.png"
    subprocess.run(["resvg", "-w", str(px), "-h", str(px), str(src), str(out)], check=True, stdin=subprocess.DEVNULL)
    return Image.open(out).convert("RGBA")


def reference(macos: bool) -> str:
    """A plain rounded square, grey, at the size of the family's tile on its platform."""
    x0, y0, t = compose.tile_geometry(macos)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">'
            f'<rect x="{x0}" y="{y0}" width="{t}" height="{t}" rx="{t * 0.2237:.1f}" fill="#8A94A6"/></svg>')


def columns(product: str) -> list[tuple[str, callable]]:
    def cand(variant: str, macos: bool):
        def make(points: int, tmp: Path) -> Image.Image:
            small = points <= SMALL_UP_TO
            svg = compose.icon(product, variant, macos, small)
            return raster(svg, points * SCALE, tmp, f"{variant}{int(macos)}{int(small)}")
        return make

    def ref(macos: bool):
        return lambda points, tmp: raster(reference(macos), points * SCALE, tmp, f"ref{int(macos)}")

    return [("A macOS", cand("a", True)), ("A Win/Linux", cand("a", False)), ("B macOS", cand("b", True)),
            ("B Win/Linux", cand("b", False)), ("ref: Apple grid", ref(True)), ("ref: flat tile", ref(False))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--product", required=True, choices=sorted(compose.PRODUCTS))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    out = args.out or HERE / "proof" / f"{args.product}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = columns(args.product)
    cell = lambda s: s * SCALE + PAD  # noqa: E731
    row_w = sum(cell(s) for s in SIZES)
    head = 70
    panel_w = row_w + PAD
    # One band per column, each with the six sizes side by side, on the light ground then the dark.
    band_h = SIZES[-1] * SCALE + PAD
    width = panel_w * len(GROUNDS)
    height = head + band_h * len(cols)
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=30)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for g, (gname, rgb) in enumerate(GROUNDS.items()):
            x_off = g * panel_w
            d.rectangle([x_off, 0, x_off + panel_w, height], fill=rgb)
            fg = (20, 24, 32) if gname == "light" else (230, 234, 242)
            d.text((x_off + PAD, 20), font=font, text=f"Facthory {compose.PRODUCTS[args.product]['name']}: {gname} ground, 2x, sizes {', '.join(map(str, SIZES))}", fill=fg)
            for r, (label, make) in enumerate(cols):
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
