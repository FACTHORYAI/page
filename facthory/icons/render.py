#!/usr/bin/env python3
"""Render the app icon set from facthory/icons/<svg> into facthory/icons/app-icon/, in the
layout of upstream's assets/app-icon/ after the rebrand renames it (rebrand.py copies it over).
[icon] in brand.toml names the SVG and the file base; macos_512 and svg_copy (default true) say
whether upstream's layout has <base>-macos-512.png and <base>.svg. macos_svg (default: svg) is the
SVG the macOS files (<base>.icns, <base>-macos-512.png) are rendered from. author, source and
licence credit the icon in ATTRIBUTION.md (default: Bandpey GmbH's original artwork).

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
# icns entry types holding PNG data, by pixel size; the @2x types reuse the same pixels.
ICNS = [("icp4", 16), ("icp5", 32), ("icp6", 64), ("ic07", 128), ("ic08", 256), ("ic09", 512), ("ic10", 1024),
        ("ic11", 32), ("ic12", 64), ("ic13", 256), ("ic14", 512)]


def render(svg: Path, size: int, out: Path) -> bytes:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["resvg", "-w", str(size), "-h", str(size), str(svg), str(out)], check=True, stdin=subprocess.DEVNULL)
    return out.read_bytes()


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


def attribution(brand: dict, svg: Path, out: Path) -> None:
    """Credit Facthory's own files in ATTRIBUTION.md: one block right under the title, replaced in
    place when it exists. The icon set, then brand.toml's [[asset]] entries."""
    path = ROOT / "ATTRIBUTION.md"
    text = path.read_text(encoding="utf-8")
    icon = brand["icon"]
    author, licence = icon.get("author", "Bandpey GmbH"), icon.get("licence", "MIT OR Apache-2.0")
    mac = HERE / icon.get("macos_svg", icon["svg"])
    mac_files = {out / f"{icon['base']}.icns", out / f"{icon['base']}-macos-512.png"}
    rows = [f"| `{s.relative_to(ROOT).as_posix()}` | {author} | {icon.get('source', 'original artwork')} | {licence} |"
            for s in dict.fromkeys([svg, mac])]
    rows += [
        f"| `{p.relative_to(ROOT).as_posix()}` | {author} | rendered from `{(mac if p in mac_files else svg).relative_to(ROOT).as_posix()}` "
        f"by `facthory/icons/render.py` | {licence} |"
        for p in sorted(out.rglob("*"))
        if p.is_file()
    ]
    rows += [f"| `facthory/{a['path']}` | {a['author']} | {a['source']} | {a['licence']} |" for a in brand.get("asset", [])]
    block = "\n".join(
        [f"{BEGIN}: Facthory's own files, written by facthory/icons/render.py; see facthory/README.md -->",
         "| Facthory asset | Author | Source | Licence |", "|---|---|---|---|", *rows, END]
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
    svg, out = HERE / brand["icon"]["svg"], HERE / "app-icon"
    if sys.argv[1:] == ["--attribution"]:
        attribution(brand, svg, out)
        return 0
    if not shutil.which("resvg"):
        print("error: resvg not found (cargo install resvg)", file=sys.stderr)
        return 1
    icon, app_id, base = brand["icon"], brand["brand"]["app_id"], brand["icon"]["base"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # macOS icons sit on Apple's grid: an 824/1024 body with a transparent margin.
        mac, mac_svg = tmp / "mac.svg", HERE / icon.get("macos_svg", icon["svg"])
        for s in (svg, mac_svg):
            if 'viewBox="0 0 512 512"' not in s.read_text(encoding="utf-8"):
                print(f"error: expected viewBox=\"0 0 512 512\" in {s}", file=sys.stderr)
                return 1
        text = mac_svg.read_text(encoding="utf-8")
        mac.write_text(text.replace('viewBox="0 0 512 512"', 'viewBox="-62.136 -62.136 636.272 636.272"'), encoding="utf-8")

        render(svg, 1024, out / f"{base}-1024.png")
        if icon.get("macos_512", True):
            render(mac, 512, out / f"{base}-macos-512.png")
        for s in HICOLOR:
            render(svg, s, out / "hicolor" / f"{s}x{s}" / "apps" / f"{app_id}.png")
        (out / "hicolor" / "scalable" / "apps").mkdir(parents=True)
        shutil.copyfile(svg, out / "hicolor" / "scalable" / "apps" / f"{app_id}.svg")
        if icon.get("svg_copy", True):
            shutil.copyfile(svg, out / f"{base}.svg")
        (out / f"{base}.ico").write_bytes(ico({s: render(svg, s, tmp / f"ico-{s}.png") for s in ICO}))
        mac_pngs = {s: render(mac, s, tmp / f"mac-{s}.png") for s in sorted({s for _, s in ICNS})}
        (out / f"{base}.icns").write_bytes(icns(mac_pngs))
    attribution(brand, svg, out)
    print(f"icons written to {out.relative_to(ROOT)}; ATTRIBUTION.md credits them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
