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

  python3 facthory/icons/proof.py --product page --appearances [--out FILE]
      `facthory/icons/proof/<product>-appearances.png`: the macOS 26 icon as `app-icon/<base>.icon` holds it,
      composed here from its icon.json and layer (no SVG, no resvg): the light and the dark appearance, then
      simulations of the tinted and the clear style, at 16, 32, 64, 128 and 256 points (twice that in pixels)
      on a light and a dark ground, and a grid check (Apple's 824 of 1024 tile, the glyph's box and optical
      centre). The tile's gloss, lighting and the tinted and clear styles are the system's: the simulations
      only show that the glyph's own light and dark survive when the system takes the colour out, not what
      macOS draws.

Needs resvg and Pillow, and a git history with origin/main for main's icons (the first sheet only).
"""

from __future__ import annotations

import argparse
import json
import re
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


# ---- the macOS 26 icon, composed from the .icon bundle ------------------------------------------------------

APPEARANCE_SIZES = [16, 32, 64, 128, 256]


def colour(spec: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"(?:extended-)?srgb:([\d.]+),([\d.]+),([\d.]+),([\d.]+)", spec)
    if not m:
        raise SystemExit(f"error: icon.json colour {spec!r} is not srgb:r,g,b,a")
    return tuple(round(float(v) * 255) for v in m.groups()[:3])  # type: ignore[return-value]


def fill_of(icon: Path, appearance: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """The top and bottom colours of the .icon's fill for an appearance ("default" or "dark")."""
    data = json.loads((icon / "icon.json").read_text(encoding="utf-8"))
    for spec in data["fill-specializations"]:
        if spec.get("appearance", "default") == appearance:
            top, bottom = spec["value"]["linear-gradient"]
            return colour(top), colour(bottom)
    raise SystemExit(f"error: {icon}/icon.json has no {appearance} fill")


def layer_of(icon: Path) -> Image.Image:
    data = json.loads((icon / "icon.json").read_text(encoding="utf-8"))
    name = data["groups"][0]["layers"][0]["image-name"]
    return Image.open(icon / "Assets" / name).convert("RGBA")


def gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    column = Image.new("RGB", (1, size))
    column.putdata([tuple(round(t + (b - t) * y / (size - 1)) for t, b in zip(top, bottom)) for y in range(size)])
    return column.resize((size, size))


def squircle(canvas: int, body: float) -> Image.Image:
    """The tile's mask on Apple's grid (an 824 of 1024 tile, its corner 22.37% of its side), antialiased by 4x supersampling."""
    k, m = 4, Image.new("L", (canvas * 4, canvas * 4), 0)
    edge = (canvas - body) / 2
    ImageDraw.Draw(m).rounded_rectangle([edge * k, edge * k, (edge + body) * k - 1, (edge + body) * k - 1], radius=body * 0.2237 * k, fill=255)
    return m.resize((canvas, canvas), Image.LANCZOS)


def luminance(layer: Image.Image) -> Image.Image:
    """The layer with its colour taken out (Rec. 709 luma), its alpha as it is: what a tinted or clear style starts from."""
    r, g, b, a = layer.split()
    luma = Image.merge("RGB", (r, g, b)).convert("L")
    return Image.merge("LA", (luma, a)).convert("RGBA")


def appearance_tile(icon: Path, which: str, canvas: int = 1024) -> Image.Image:
    """One appearance of the icon on a transparent `canvas` x `canvas` image: the tile on the grid, the layer on it."""
    body = 824 * canvas / 1024
    mask = squircle(canvas, body)
    side = round(body)
    layer = layer_of(icon).resize((side, side), Image.LANCZOS)
    edge = round((canvas - body) / 2)
    out = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    if which in ("default", "dark"):
        top, bottom = fill_of(icon, which)
        ground = gradient(canvas, top, bottom)
        glyph = layer
    elif which == "tinted":
        # Simulation: the layer's luma mapped from near-black to a mid tint, over a dark tinted tile.
        tint = (110, 150, 235)
        ground = gradient(canvas, (46, 50, 66), (22, 24, 34))
        luma = luminance(layer).getchannel("R")
        glyph = Image.merge("RGBA", (*[luma.point(lambda v, c=c: round(v / 255 * c)) for c in tint], layer.getchannel("A")))
    elif which == "clear":
        # Simulation: the layer's luma as white of that strength over a glassy grey tile.
        ground = gradient(canvas, (150, 156, 168), (96, 102, 114))
        luma = luminance(layer).getchannel("R")
        glyph = Image.merge("RGBA", (luma, luma, luma, layer.getchannel("A")))
    else:
        raise ValueError(which)
    out.paste(ground, (0, 0), mask)
    out.alpha_composite(glyph, (edge, edge))
    # The glyph only inside the tile: nothing of it may reach the mask's outside.
    clipped = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    clipped.paste(out, (0, 0), mask)
    return clipped


