#!/usr/bin/env python3
"""Put the appearance-aware icon into a macOS app bundle, and check it.

macOS 26 draws an app's icon from an Icon Composer bundle (`<name>.icon`: icon.json and its layers) compiled
into the bundle's `Assets.car` and named by `CFBundleIconName`: one tile for the light appearance, another for
the dark one, and the tinted and clear styles made by the system from the layer. Earlier systems (and the
Finder's own caches) read `CFBundleIconFile`, the `.icns`, which package.sh already copies in and which stays.
Xcode builds none of this for us, so this script runs `actool` the way Xcode does and puts the result in:

  python3 facthory/appicon.py build --icon assets/app-icon/<name>.icon --app <App>.app
      selects Xcode 26.0.1 (see XCODE), compiles the .icon with actool into a scratch folder, checks the Assets.car
      with `assetutil --info`, copies it to <App>.app/Contents/Resources/, sets CFBundleIconName in Info.plist
      (CFBundleIconFile and the .icns stay as they are) and checks the bundle. It fails on any missing piece.
      Run it before the bundle is signed: Assets.car is a resource, so the signature and notarization cover it.
  python3 facthory/appicon.py check <App>.app
      checks a finished bundle (the same checks, no compile); install_check.py runs it on the installed app.
  python3 facthory/appicon.py source <name>.icon
      checks the .icon bundle itself (valid icon.json, its layers present, a default and a dark fill); runs anywhere.

The only part that needs macOS is `build` and `check` of a car; everything else runs, and is unit-tested, anywhere
(`facthory/test_appicon.py`). Nothing here knows an app's name: the .icon's own name is the icon's name.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Xcode 26.0.1: the runners' (macos-15 image) Xcode that has `actool` for .icon and that still honours
# --enable-icon-stack-fallback-generation=disabled. From 26.1 on, reports say Xcode ignores it and puts
# generated bitmaps of the old icon format into Assets.car, which systems before 26 then show instead of the
# .icns. A runner image without this Xcode fails the build, by name, instead of building another icon.
XCODE = "26.0.1"
XCODE_FOLDER = "/Applications"
# The oldest system that reads an icon stack; the .icns serves the rest.
ICON_TARGET = "26.0"

# What a car must hold for the icon's name, by variant: a substring looked for (lower case) in the JSON of the
# icon's entries of `assetutil --info`. "default" has none: any entry of the icon is it.
VARIANTS = {"default": None, "dark": "dark"}
# Listed in the log when present, never required: the system makes these from the layer, and which entries
# assetutil shows for them is not something Apple documents.
LISTED = {"tinted": "tint", "clear": "clear"}


class AppIconError(Exception):
    pass


# ---- the source ---------------------------------------------------------------------------------------------


def check_source(icon: Path) -> dict:
    """The .icon bundle's icon.json, checked: the layers it names exist, a default fill and a dark fill exist."""
    manifest = icon / "icon.json"
    if icon.suffix != ".icon" or not manifest.is_file():
        raise AppIconError(f"{icon} is not an Icon Composer bundle (a folder `<name>.icon` with an icon.json)")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise AppIconError(f"{manifest}: {e}") from e
    groups = data.get("groups")
    if not isinstance(groups, list) or not groups:
        raise AppIconError(f"{manifest}: no groups")
    layers = [layer for g in groups for layer in g.get("layers", [])]
    if not layers:
        raise AppIconError(f"{manifest}: no layer")
    for layer in layers:
        name = layer.get("image-name")
        if not name or not (icon / "Assets" / name).is_file():
            raise AppIconError(f"{manifest}: layer {layer.get('name')!r} names {name!r}, which is not in {icon / 'Assets'}")
    appearances = {s.get("appearance", "default") for s in data.get("fill-specializations", [])}
    for want in ("default", "dark"):
        if want not in appearances:
            raise AppIconError(f"{manifest}: no {want} fill in fill-specializations (has {sorted(appearances)})")
    return data


# ---- Xcode --------------------------------------------------------------------------------------------------


