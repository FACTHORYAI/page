#!/usr/bin/env python3
"""Collect a release's files and write its checksums, update feed and notes.

  python3 facthory/release.py <dist> <version> <owner/repo>

<dist> holds the build artifacts, as the release workflow downloads them. Writes:

  <dist>/release-files/   the installers and archives, SHA256SUMS, and latest.json
  <dist>/NOTES.md         the release notes

latest.json is the update feed the apps read (from releases/latest/download/latest.json, which
GitHub serves for the newest published, non-draft, non-prerelease release):

  {"name", "version", "date", "notes", "rollout",
   "assets": {"<platform>": {"name", "url", "sha256", "size"}}}

rollout is the percentage of copies the update is offered to: FACTHORY_ROLLOUT from the
environment (the release workflow starts at 10), 100 without it. facthory/rollout.py raises it.

with one asset per platform an app can update itself on: macos-universal (DMG),
windows-x64 and windows-arm64 (MSI), linux-x86_64 and linux-aarch64 (AppImage). The Microsoft
Store installs the same MSI and leaves its updates to the app, so Store copies update from here
too; the .deb and .rpm update through the system's package manager.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Files a release carries, by suffix; anything else in the artifacts is left out.
SHIPPED = (".dmg", ".msi", ".zip", ".AppImage", ".zsync", ".deb", ".rpm", ".tar.gz", ".flatpak")
PLATFORMS = [
    ("macos-universal", re.compile(r"-macos-universal\.dmg$")),
    ("windows-x64", re.compile(r"-windows-x64\.msi$")),
    ("windows-arm64", re.compile(r"-windows-arm64\.msi$")),
    ("linux-x86_64", re.compile(r"-linux-x86_64\.AppImage$")),
    ("linux-aarch64", re.compile(r"-linux-aarch64\.AppImage$")),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    dist, version, repo = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    with (ROOT / "facthory" / "brand.toml").open("rb") as f:
        brand = tomllib.load(f)
    name, upstream = brand["brand"]["name"], brand["upstream"]

    out = dist / "release-files"
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in dist.rglob("*") if p.is_file() and out not in p.parents and p.name.endswith(SHIPPED))
    if not files:
        print(f"error: no release files under {dist}", file=sys.stderr)
        return 1
    seen: set[str] = set()
    for p in files:
        if p.name in seen:
            print(f"error: two artifacts are named {p.name}", file=sys.stderr)
            return 1
        seen.add(p.name)
        shutil.copyfile(p, out / p.name)

    shipped = sorted(out.iterdir())
    sums = {p.name: sha256(p) for p in shipped}
    (out / "SHA256SUMS").write_text("".join(f"{h}  {n}\n" for n, h in sums.items()), encoding="utf-8")

    base = f"https://github.com/{repo}/releases/download/v{version}"
    assets = {}
    for platform, pattern in PLATFORMS:
        match = [p for p in shipped if pattern.search(p.name)]
        if len(match) == 1:
            p = match[0]
            assets[platform] = {"name": p.name, "url": f"{base}/{p.name}", "sha256": sums[p.name], "size": p.stat().st_size}
    feed = {
        "name": name,
        "version": version,
        "date": datetime.date.today().isoformat(),
        "notes": f"https://github.com/{repo}/releases/tag/v{version}",
        "rollout": max(0, min(100, int(os.environ.get("FACTHORY_ROLLOUT") or 100))),
        "assets": assets,
    }
    (out / "latest.json").write_text(json.dumps(feed, indent=2) + "\n", encoding="utf-8")

    upstream_notes = f"{upstream['repository']}/releases/tag/v{version}"
    rows = "\n".join(f"| `{n}` | `{h}` |" for n, h in sums.items())
    (dist / "NOTES.md").write_text(
        f"{name} {version}, based on {upstream['name']} {version} by the {upstream['team']}: "
        f"what changed is in [{upstream['name']}'s release notes]({upstream_notes}).\n\n"
        f"Check a download against `SHA256SUMS` (`sha256sum -c SHA256SUMS --ignore-missing`).\n\n"
        f"| File | SHA-256 |\n| ---- | ------- |\n{rows}\n",
        encoding="utf-8",
    )
    missing = [p for p, _ in PLATFORMS if p not in assets]
    print(f"{len(shipped)} files, update feed for {', '.join(assets) or 'no platform'}")
    if missing:
        print(f"warning: no self-updating asset for {', '.join(missing)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
