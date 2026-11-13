#!/usr/bin/env python3
"""Render the app icon set from the fitted SVGs (facthory/icons/fit.py) into facthory/icons/app-icon/,
in the layout of upstream's assets/app-icon/ after the rebrand renames it (rebrand.py copies it
over). [icon] in brand.toml names the files and the file base:

  glyph      the glyph, unchanged (with icons' Chrome style, recoloured): the source of the others
  svg        Windows, Linux and the scalable icon: the free-form glyph, its longer side 88% of 1024
  macos_svg  macOS: an 824 x 824 tile on Apple's grid in the 1024 canvas, the glyph at about 75% of its width

macos_512 and svg_copy (default true) say whether upstream's layout has <base>-macos-512.png and
<base>.svg. author, source and licence credit the glyph and its renders in ATTRIBUTION.md, notice
names a licence file beside the SVGs whose text ends ATTRIBUTION.md's Facthory block (which ships),
and note is a paragraph after it. Facthory's own marks (the About box's two renders of them) are
credited as the trademark they are.

Needs resvg (cargo install resvg). The outputs are committed, so builds never need it. Writes
the .ico and .icns containers itself (PNG entries), so no macOS or Windows tool is needed.

Upstream's `cargo xtask assets` needs an ATTRIBUTION.md row for every image in the repository, so
this also writes one marked block under ATTRIBUTION.md's title that credits these files; upstream
seldom edits the top of that file, so merges rarely touch the block.

  python3 facthory/icons/render.py                 render, then write the block
  python3 facthory/icons/render.py --attribution   only rewrite the block (after an upstream merge)
"""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BEGIN = "<!-- facthory:begin"
END = "<!-- facthory:end -->"
HICOLOR = [16, 24, 32, 48, 64, 128, 256, 512]
ICO = [16, 20, 24, 32, 40, 48, 64, 128, 256]
# The About box's mark: 72 points at up to 2.5x.
LOGO_PX = 192
# icns entry types holding PNG data, by pixel size; the @2x types reuse the same pixels.
ICNS = [("icp4", 16), ("icp5", 32), ("icp6", 64), ("ic07", 128), ("ic08", 256), ("ic09", 512), ("ic10", 1024),
        ("ic11", 32), ("ic12", 64), ("ic13", 256), ("ic14", 512)]


def render(svg: Path, size: int, out: Path) -> bytes:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["resvg", "-w", str(size), "-h", str(size), str(svg), str(out)], check=True, stdin=subprocess.DEVNULL)
    return out.read_bytes()


def render_height(svg: Path, height: int, out: Path) -> None:
    """Render `svg` at its own proportions, `height` pixels tall."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["resvg", "-h", str(height), str(svg), str(out)], check=True, stdin=subprocess.DEVNULL)


def ico(pngs: dict[int, bytes]) -> bytes:
    head = struct.pack("<HHH", 0, 1, len(pngs))
    entries, data, offset = b"", b"", 6 + 16 * len(pngs)
    for size, png in sorted(pngs.items()):
        dim = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        data += png
        offset += len(png)
    return head + entries + data


def icns(pngs: dict[int, bytes]) -> bytes:
    body = b"".join(kind.encode() + struct.pack(">I", 8 + len(pngs[size])) + pngs[size] for kind, size in ICNS)
    return b"icns" + struct.pack(">I", 8 + len(body)) + body


MARK_LICENCE = "Facthory trademark, all rights reserved: not open source; usable unmodified only"


def attribution(brand: dict, out: Path) -> None:
    """Credit Facthory's own files in ATTRIBUTION.md: one block right under the title, replaced in
    place when it exists. The glyph and its fitted SVGs, the icon set, then brand.toml's [[asset]]
    entries, and the glyph's licence text."""
    path = ROOT / "ATTRIBUTION.md"
    text = path.read_text(encoding="utf-8")
    icon = brand["icon"]
    author, licence = icon.get("author", "Bandpey GmbH"), icon.get("licence", "MIT OR Apache-2.0")
    source = icon.get("source", "original artwork")
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731
    glyph = HERE / icon.get("glyph", icon["svg"])
    flat, mac = HERE / icon["svg"], HERE / icon["macos_svg"]
    rows = [f"| `{rel(glyph)}` | {author} | {source} | {licence} |"]
    for p, what in ((mac, "on Apple's grid"), (flat, "for Windows and Linux")):
        if p != glyph:
            rows.append(f"| `{rel(p)}` | {author} | `{rel(glyph)}` scaled and placed {what} by `facthory/icons/fit.py`; the glyph itself is unchanged | {licence} |")
    mac_files = {out / f"{icon['base']}.icns", out / f"{icon['base']}-macos-512.png"}
    for p in sorted(out.rglob("*")):
        if not p.is_file():
            continue
        if p.name.endswith("-logo-light.png") or p.name.endswith("-logo-dark.png"):
            mark = HERE / "brand" / ("mark.svg" if p.name.endswith("-light.png") else "mark-mono.svg")
            rows.append(f"| `{rel(p)}` | Bandpey GmbH | rendered from `{rel(mark)}`, the Facthory mark, by `facthory/icons/render.py` (drawn in the About box) | {MARK_LICENCE} |")
            rows.append(f"| `assets/app-icon/{p.name}` | Bandpey GmbH | the branded tree's copy of `{rel(p)}` | {MARK_LICENCE} |")
        else:
            rows.append(f"| `{rel(p)}` | {author} | rendered from `{rel(mac if p in mac_files else flat)}` by `facthory/icons/render.py` | {licence} |")
    rows += [f"| `facthory/{a['path']}` | {a['author']} | {a['source']} | {a['licence']} |" for a in brand.get("asset", [])]
    # The glyph's licence text goes in the block, so it travels wherever ATTRIBUTION.md does.
    tail = []
    if "notice" in icon:
        tail += ["", f"The app icon's licence ({licence}), from `{rel(HERE / icon['notice'])}`:", "", "```text", (HERE / icon["notice"]).read_text(encoding="utf-8").strip(), "```"]
    if "note" in icon:
        tail += ["", icon["note"].strip()]
    block = "\n".join(
        [f"{BEGIN}: Facthory's own files, written by facthory/icons/render.py; see facthory/README.md -->",
         "| Facthory asset | Author | Source | Licence |", "|---|---|---|---|", *rows, *tail, END]
    )
    if BEGIN in text:
        start = text.index(BEGIN)
        end = text.index(END, start) + len(END)
        text = text[:start] + block + text[end:]
    else:
        title, _, rest = text.partition("\n")
        text = f"{title}\n\n{block}\n{rest}"
    path.write_text(text, encoding="utf-8")