def developer_dir(folder: str = XCODE_FOLDER, version: str = XCODE) -> Path:
    """The developer folder of the pinned Xcode, as GitHub's macOS images install it (Xcode_<version>.app)."""
    app = Path(folder) / f"Xcode_{version}.app"
    if not app.is_dir():
        have = sorted(p.name for p in Path(folder).glob("Xcode*.app")) if Path(folder).is_dir() else []
        raise AppIconError(f"Xcode {version} is not installed in {folder} (has: {', '.join(have) or 'none'}); the icon needs its actool")
    return app / "Contents" / "Developer"


def actool_args(icon: Path, out: Path, partial: Path) -> list[str]:
    """actool's command line: the one Tauri's bundler uses for an .icon (the whole catalog is the bundle), with the
    old-format fallbacks off. The icon's name for --app-icon is the bundle's name without `.icon`."""
    return [
        "xcrun", "actool", str(icon),
        "--compile", str(out),
        "--output-format", "human-readable-text", "--notices", "--warnings", "--errors",
        "--output-partial-info-plist", str(partial),
        "--app-icon", icon.stem, "--include-all-app-icons",
        "--enable-icon-stack-fallback-generation=disabled",
        "--development-region", "en", "--target-device", "mac",
        "--minimum-deployment-target", ICON_TARGET, "--platform", "macosx",
    ]  # fmt: skip


def run(args: list[str], env: dict[str, str] | None = None) -> str:
    r = subprocess.run(args, capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL, check=False)
    if r.returncode != 0:
        raise AppIconError(f"{' '.join(args[:3])} failed ({r.returncode}):\n{r.stdout}{r.stderr}")
    return r.stdout


# ---- the car ------------------------------------------------------------------------------------------------


def icon_entries(info: object, name: str) -> list[dict]:
    """The entries of `assetutil --info` (a JSON array) that are the named icon's images."""
    if not isinstance(info, list):
        raise AppIconError("assetutil --info did not print a JSON array")
    return [e for e in info if isinstance(e, dict) and e.get("AssetType") == "Icon Image" and e.get("Name") == name]


def check_car_info(info: object, name: str) -> list[str]:
    """What the car's listing says about the icon `name`: lines for the log. Raises when the icon or a variant is missing."""
    entries = icon_entries(info, name)
    if not entries:
        names = sorted({str(e.get("Name")) for e in info if isinstance(e, dict) and e.get("AssetType") == "Icon Image"}) if isinstance(info, list) else []
        raise AppIconError(f"Assets.car has no icon image named {name!r} (icon images: {', '.join(names) or 'none'})")
    text = [json.dumps(e, sort_keys=True).lower() for e in entries]
    lines = [f"{len(entries)} icon image(s) named {name!r}", *(f"  {t[:240]}" for t in text[:40])]
    for variant, token in VARIANTS.items():
        n = len(text) if token is None else sum(token in t for t in text)
        if n == 0:
            raise AppIconError(
                f"Assets.car lacks the {variant} variant of {name!r}: none of its {len(entries)} icon images mentions {token!r}. "
                f"Its icon images, to see what assetutil calls the variants:\n" + "\n".join(f"  {t[:400]}" for t in text[:40])
            )
        lines.append(f"{variant}: {n} entr{'y' if n == 1 else 'ies'}")
    for variant, token in LISTED.items():
        n = sum(token in t for t in text)
        lines.append(f"{variant}: {n} entr{'y' if n == 1 else 'ies'} listed (made by the system from the layer; not required)")
    return lines


def car_info(car: Path, env: dict[str, str] | None = None) -> object:
    try:
        return json.loads(run(["xcrun", "assetutil", "--info", str(car)], env))
    except ValueError as e:
        raise AppIconError(f"assetutil --info {car}: not JSON ({e})") from e


# ---- the bundle ---------------------------------------------------------------------------------------------


