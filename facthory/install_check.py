#!/usr/bin/env python3
"""Install a release's files on this machine as a user would, and check what they install.

  python3 facthory/install_check.py <dist> <version> --bin <name> --arch <arch> [--previous <dir>] [--signed]

<dist> holds this platform's build artifacts (the release workflow's); <dir> holds the newest
published release's files for this platform, when there is one, which the new files must
upgrade. <name> is the app's program (facthorypage); its command-line tool is <name>-cli. <arch>
names the build to check: universal (macOS), x64 or arm64 (Windows), x86_64 or aarch64 (Linux). On
each system:

  macOS    the DMG: mounts it, copies the app out, runs it with --version and checks the version
           it declares; unpacks the CLI zip and runs it with --version
  Windows  the MSI for this machine's architecture: installs it for the current account (its
           default), over the previous release's MSI when given, which must leave one installed
           copy of the new version; runs both programs with --version; uninstalls it
  Linux    the AppImage, run with --version; the .deb installed with apt and the .rpm with dnf
           in a Fedora container, each over the previous release's when given

--signed also checks signatures: on macOS the strict code signature and that Gatekeeper accepts
the app as notarized Developer ID; on Windows a valid Authenticode signature by Bandpey GmbH on
the MSI and both programs. Stops at the first failure, saying what failed.
"""

from __future__ import annotations

import argparse
import os
import platform
import plistlib
import shlex
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIGNER = "CN=Bandpey GmbH"
FEDORA = "fedora:44"


class Fail(Exception):
    pass


def run(cmd: list[object], env: dict[str, str] | None = None) -> str:
    """Runs a command and returns its output (stdout, then stderr); a non-zero exit fails."""
    args = [str(c) for c in cmd]
    print("+", shlex.join(args), flush=True)
    r = subprocess.run(args, capture_output=True, text=True, env=env)
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise Fail(f"{Path(args[0]).name} exited with {r.returncode}: {out.strip()[-3000:]}")
    return out


def one(folder: Path, pattern: str) -> Path:
    found = sorted(p for p in folder.rglob(pattern) if p.is_file())
    if len(found) != 1:
        raise Fail(f"expected one {pattern} in {folder}, found {len(found)}: {[p.name for p in found]}")
    return found[0]


def says_version(out: str, version: str, what: str) -> None:
    if version not in out:
        raise Fail(f"{what} --version printed {out.strip()!r}, not {version}")
    print(f"ok: {what} is {version}")


# ---- macOS ---------------------------------------------------------------------------------------


def macos(dist: Path, version: str, name: str, signed: bool) -> None:
    dmg = one(dist, f"*-{version}-macos-universal.dmg")
    work = Path(tempfile.mkdtemp(prefix="install-check-"))
    mount = work / "dmg"
    run(["hdiutil", "attach", "-readonly", "-nobrowse", "-noautoopen", "-mountpoint", mount, dmg])
    try:
        apps = sorted(mount.glob("*.app"))
        if len(apps) != 1:
            raise Fail(f"the DMG holds {len(apps)} apps: {[a.name for a in apps]}")
        app = work / apps[0].name
        run(["ditto", apps[0], app])
    finally:
        run(["hdiutil", "detach", "-force", mount])
    info = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
    if info.get("CFBundleShortVersionString") != version:
        raise Fail(f"{app.name} declares version {info.get('CFBundleShortVersionString')}, not {version}")
    exe = app / "Contents" / "MacOS" / str(info.get("CFBundleExecutable", name))
    says_version(run([exe, "--version"]), version, app.name)
    if signed:
        run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", app])
        assessed = run(["spctl", "--assess", "--type", "execute", "--verbose=4", app])
        if "Notarized Developer ID" not in assessed:
            raise Fail(f"Gatekeeper doesn't accept {app.name} as notarized Developer ID: {assessed.strip()}")
        print(f"ok: {app.name} is signed and notarized")
    cli_zip = one(dist, f"*-cli-{version}-macos-universal.zip")
    run(["ditto", "-x", "-k", cli_zip, work / "cli"])
    cli = one(work / "cli", f"{name}-cli")
    says_version(run([cli, "--version"]), version, cli.name)


# ---- Windows -------------------------------------------------------------------------------------


def msiexec(action: str, msi: Path, log: Path) -> None:
    print(f"+ msiexec {action} {msi.name} /qn", flush=True)
    r = subprocess.run(["msiexec", action, str(msi), "/qn", "/norestart", "/l*v", str(log)])
    # 3010: done, a restart would complete it.
    if r.returncode not in (0, 3010):
        raw = log.read_bytes() if log.exists() else b""
        # Windows Installer writes its log in UTF-16 with a byte-order mark, or in the ANSI code page.
        tail = raw.decode("utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "cp1252", errors="replace")[-4000:]
        raise Fail(f"msiexec {action} {msi.name} exited with {r.returncode}\n{tail}")


def installed(product: str) -> list[tuple[str, str]]:
    """(product code, version) of every installed copy named `product`, for this account or all."""
    import winreg

    found = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            root = winreg.OpenKey(hive, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
        except OSError:
            continue
        with root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                code = winreg.EnumKey(root, i)
                try:
                    with winreg.OpenKey(root, code) as key:
                        if winreg.QueryValueEx(key, "DisplayName")[0] == product:
                            found.append((code, str(winreg.QueryValueEx(key, "DisplayVersion")[0])))
                except OSError:
                    continue
    return found


def install_dir(product: str) -> Path:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\{product}") as key:
            return Path(winreg.QueryValueEx(key, "InstallDir")[0])
    except OSError as e:
        raise Fail(rf"the installer recorded no HKCU\Software\{product}\InstallDir: {e}") from e


def authenticode(path: Path) -> None:
    script = f"$s = Get-AuthenticodeSignature -LiteralPath '{path}'; \"$($s.Status)|$($s.SignerCertificate.Subject)\""
    status, _, subject = run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script]).strip().partition("|")
    if status != "Valid" or SIGNER not in subject:
        raise Fail(f"{path.name}: signature {status}, signer {subject or 'none'}")
    print(f"ok: {path.name} is signed by {subject}")


