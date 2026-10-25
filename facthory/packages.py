#!/usr/bin/env python3
"""Build the Linux package repositories of our releases: a signed apt repository and a dnf one.

  python3 facthory/packages.py <packages> <site> <owner/repo>

<packages> holds the .deb and .rpm files of the releases to serve (the workflow downloads the
newest published ones). Writes <site>, which GitHub Pages serves at
https://<owner>.github.io/<repo>/:

  apt/          a flat apt repository: the .deb files, Packages, Release, InRelease, Release.gpg
  rpm/          a dnf repository: the .rpm files and repodata/, with repomd.xml signed
  <name>.repo   the dnf source file
  key.asc       the public key both are signed with
  index.html    how to add the repository

Signs with the gpg key already imported (the workflow imports PACKAGES_GPG_KEY). Needs
apt-ftparchive (apt-utils), createrepo_c and gpg.
"""

from __future__ import annotations

import html
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*cmd: str, cwd: Path | None = None, out: Path | None = None) -> None:
    if out is None:
        subprocess.run(cmd, cwd=cwd, check=True)
    else:
        with out.open("wb") as f:
            subprocess.run(cmd, cwd=cwd, check=True, stdout=f)


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    packages, site, repo = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    with (ROOT / "facthory" / "brand.toml").open("rb") as f:
        config = tomllib.load(f)
    brand = config["brand"]
    # The package's name is the binary's (upstream's nfpm.yaml, renamed by the tokens).
    name, app_id, package = brand["name"], brand["app_id"], config["icon"]["base"]
    owner, _, project = repo.partition("/")
    base = f"https://{owner.lower()}.github.io/{project}"
    debs = sorted(packages.rglob("*.deb"))
    rpms = sorted(packages.rglob("*.rpm"))
    if not debs and not rpms:
        print(f"error: no .deb or .rpm under {packages}", file=sys.stderr)
        return 1
    if site.exists():
        shutil.rmtree(site)
    apt, rpm = site / "apt", site / "rpm"
    apt.mkdir(parents=True)
    rpm.mkdir(parents=True)

    # apt: a flat repository ("deb … ./"), signed inline (InRelease) and detached (Release.gpg).
    for d in debs:
        shutil.copyfile(d, apt / d.name)
    run("apt-ftparchive", "packages", ".", cwd=apt, out=apt / "Packages")
    run("gzip", "-9", "-k", "Packages", cwd=apt)
    run(
        "apt-ftparchive",
        "-o", f"APT::FTPArchive::Release::Origin={brand['publisher']}",
        "-o", f"APT::FTPArchive::Release::Label={name}",
        "-o", "APT::FTPArchive::Release::Suite=stable",
        "release", ".", cwd=apt, out=apt / "Release",
    )
    run("gpg", "--batch", "--yes", "--clearsign", "-o", "InRelease", "Release", cwd=apt)
    run("gpg", "--batch", "--yes", "--armor", "--detach-sign", "-o", "Release.gpg", "Release", cwd=apt)

    # dnf: the metadata is signed, and it carries every package's checksum.
    for r in rpms:
        shutil.copyfile(r, rpm / r.name)
    run("createrepo_c", "--quiet", ".", cwd=rpm)
    run("gpg", "--batch", "--yes", "--armor", "--detach-sign", "-o", "repodata/repomd.xml.asc", "repodata/repomd.xml", cwd=rpm)

    run("gpg", "--armor", "--export", out=site / "key.asc")
    slug = project.lower()
    (site / f"facthory-{slug}.repo").write_text(
        f"[facthory-{slug}]\nname={name}\nbaseurl={base}/rpm\nenabled=1\n"
        f"repo_gpgcheck=1\ngpgcheck=0\ngpgkey={base}/key.asc\n",
        encoding="utf-8",
    )
    keyring = f"/usr/share/keyrings/facthory-{slug}.gpg"
    apt_lines = (
        f"curl -fsSL {base}/key.asc | sudo gpg --dearmor -o {keyring}\n"
        f'echo "deb [signed-by={keyring}] {base}/apt ./" | sudo tee /etc/apt/sources.list.d/facthory-{slug}.list\n'
        f"sudo apt update && sudo apt install {package}"
    )
    dnf_lines = f"sudo curl -fsSL -o /etc/yum.repos.d/facthory-{slug}.repo {base}/facthory-{slug}.repo\nsudo dnf install {package}"
    files = "".join(f"<li><code>{html.escape(p.name)}</code></li>" for p in [*debs, *rpms])
    (site / "index.html").write_text(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(name)} for Linux</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#1E2A38;background:#F4F1EA}}
pre{{background:#fff;padding:1rem;overflow-x:auto;border-radius:6px}}code{{font-size:.9em}}</style></head>
<body><h1>{html.escape(name)} for Linux</h1>
<p>Install {html.escape(name)} from these repositories and your system's updates keep it current.
The repositories are signed with <a href="key.asc">this key</a>. Other downloads, including the
AppImage, are on the <a href="https://github.com/{html.escape(repo)}/releases/latest">release page</a>.</p>
<h2>Debian, Ubuntu and derivatives</h2><pre>{html.escape(apt_lines)}</pre>
<h2>Fedora, RHEL and derivatives</h2><pre>{html.escape(dnf_lines)}</pre>
<h2>Packages here</h2><ul>{files}</ul>
<p><small>{html.escape(app_id)} · {html.escape(brand['publisher'])}</small></p>
</body></html>
""",
        encoding="utf-8",
    )
    print(f"{len(debs)} .deb and {len(rpms)} .rpm files in {site}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
