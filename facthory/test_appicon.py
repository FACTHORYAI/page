#!/usr/bin/env python3
"""Tests of appicon.py that need no macOS: the .icon source, the car checks against listings of the shape
`assetutil --info` prints (a JSON array; `Icon Image` entries with a `Name`, as Tauri's bundler reads them),
the bundle checks, the actool command line and the Xcode selection. `build` itself needs macOS and runs in the
release workflow's macOS job.

  python3 facthory/test_appicon.py
"""

from __future__ import annotations

import json
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import appicon  # noqa: E402

ICON = HERE / "icons" / "app-icon" / "facthorypage.icon"


def listing(*appearances: str, name: str = "facthorypage") -> list[dict]:
    return [{"AssetType": "Icon Image", "Name": name, "Appearance": a, "PixelWidth": 1024} for a in appearances] + [
        {"AssetType": "Color", "Name": "AccentColor"}
    ]


class Source(unittest.TestCase):
    def test_the_committed_icon_is_valid(self) -> None:
        data = appicon.check_source(ICON)
        self.assertEqual(data["supported-platforms"], {"squares": "shared"})

    def copy(self, tmp: str, edit) -> Path:
        icon = Path(tmp) / "x.icon"
        (icon / "Assets").mkdir(parents=True)
        for f in ICON.rglob("*"):
            if f.is_file():
                target = icon / f.relative_to(ICON)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())
        data = json.loads((icon / "icon.json").read_text())
        edit(icon, data)
        (icon / "icon.json").write_text(json.dumps(data))
        return icon

    def test_a_missing_layer_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            icon = self.copy(tmp, lambda i, d: d["groups"][0]["layers"][0].update({"image-name": "gone.png"}))
            with self.assertRaisesRegex(appicon.AppIconError, "gone.png"):
                appicon.check_source(icon)

    def test_a_missing_dark_fill_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            icon = self.copy(tmp, lambda i, d: d.update({"fill-specializations": d["fill-specializations"][:1]}))
            with self.assertRaisesRegex(appicon.AppIconError, "no dark fill"):
                appicon.check_source(icon)

    def test_a_folder_that_is_not_an_icon_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(appicon.AppIconError):
                appicon.check_source(Path(tmp))


class Car(unittest.TestCase):
    def test_default_and_dark_pass(self) -> None:
        lines = appicon.check_car_info(listing("NSAppearanceNameAqua", "NSAppearanceNameDarkAqua"), "facthorypage")
        self.assertTrue(any(line.startswith("dark: 1") for line in lines))

    def test_a_car_without_dark_fails_and_shows_what_it_has(self) -> None:
        with self.assertRaisesRegex(appicon.AppIconError, "(?s)lacks the dark variant.*nsappearancenameaqua"):
            appicon.check_car_info(listing("NSAppearanceNameAqua"), "facthorypage")

    def test_a_car_without_the_icon_fails(self) -> None:
        with self.assertRaisesRegex(appicon.AppIconError, "(?s)no icon image named 'facthorypage' .*other"):
            appicon.check_car_info(listing("dark", name="other"), "facthorypage")

    def test_tinted_is_listed_not_required(self) -> None:
        lines = appicon.check_car_info(listing("light", "dark", "tinted"), "facthorypage")
        self.assertIn("tinted: 1 entry listed (made by the system from the layer; not required)", lines)
        lines = appicon.check_car_info(listing("light", "dark"), "facthorypage")
        self.assertIn("tinted: 0 entries listed (made by the system from the layer; not required)", lines)

    def test_not_a_listing_fails(self) -> None:
        with self.assertRaises(appicon.AppIconError):
            appicon.check_car_info({"a": 1}, "facthorypage")


def bundle(root: Path, name: str = "facthorypage", icns: bytes = b"icns....", car: bool = True, icon_file: str | None = "App") -> Path:
    app = root / "App.app"
    res = app / "Contents" / "Resources"
    res.mkdir(parents=True)
    plist: dict = {"CFBundleIconName": name}
    if icon_file:
        plist["CFBundleIconFile"] = icon_file
        (res / f"{icon_file}.icns").write_bytes(icns)
    (app / "Contents" / "Info.plist").write_bytes(plistlib.dumps(plist))
    if car:
        (res / "Assets.car").write_bytes(b"car")
    return app


class Bundle(unittest.TestCase):
    def test_a_complete_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            appicon.check_bundle_files(bundle(Path(tmp)), "facthorypage")

    def test_the_fallback_icns_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "no CFBundleIconFile"):
                appicon.check_bundle_files(bundle(Path(tmp), icon_file=None), "facthorypage")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "not an icns file"):
                appicon.check_bundle_files(bundle(Path(tmp), icns=b"PNG...."), "facthorypage")

    def test_the_car_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "Assets.car is missing"):
                appicon.check_bundle_files(bundle(Path(tmp), car=False), "facthorypage")

    def test_the_icon_name_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "CFBundleIconName is 'other'"):
                appicon.check_bundle_files(bundle(Path(tmp), name="other"), "facthorypage")