def grid_check(icon: Path, which: str) -> Image.Image:
    """A 1024 canvas with the guides drawn over the icon: the 824 tile's box, the glyph's box and the canvas's centre."""
    im = appearance_tile(icon, which, 1024).convert("RGBA")
    layer = layer_of(icon)
    side = 824
    box = layer.resize((side, side), Image.LANCZOS).getchannel("A").point(lambda v: 255 if v > fit.ALPHA_EDGE else 0).getbbox()
    d = ImageDraw.Draw(im)
    x0 = 100
    d.rectangle([x0, x0, x0 + side - 1, x0 + side - 1], outline=(255, 70, 70, 255), width=3)
    if box:
        d.rectangle([x0 + box[0], x0 + box[1], x0 + box[2], x0 + box[3]], outline=(60, 120, 255, 255), width=3)
    d.line([(512, 60), (512, 964)], fill=(40, 200, 120, 255), width=2)
    d.line([(60, 512), (964, 512)], fill=(40, 200, 120, 255), width=2)
    return im.resize((512, 512), Image.LANCZOS)


def appearances_sheet(product: str, icon: Path, out: Path) -> None:
    rows = [("default (light) appearance: the tile of the .icns too", "default"), ("dark appearance", "dark"),
            ("tinted style: SIMULATION from the layer's luma, not macOS's render", "tinted"),
            ("clear style: SIMULATION from the layer's luma, not macOS's render", "clear")]
    cell = lambda s: s * SCALE + PAD  # noqa: E731
    panel_w = sum(cell(s) for s in APPEARANCE_SIZES) + PAD
    band_h = APPEARANCE_SIZES[-1] * SCALE + PAD
    grid_h = 512 + PAD + 40
    head = 70
    sheet = Image.new("RGB", (panel_w * len(GROUNDS), head + band_h * len(rows) + grid_h), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=30)
    small = ImageFont.load_default(size=22)
    cache = {w: appearance_tile(icon, w) for _, w in rows}
    for g, (gname, rgb) in enumerate(GROUNDS.items()):
        x_off = g * panel_w
        d.rectangle([x_off, 0, x_off + panel_w, sheet.height], fill=rgb)
        fg = (20, 24, 32) if gname == "light" else (230, 234, 242)
        d.text((x_off + PAD, 20), f"Facthory {product.capitalize()}: macOS 26 icon, {gname} ground, 2x, sizes {', '.join(map(str, APPEARANCE_SIZES))}", fill=fg, font=font)
        for r, (label, which) in enumerate(rows):
            y_base = head + r * band_h + band_h - PAD // 2
            d.text((x_off + PAD, head + r * band_h + 6), label, fill=fg, font=small)
            x = x_off + PAD
            for s in APPEARANCE_SIZES:
                px = s * SCALE
                im = cache[which].resize((px, px), Image.LANCZOS)
                sheet.paste(im, (x, y_base - px), im)
                x += cell(s)
        y = head + band_h * len(rows)
        d.text((x_off + PAD, y + 4), "grid check: tile (red, 824 of 1024), glyph's box (blue), canvas centre (green); default, then dark", fill=fg, font=small)
        x = x_off + PAD
        for which in ("default", "dark"):
            im = grid_check(icon, which)
            sheet.paste(im, (x, y + 40), im)
            x += 512 + PAD
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    print(out, sheet.size)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--product", required=True, choices=sorted(fit.TILE_BOTTOM))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--appearances", action="store_true", help="the macOS 26 icon's appearances, from app-icon/<base>.icon")
    args = ap.parse_args()
    if args.appearances:
        import tomllib

        base = tomllib.loads((HERE.parent / "brand.toml").read_text(encoding="utf-8"))["icon"]["base"]
        appearances_sheet(args.product, HERE / "app-icon" / f"{base}.icon", args.out or HERE / "proof" / f"{args.product}-appearances.png")
        return 0
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
