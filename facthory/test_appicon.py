#!/usr/bin/env python3
"""Tests of appicon.py that need no macOS: the .icon source, the car checks against listings of the shape
`assetutil --info` prints (a JSON array; `IconImageStack` entries with a `Name` and an `Appearance`, as the Xcode
26.0.1 car of the Page icon lists them: no flattened `Icon Image` bitmaps, which that Xcode writes none of with the
old format off),
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


AQUA, DARK, TINT = "NSAppearanceNameAqua", "NSAppearanceNameDarkAqua", "ISAppearanceTintable"


def listing(*appearances: str, name: str = "facthorypage", flattened: int = 0) -> list[dict]:
    """The entries of the Xcode 26.0.1 car of the Page icon (macos-15 runner, probe run 43617349785 and after), by
    appearance; `flattened` adds the bitmaps Xcode 26.1 and later write regardless."""
    return (
        [{"AssetType": "IconGroup", "Name": f"{name}/Group", "Appearance": a} for a in appearances]
        + [{"AssetType": "IconImageStack", "Name": name, "Appearance": a, "RenditionName": f"{name}.iconstack"} for a in appearances]
        + [{"AssetType": "Icon Image", "Name": name, "PixelWidth": 1024, "Scale": 1} for _ in range(flattened)]
        + [{"AssetType": "Image", "Name": f"{name}_Assets/{name}-layer"}, {"AssetType": "Color", "Name": f"{name}_Assets/Color-1"}]
    )


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
        lines = appicon.check_car_info(listing(DARK, AQUA, TINT), "facthorypage")
        self.assertIn("default: 1 entry", lines)
        self.assertIn("dark: 1 entry", lines)

    def test_the_stack_alone_is_a_complete_icon(self) -> None:
        # What Xcode 26.0.1 writes with the old format off: no flattened bitmaps. The guard used to ask for those
        # and failed a car that holds the whole icon.
        lines = appicon.check_car_info(listing(DARK, AQUA, TINT, flattened=0), "facthorypage")
        self.assertTrue(any(line.startswith("0 flattened bitmap(s)") for line in lines))

    def test_flattened_bitmaps_are_listed_not_required(self) -> None:
        lines = appicon.check_car_info(listing(DARK, AQUA, TINT, flattened=7), "facthorypage")
        self.assertTrue(any(line.startswith("7 flattened bitmap(s)") for line in lines))

    def test_flattened_bitmaps_alone_are_no_icon(self) -> None:
        with self.assertRaisesRegex(appicon.AppIconError, "no icon image stack named 'facthorypage'"):
            appicon.check_car_info(listing(flattened=7), "facthorypage")

    def test_a_car_without_dark_fails_and_shows_what_it_has(self) -> None:
        with self.assertRaisesRegex(appicon.AppIconError, "(?s)lacks the dark variant.*'NSAppearanceNameAqua'"):
            appicon.check_car_info(listing(AQUA), "facthorypage")

    def test_a_car_without_the_default_fails(self) -> None:
        with self.assertRaisesRegex(appicon.AppIconError, "lacks the default variant"):
            appicon.check_car_info(listing(DARK, TINT), "facthorypage")

    def test_a_car_without_the_icon_fails(self) -> None:
        with self.assertRaisesRegex(appicon.AppIconError, "(?s)no icon image stack named 'facthorypage' .*other"):
            appicon.check_car_info(listing(AQUA, DARK, name="other"), "facthorypage")

    def test_an_empty_car_fails_as_the_release_did(self) -> None:
        # Run 43604567145: actool wrote a car, its listing held colours and images, and no icon.
        with self.assertRaisesRegex(appicon.AppIconError, r"icon image stacks: none\)"):
            appicon.check_car_info([{"AssetType": "Color", "Name": "AccentColor"}], "facthorypage")

    def test_tinted_is_listed_not_required(self) -> None:
        lines = appicon.check_car_info(listing(AQUA, DARK, TINT), "facthorypage")
        self.assertIn("tinted: 1 entry listed (made by the system from the layer; not required)", lines)
        lines = appicon.check_car_info(listing(AQUA, DARK), "facthorypage")
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
        # On a macos-15 runner (macOS 15 host) Xcode 26's actool crashes (ibtoold: "The tool closed the connection")
        # without this flag, because the old-format bitmaps need macOS 26's renderer (probe run 43617349785). With it
        # Xcode 26.0.1 warns "Failed to generate flattened icon stack" and writes the stack: that warning is expected.
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
    print(json.dumps([{"AssetType": "IconImageStack", "Name": name, "Appearance": a} for a in %r]))
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
            app = self.run_build(Path(tmp), [AQUA, DARK])
            plist = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
            self.assertEqual(plist["CFBundleIconName"], "facthorypage")
            self.assertEqual(plist["CFBundleIconFile"], "App")
            self.assertEqual((app / "Contents" / "Resources" / "Assets.car").read_bytes(), b"car")
            self.assertTrue((app / "Contents" / "Resources" / "App.icns").is_file())

    def test_build_fails_when_the_car_lacks_dark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "lacks the dark variant"):
                self.run_build(Path(tmp), [AQUA])

    def test_the_stub_builds_into_a_throwaway_bundle_and_keeps_it_on_request(self) -> None:
        import os
        import stat

        with tempfile.TemporaryDirectory() as tmp:
            tmp_ = Path(tmp)
            folder = tmp_ / "Applications"
            (folder / f"Xcode_{appicon.XCODE}.app").mkdir(parents=True)
            bin_ = tmp_ / "bin"
            bin_.mkdir()
            for name, text in (("xcrun", XCRUN % [AQUA, DARK]), ("plutil", PLUTIL)):
                (bin_ / name).write_text(text)
                (bin_ / name).chmod(stat.S_IRWXU)
            old = os.environ["PATH"]
            os.environ["PATH"] = f"{bin_}{os.pathsep}{old}"
            try:
                appicon.stub(ICON, None, None, str(folder))
                keep = tmp_ / "keep"
                appicon.stub(ICON, None, keep, str(folder))
            finally:
                os.environ["PATH"] = old
            plist = plistlib.loads((keep / "Probe.app" / "Contents" / "Info.plist").read_bytes())
            self.assertEqual((plist["CFBundleIconName"], plist["CFBundleIconFile"]), ("facthorypage", "stub"))
            self.assertTrue((keep / "Probe.app" / "Contents" / "Resources" / "Assets.car").is_file())

    def test_build_fails_without_the_pinned_xcode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(appicon.AppIconError, "Xcode 26.0.1 is not installed"):
                self.run_build(Path(tmp), ["x"], xcode=False)


if __name__ == "__main__":
    unittest.main()