def windows(dist: Path, version: str, arch: str, name: str, product: str, previous: Path | None, signed: bool) -> None:
    msi = one(dist, f"*-{version}-windows-{arch}.msi")
    work = Path(tempfile.mkdtemp(prefix="install-check-"))
    if installed(product):
        raise Fail(f"{product} is installed already: {installed(product)}")
    if previous is not None:
        old = one(previous, f"*-windows-{arch}.msi")
        msiexec("/i", old, work / "previous.log")
        print(f"ok: installed {old.name}: {installed(product)}")
    msiexec("/i", msi, work / "install.log")
    copies = installed(product)
    if len(copies) != 1 or not copies[0][1].startswith(version):
        raise Fail(f"after installing {msi.name}, the installed copies are {copies}; expected one of {version}")
    folder = install_dir(product)
    for exe in (folder / f"{name}.exe", folder / f"{name}-cli.exe"):
        says_version(run([exe, "--version"]), version, exe.name)
        if signed:
            authenticode(exe)
    if signed:
        authenticode(msi)
    msiexec("/x", msi, work / "uninstall.log")
    if installed(product):
        raise Fail(f"uninstalling left {installed(product)}")
    print(f"ok: {msi.name} installs, upgrades and uninstalls")


# ---- Linux ---------------------------------------------------------------------------------------


def linux(dist: Path, version: str, arch: str, name: str, previous: Path | None) -> None:
    appimage = one(dist, f"*-{version}-linux-{arch}.AppImage")
    appimage.chmod(0o755)
    # No FUSE on a build machine: the AppImage unpacks itself and runs.
    says_version(run([appimage, "--version"], env={**os.environ, "APPIMAGE_EXTRACT_AND_RUN": "1"}), version, appimage.name)

    deb = one(dist, f"*-{version}-linux-{arch}.deb")
    package = run(["dpkg-deb", "--field", deb, "Package"]).strip()
    debs = ([one(previous, f"*-linux-{arch}.deb")] if previous is not None else []) + [deb]
    # The runner image's package lists may be older than the mirrors: a dependency would 404.
    run(["sudo", "apt-get", "update"])
    for d in debs:
        run(["sudo", "apt-get", "install", "-y", "--no-install-recommends", d.resolve()])
    got = run(["dpkg-query", "--show", "--showformat=${Version}", package]).strip()
    if not got.startswith(version):
        raise Fail(f"apt installed {package} {got}, not {version}")
    for exe in (name, f"{name}-cli"):
        says_version(run([exe, "--version"]), version, f"{exe} (.deb)")
    run(["sudo", "apt-get", "remove", "-y", package])

    rpm = one(dist, f"*-{version}-linux-{arch}.rpm")
    mounts = ["-v", f"{rpm.parent.resolve()}:/new:ro"]
    installs = []
    if previous is not None:
        old = one(previous, f"*-linux-{arch}.rpm")
        mounts += ["-v", f"{old.parent.resolve()}:/old:ro"]
        installs.append(f"/old/{old.name}")
    installs.append(f"/new/{rpm.name}")
    script = "\n".join(
        [
            "set -euo pipefail",
            *(f"dnf install -y --setopt=install_weak_deps=False {shlex.quote(p)}" for p in installs),
            f"package=$(rpm -qp --qf '%{{NAME}}' {shlex.quote('/new/' + rpm.name)})",
            "echo \"installed: $(rpm -q --qf '%{VERSION}' \"$package\")\"",
            f"echo \"program: $({name} --version)\"",
            f"echo \"tool: $({name}-cli --version)\"",
        ]
    )
    out = run(["docker", "run", "--rm", *mounts, FEDORA, "bash", "-c", script])
    lines = {k: v for k, _, v in (line.partition(": ") for line in out.splitlines()) if k in ("installed", "program", "tool")}
    if not lines.get("installed", "").startswith(version):
        raise Fail(f"dnf installed {lines.get('installed')}, not {version}: {out.strip()[-2000:]}")
    says_version(lines.get("program", ""), version, f"{name} (.rpm)")
    says_version(lines.get("tool", ""), version, f"{name}-cli (.rpm)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dist", type=Path)
    parser.add_argument("version")
    parser.add_argument("--bin", required=True, help="the app's program, e.g. facthorypage")
    parser.add_argument("--arch", required=True, choices=["universal", "x64", "arm64", "x86_64", "aarch64"])
    parser.add_argument("--previous", type=Path, help="the newest published release's files for this platform")
    parser.add_argument("--signed", action="store_true", help="also check the signatures")
    args = parser.parse_args()
    previous = args.previous if args.previous is not None and any(args.previous.rglob("*")) else None
    with (ROOT / "facthory" / "brand.toml").open("rb") as f:
        product = tomllib.load(f)["brand"]["name"]
    try:
        if sys.platform == "darwin":
            macos(args.dist, args.version, args.bin, args.signed)
        elif sys.platform == "win32":
            windows(args.dist, args.version, args.arch, args.bin, product, previous, args.signed)
        elif sys.platform.startswith("linux"):
            linux(args.dist, args.version, args.arch, args.bin, previous)
        else:
            raise Fail(f"no install check for {sys.platform}")
    except Fail as e:
        print(f"::error::{e}", file=sys.stderr)
        return 1
    print(f"{product} {args.version}: the install check passed on {platform.system()} {platform.machine()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