def main() -> int:
    with (HERE.parent / "brand.toml").open("rb") as f:
        brand = tomllib.load(f)
    icon, out = brand["icon"], HERE / "app-icon"
    svg, mac_svg = HERE / icon["svg"], HERE / icon["macos_svg"]
    glyph = HERE / icon.get("glyph", icon["svg"])
    # Check the sources before anything is deleted, so a typo in brand.toml leaves the set alone.
    for s in (svg, mac_svg):
        if not s.is_file() or 'viewBox="0 0 1024 1024"' not in s.read_text(encoding="utf-8"):
            print(f"error: {s} is missing or lacks viewBox=\"0 0 1024 1024\" (python3 facthory/icons/fit.py)", file=sys.stderr)
            return 1
    if not glyph.is_file():
        print(f"error: {glyph} is missing", file=sys.stderr)
        return 1
    if "notice" in icon and not (HERE / icon["notice"]).is_file():
        print(f"error: {HERE / icon['notice']} is missing", file=sys.stderr)
        return 1
    if sys.argv[1:] == ["--attribution"]:
        attribution(brand, out)
        return 0
    if not shutil.which("resvg"):
        print("error: resvg not found (cargo install resvg)", file=sys.stderr)
        return 1
    app_id, base = brand["brand"]["app_id"], icon["base"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        render(svg, 1024, out / f"{base}-1024.png")
        if icon.get("macos_512", True):
            render(mac_svg, 512, out / f"{base}-macos-512.png")
        for s in HICOLOR:
            render(svg, s, out / "hicolor" / f"{s}x{s}" / "apps" / f"{app_id}.png")
        (out / "hicolor" / "scalable" / "apps").mkdir(parents=True)
        shutil.copyfile(svg, out / "hicolor" / "scalable" / "apps" / f"{app_id}.svg")
        if icon.get("svg_copy", True):
            shutil.copyfile(svg, out / f"{base}.svg")
        (out / f"{base}.ico").write_bytes(ico({s: render(svg, s, tmp / f"ico-{s}.png") for s in ICO}))
        mac_pngs = {s: render(mac_svg, s, tmp / f"mac-{s}.png") for s in sorted({s for _, s in ICNS})}
        (out / f"{base}.icns").write_bytes(icns(mac_pngs))
        # Facthory's mark for the About box, one file per theme: light grounds get the mark, dark
        # grounds its mono file (the app picks by theme; facthory/ui/facthory_logo.rs).
        render_height(HERE / "brand" / "mark.svg", LOGO_PX, out / f"{base}-logo-light.png")
        render_height(HERE / "brand" / "mark-mono.svg", LOGO_PX, out / f"{base}-logo-dark.png")
    attribution(brand, out)
    print(f"icons written to {out.relative_to(ROOT)}; ATTRIBUTION.md credits them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