class Tools(unittest.TestCase):
    def test_actool_is_given_the_icon_as_the_catalog_and_the_old_format_off(self) -> None:
        args = appicon.actool_args(Path("/x/facthorypage.icon"), Path("/o"), Path("/o/p.plist"))
        self.assertEqual(args[:3], ["xcrun", "actool", "/x/facthorypage.icon"])
        self.assertEqual(args[args.index("--app-icon") + 1], "facthorypage")
        self.assertIn("--enable-icon-stack-fallback-generation=disabled", args)
        self.assertEqual(args[args.index("--minimum-deployment-target") + 1], "26.0")

    def test_the_pinned_xcode_is_found_by_name_or_the_build_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Xcode_16.4.app").mkdir()
            with self.assertRaisesRegex(appicon.AppIconError, "Xcode 26.0.1 is not installed.*Xcode_16.4.app"):
                appicon.developer_dir(tmp)
            (Path(tmp) / f"Xcode_{appicon.XCODE}.app").mkdir()
            self.assertEqual(appicon.developer_dir(tmp), Path(tmp) / f"Xcode_{appicon.XCODE}.app" / "Contents" / "Developer")


XCRUN = """#!/usr/bin/env python3
import json, sys
tool, args = sys.argv[1], sys.argv[2:]
if tool == "actool" and "--version" in args:
    print("short-bundle-version: 26.0\\n")
elif tool == "actool":
    out = args[args.index("--compile") + 1]
    open(out + "/Assets.car", "wb").write(b"car")
    open(args[args.index("--output-partial-info-plist") + 1], "wb").write(b"")
    print("actool ok")
elif tool == "assetutil":
    name = "facthorypage"
    print(json.dumps([{"AssetType": "Icon Image", "Name": name, "Appearance": a} for a in %r]))
else:
    sys.exit("unexpected " + tool)
"""
PLUTIL = """#!/usr/bin/env python3
import plistlib, sys
if sys.argv[1] == "-replace":
    path = sys.argv[-1]
    plist = plistlib.load(open(path, "rb"))
    plist[sys.argv[2]] = sys.argv[4]
    plistlib.dump(plist, open(path, "wb"))
"""


class Build(unittest.TestCase):
    """build() end to end with stand-ins for xcrun and plutil, which exist on macOS only: the glue is tested here, the
    real tools' output in the macOS job."""

    def run_build(self, tmp: Path, appearances: list[str], xcode: bool = True) -> Path:
        import os
        import stat

        folder = tmp / "Applications"
        (folder / (f"Xcode_{appicon.XCODE}.app" if xcode else "Xcode_16.4.app")).mkdir(parents=True)
        bin_ = tmp / "bin"
        bin_.mkdir()
        for name, text in (("xcrun", XCRUN % appearances), ("plutil", PLUTIL)):
            (bin_ / name).write_text(text)
            (bin_ / name).chmod(stat.S_IRWXU)
        app = bundle(tmp, name="stale")
        # The bundle as package.sh leaves it before the icon step: the .icns and the plist, no CFBundleIconName.
        plist = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
        del plist["CFBundleIconName"]
        (app / "Contents" / "Info.plist").write_bytes(plistlib.dumps(plist))
        (app / "Contents" / "Resources" / "Assets.car").unlink()
        old = os.environ["PATH"]
        os.environ["PATH"] = f"{bin_}{os.pathsep}{old}"
        try:
            appicon.build(ICON, app, str(folder))
        finally:
            os.environ["PATH"] = old
        return app

    def test_build_puts_the_car_in_and_keeps_the_icns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = self.run_build(Path(tmp), ["NSAppearanceNameAqua", "NSAppearanceNameDarkAqua"])
            plist = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
            self.assertEqual(plist["CFBundleIconName"], "facthorypage")
            self.assertEqual(plist["CFBundleIconFile"], "App")
            self.assertEqual((app / "Contents" / "Resources" / "Assets.car").read_bytes(), b"car")
            self.assertTrue((app / "Contents" / "Resources" / "App.icns").is_file())

    def test_build_fails_when_the_car_lacks_dark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "lacks the dark variant"):
                self.run_build(Path(tmp), ["NSAppearanceNameAqua"])

    def test_build_fails_without_the_pinned_xcode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "Xcode 26.0.1 is not installed"):
                self.run_build(Path(tmp), ["x"], xcode=False)


if __name__ == "__main__":
    unittest.main()