def check_bundle_files(app: Path, name: str) -> list[str]:
    """What a bundle needs besides the car's contents: the car, CFBundleIconName naming the icon, and the
    .icns that CFBundleIconFile names, for systems that do not read the car's icon."""
    info = app / "Contents" / "Info.plist"
    try:
        plist = plistlib.loads(info.read_bytes())
    except (OSError, ValueError) as e:
        raise AppIconError(f"{info}: {e}") from e
    if plist.get("CFBundleIconName") != name:
        raise AppIconError(f"{info}: CFBundleIconName is {plist.get('CFBundleIconName')!r}, want {name!r}")
    file = plist.get("CFBundleIconFile")
    if not file:
        raise AppIconError(f"{info}: no CFBundleIconFile, so systems before macOS 26 have no icon")
    icns = app / "Contents" / "Resources" / (file if file.endswith(".icns") else f"{file}.icns")
    if not icns.is_file() or icns.read_bytes()[:4] != b"icns":
        raise AppIconError(f"{icns}: the .icns that CFBundleIconFile names is missing or not an icns file")
    if not (app / "Contents" / "Resources" / "Assets.car").is_file():
        raise AppIconError(f"{app}: Contents/Resources/Assets.car is missing")
    return [f"CFBundleIconName {name}, CFBundleIconFile {file} ({icns.stat().st_size} bytes), Assets.car {(app / 'Contents' / 'Resources' / 'Assets.car').stat().st_size} bytes"]


def icon_name_of(app: Path) -> str:
    plist = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
    name = plist.get("CFBundleIconName")
    if not isinstance(name, str) or not name:
        raise AppIconError(f"{app}: Info.plist has no CFBundleIconName")
    return name


def say(lines: list[str]) -> None:
    for line in lines:
        print(f"appicon: {line}")


def build(icon: Path, app: Path, folder: str = XCODE_FOLDER) -> None:
    check_source(icon)
    name = icon.stem
    if not (app / "Contents" / "Info.plist").is_file():
        raise AppIconError(f"{app} has no Contents/Info.plist (assemble the bundle first)")
    env = {**os.environ, "DEVELOPER_DIR": str(developer_dir(folder))}
    # `xcrun --find` fails the build early, with a clear name, if the pinned Xcode has no actool.
    version = run(["xcrun", "actool", "--version", "--output-format=human-readable-text"], env)
    major = re.search(r"short-bundle-version:\s*(\d+)", version)
    if not major or int(major.group(1)) < 26:
        raise AppIconError(f"actool is too old for .icon (need 26 or later):\n{version}")
    with tempfile.TemporaryDirectory() as tmp:
        out, partial = Path(tmp) / "out", Path(tmp) / "partial.plist"
        out.mkdir()
        log = run(actool_args(icon, out, partial), env)
        print(log.rstrip())
        car = out / "Assets.car"
        if not car.is_file():
            raise AppIconError("actool wrote no Assets.car")
        say(check_car_info(car_info(car, env), name))
        # The partial Info.plist is only read, never merged: its CFBundleIconFile would replace our .icns.
        try:
            keys = plistlib.loads(partial.read_bytes())
            say([f"actool's partial Info.plist: { {k: v for k, v in keys.items() if k.startswith('CFBundleIcon')} }"])
        except (OSError, ValueError):
            say(["actool wrote no readable partial Info.plist (only logged, never merged)"])
        shutil.copyfile(car, app / "Contents" / "Resources" / "Assets.car")
    # plutil -replace inserts the key when it is not there.
    run(["plutil", "-replace", "CFBundleIconName", "-string", name, str(app / "Contents" / "Info.plist")])
    run(["plutil", "-lint", str(app / "Contents" / "Info.plist")])
    check_app(app, env)


def tool_env(folder: str = XCODE_FOLDER) -> dict[str, str] | None:
    """The environment of the pinned Xcode's tools when it is installed (its assetutil reads what its actool wrote), else the default's."""
    try:
        return {**os.environ, "DEVELOPER_DIR": str(developer_dir(folder))}
    except AppIconError:
        return None


def check_app(app: Path, env: dict[str, str] | None = None) -> None:
    env = env or tool_env()
    name = icon_name_of(app)
    say(check_bundle_files(app, name))
    say(check_car_info(car_info(app / "Contents" / "Resources" / "Assets.car", env), name))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="compile the .icon and put it in the bundle")
    b.add_argument("--icon", type=Path, required=True)
    b.add_argument("--app", type=Path, required=True)
    c = sub.add_parser("check", help="check a finished bundle")
    c.add_argument("app", type=Path)
    s = sub.add_parser("source", help="check the .icon bundle")
    s.add_argument("icon", type=Path)
    args = ap.parse_args()
    try:
        if args.cmd == "build":
            build(args.icon, args.app)
        elif args.cmd == "check":
            check_app(args.app)
        else:
            check_source(args.icon)
            print(f"appicon: {args.icon} is a valid icon bundle")
    except AppIconError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
