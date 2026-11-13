#!/usr/bin/env python3
"""Render the app icon set from the composed SVGs (facthory/icons/compose.py) into
facthory/icons/app-icon/, in the layout of upstream's assets/app-icon/ after the rebrand renames it
(rebrand.py copies it over). [icon] in brand.toml names the four SVGs and the file base:

  svg              the tile at the canvas edge (Windows, Linux, the scalable icon)
  macos_svg        on Apple's grid: an 824 x 824 body in the 1024 canvas, with its shadow
  small_svg        the simplified form for Windows and Linux icons of 24 pixels and under
  macos_small_svg  the same for macOS icons of 32 pixels and under (16 points, at 1x and 2x)

macos_512 and svg_copy (default true) say whether upstream's layout has <base>-macos-512.png and
<base>.svg. author, source and licence credit the icon in ATTRIBUTION.md (default: Bandpey GmbH's
original artwork), and note is a paragraph at the end of ATTRIBUTION.md's Facthory block, which ships.

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
# Up to these pixel sizes the simplified form is used: the hero alone, larger.
SMALL_PX = 24
SMALL_MACOS_PX = 32
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


def attribution(brand: dict, out: Path) -> None:
    """Credit Facthory's own files in ATTRIBUTION.md: one block right under the title, replaced in
    place when it exists. The composed icons, the icon set, then brand.toml's [[asset]] entries."""
    path = ROOT / "ATTRIBUTION.md"
    text = path.read_text(encoding="utf-8")
    icon = brand["icon"]
    author, licence = icon.get("author", "Bandpey GmbH"), icon.get("licence", "MIT OR Apache-2.0")
    source = icon.get("source", "original artwork")
    svgs = [HERE / icon[k] for k in ("svg", "macos_svg", "small_svg", "macos_small_svg") if k in icon]
    mac_files = {out / f"{icon['base']}.icns", out / f"{icon['base']}-macos-512.png"}
    rows = [f"| `{p.relative_to(ROOT).as_posix()}` | {author} | {source} | {licence} |" for p in svgs]
    mac = HERE / icon.get("macos_svg", icon["svg"])
    def made_from(p: Path) -> Path:
        if p.name.endswith("-logo-light.png"):
            return HERE / "brand" / "mark.svg"
        if p.name.endswith("-logo-dark.png"):
            return HERE / "brand" / "mark-mono.svg"
        return mac if p in mac_files else HERE / icon["svg"]

    rows += [
        f"| `{p.relative_to(ROOT).as_posix()}` | {author} | rendered from `{made_from(p).relative_to(ROOT).as_posix()}` "
        f"by `facthory/icons/render.py` | {licence} |"
        for p in sorted(out.rglob("*"))
        if p.is_file()
    ]
    rows += [f"| `facthory/{a['path']}` | {a['author']} | {a['source']} | {a['licence']} |" for a in brand.get("asset", [])]
    note = ["", icon["note"].strip()] if "note" in icon else []
    block = "\n".join(
        [f"{BEGIN}: Facthory's own files, written by facthory/icons/render.py; see facthory/README.md -->",
         "| Facthory asset | Author | Source | Licence |", "|---|---|---|---|", *rows, *note, END]
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
    svg = HERE / icon["svg"]
    mac_svg = HERE / icon["macos_svg"]
    small = HERE / icon.get("small_svg", icon["svg"])
    mac_small = HERE / icon.get("macos_small_svg", icon["macos_svg"])
    # Check the sources before anything is deleted, so a typo in brand.toml leaves the set alone.
    for s in (svg, mac_svg, small, mac_small):
        if not s.is_file() or 'viewBox="0 0 1024 1024"' not in s.read_text(encoding="utf-8"):
            print(f"error: {s} is missing or lacks viewBox=\"0 0 1024 1024\" (python3 facthory/icons/compose.py)", file=sys.stderr)
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

        def flat(size: int) -> Path:
            return small if size <= SMALL_PX else svg

        def mac(size: int) -> Path:
            return mac_small if size <= SMALL_MACOS_PX else mac_svg

        render(svg, 1024, out / f"{base}-1024.png")
        if icon.get("macos_512", True):
            render(mac_svg, 512, out / f"{base}-macos-512.png")
        for s in HICOLOR:
            render(flat(s), s, out / "hicolor" / f"{s}x{s}" / "apps" / f"{app_id}.png")
        (out / "hicolor" / "scalable" / "apps").mkdir(parents=True)
        shutil.copyfile(svg, out / "hicolor" / "scalable" / "apps" / f"{app_id}.svg")
        if icon.get("svg_copy", True):
            shutil.copyfile(svg, out / f"{base}.svg")
        (out / f"{base}.ico").write_bytes(ico({s: render(flat(s), s, tmp / f"ico-{s}.png") for s in ICO}))
        mac_pngs = {s: render(mac(s), s, tmp / f"mac-{s}.png") for s in sorted({s for _, s in ICNS})}
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
