#!/usr/bin/env python3
"""Apply the Facthory brand to this checkout of upstream, in place.

The repository keeps upstream's tree as upstream wrote it, so every upstream release merges
without conflicts; our builds run this first, on a fresh checkout. What changes is data, in
facthory/brand.toml, applied in this order:

  [[rule]] (phase "before")  exact edits in named files. Each says how many matches it expects,
                             so when upstream moves a string the build fails here instead of
                             shipping a mark.
  [[token]]                  ordered replacements over every text file. Tokens with
                             credits = true also apply to the credit files ([files].credits:
                             licences, NOTICE, ATTRIBUTION.md), which otherwise keep upstream's
                             copyright and credits as written. Phrases in [files].keep are left
                             as they are: names fixed inside binary fixtures (a test font's family
                             name) that the text naming them must keep matching.
  [guids]                    every GUID in these files becomes one derived from the brand's app
                             id, so our installers never share an UpgradeCode or a component
                             with upstream's.
  renames                    paths whose names hold a token are renamed by the same tokens.
  [[rule]] (phase "after")   edits on the renamed tree, after the tokens (credits that must keep
                             upstream's name).
  [[copy]]                   brand files (icons) replace upstream's.
  [files].delete             upstream-only files (the ArtCraft marks) are removed.

The interface catalogs are not in the tree: the build checks out craft-i18n beside it ([i18n].dir,
at the commit craft-i18n.rev names), and the steps above brand the tables the build embeds
([i18n].tables) as part of the tree. Rules with `i18n = true` edit those tables and are skipped in a
build without the checkout, which is English only.

Then cargo puts Cargo.lock back in its own order (renamed packages sort elsewhere; the packages,
versions and checksums stay the same), so a later `git diff Cargo.lock` stays empty, and
`git add -A` records the result, so tools that read the index see the branded tree.

  python3 facthory/rebrand.py apply             brand the tree (once; a stamp file guards it)
  python3 facthory/rebrand.py check [FILE ...]  fail on an upstream mark in the shipped text
                                                ([check].paths) or in built files (binaries,
                                                packages), outside the allowed credits
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tomllib
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "facthory" / "brand.toml"
STAMP = ROOT / ".facthory-branded"
GUID = re.compile(r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b")


class BrandError(Exception):
    pass


def load() -> dict:
    with BRAND.open("rb") as f:
        return tomllib.load(f)


def matches(path: str, patterns: list[str] | str) -> bool:
    if isinstance(patterns, str):
        patterns = [patterns]
    return any(fnmatch.fnmatchcase(path, p) or path == p.rstrip("/") or path.startswith(p.rstrip("/") + "/") for p in patterns)


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def read_text(path: Path) -> str | None:
    """The file's text, or None for a binary or non-UTF-8 file (never rewritten)."""
    try:
        data = path.read_bytes()
    except (FileNotFoundError, IsADirectoryError):
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def write_text(path: Path, text: str) -> None:
    # newline="" keeps upstream's line endings (CRLF in some Windows files) as they are.
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(text)


def apply_rules(brand: dict, files: list[str], phase: str) -> None:
    for i, rule in enumerate(brand.get("rule", [])):
        if rule.get("phase", "before") != phase:
            continue
        label = rule.get("why") or f"rule {i + 1}"
        targets = [p for p in files if matches(p, rule["files"])]
        if not targets and rule.get("i18n") and not i18n_files(brand):
            # A rule on the interface catalogs, in a build without them (English only).
            continue
        if not targets:
            raise BrandError(f"{label}: no file matches {rule['files']!r}")
        found = 0
        for p in targets:
            path = ROOT / p
            text = read_text(path)
            if text is None:
                continue
            # A Windows checkout has CRLF line ends: rules match on LF and the file keeps its ends.
            crlf = "\r\n" in text and text.count("\r\n") == text.count("\n")
            if crlf:
                text = text.replace("\r\n", "\n")
            if rule.get("kind") == "tsv":
                text, n = tsv_row(text, rule["key"], rule["new_key"], rule.get("translation"))
            elif rule.get("regex"):
                text, n = re.subn(rule["find"], rule["replace"], text, flags=re.MULTILINE)
            else:
                n = text.count(rule["find"])
                text = text.replace(rule["find"], rule["replace"])
            if n:
                write_text(path, text.replace("\n", "\r\n") if crlf else text)
                found += n
        want = rule.get("count")
        if want is None and found == 0:
            raise BrandError(f"{label}: {rule.get('find', rule.get('key'))!r} not found in {rule['files']!r}; upstream moved it")
        if want is not None and found != want:
            raise BrandError(f"{label}: expected {want} match(es) of {rule.get('find', rule.get('key'))!r} in {rule['files']!r}, found {found}; upstream changed it")


def tsv_row(text: str, key: str, new_key: str, translation: str | None) -> tuple[str, int]:
    """Replace the catalog row whose English source is `key`: the new source, and the given
    translation (the new English when None, so the interface shows English until translated)."""
    out, n = [], 0
    for line in text.split("\n"):
        cols = line.split("\t")
        if len(cols) >= 3 and not line.startswith("#") and cols[1] == key:
            cols = [cols[0], new_key, new_key if translation is None else translation] + cols[3:]
            n += 1
        out.append("\t".join(cols))
    return "\n".join(out), n


def apply_tokens(brand: dict, files: list[str]) -> None:
    tokens = brand.get("token", [])
    credits = brand.get("files", {}).get("credits", [])
    skip = brand.get("files", {}).get("skip", [])
    keep = brand.get("files", {}).get("keep", [])
    for p in files:
        if matches(p, skip):
            continue
        path = ROOT / p
        text = read_text(path)
        if text is None:
            continue
        is_credit = matches(p, credits)
        new = text
        # Kept phrases sit behind placeholders no token can match while the tokens run.
        for i, k in enumerate(keep):
            new = new.replace(k, f"\0keep{i}\0")
        for t in tokens:
            if is_credit and not t.get("credits", False):
                continue
            new = new.replace(t["from"], t["to"])
        for i, k in enumerate(keep):
            new = new.replace(f"\0keep{i}\0", k)
        if new != text:
            write_text(path, new)


def apply_guids(brand: dict, files: list[str]) -> None:
    conf = brand.get("guids")
    if not conf:
        return
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, conf["namespace"])
    for p in files:
        if not matches(p, conf["files"]):
            continue
        path = ROOT / p
        text = read_text(path)
        if text is None:
            continue

        def derive(m: re.Match) -> str:
            # Stable: the same upstream GUID always maps to the same one of ours, in its case.
            new = str(uuid.uuid5(namespace, m.group(0).upper()))
            return new.upper() if m.group(0) == m.group(0).upper() else new

        text, n = GUID.subn(derive, text)
        if n:
            write_text(path, text)


def renamed(path: str, tokens: list[dict]) -> str:
    for t in tokens:
        path = path.replace(t["from"], t["to"])
    return path


def apply_renames(brand: dict, files: list[str]) -> list[str]:
    tokens = brand.get("token", [])
    skip = brand.get("files", {}).get("skip", [])
    result = []
    for p in files:
        new = p if matches(p, skip) else renamed(p, tokens)
        if new != p and (ROOT / p).exists():
            if " " in new:
                raise BrandError(f"renaming {p} would put a space in a path: {new}")
            (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
            os.replace(ROOT / p, ROOT / new)
            remove_empty_dirs((ROOT / p).parent)
        result.append(new)
    return result


def remove_empty_dirs(d: Path) -> None:
    while d != ROOT and d.is_dir() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent


def apply_copies(brand: dict) -> None:
    for c in brand.get("copy", []):
        src, dst = ROOT / "facthory" / c["from"], ROOT / c["to"]
        if not src.exists():
            raise BrandError(f"copy: facthory/{c['from']} is missing")
        if src.is_dir():
            if c.get("replace", False) and dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


def apply_deletes(brand: dict) -> None:
    for p in brand.get("files", {}).get("delete", []):
        path = ROOT / p
        if not path.exists():
            raise BrandError(f"delete: {p} is gone; upstream moved it, check where the marks went")
        shutil.rmtree(path) if path.is_dir() else path.unlink()


def i18n_files(brand: dict) -> list[str]:
    """The interface catalogs the build embeds, from the craft-i18n checkout ([i18n].dir) the
    build made beside the tree; none when there is no checkout (an English-only build)."""
    conf = brand.get("i18n")
    if not conf or not (ROOT / conf["dir"]).is_dir():
        return []
    locales = ROOT / conf["dir"] / "locales"
    return sorted(p.relative_to(ROOT).as_posix() for t in conf["tables"] for p in locales.glob(f"*/{t}"))


def apply() -> None:
    if STAMP.exists():
        raise BrandError(f"this tree is already branded ({STAMP.name} exists); start from a fresh checkout")
    brand = load()
    files = [p for p in tracked() if not p.startswith("facthory/")] + i18n_files(brand)
    apply_rules(brand, files, "before")
    apply_tokens(brand, files)
    apply_guids(brand, files)
    files = apply_renames(brand, files)
    apply_rules(brand, files, "after")
    apply_copies(brand)
    apply_deletes(brand)
    if (ROOT / "Cargo.lock").exists():
        if not shutil.which("cargo"):
            raise BrandError("cargo is needed to put the renamed Cargo.lock back in order")
        subprocess.run(["cargo", "metadata", "--format-version", "1"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    STAMP.write_text(f"{brand['brand']['name']}\n", encoding="utf-8")
    if (ROOT / ".git").exists():
        # The craft-i18n checkout is a repository of its own, not part of this tree's index.
        outside = [f":(exclude){brand['i18n']['dir']}"] if brand.get("i18n") else []
        subprocess.run(["git", "add", "-A", "--", ".", *outside], cwd=ROOT, check=True)
    print(f"branded as {brand['brand']['name']}")


def strip_allowed(text: str, allow: list[str]) -> str:
    for a in sorted(allow, key=len, reverse=True):
        text = text.replace(a, "")
    return text


def scan(name: str, text: str, forbid: list[str], allow: list[str]) -> list[str]:
    text = strip_allowed(text, allow)
    lower = text.lower()
    hits = []
    for f in forbid:
        start = 0
        while (i := lower.find(f.lower(), start)) >= 0:
            context = text[max(0, i - 40) : i + len(f) + 40].replace("\n", " ")
            hits.append(f"{name}: {f!r} in …{context}…")
            start = i + len(f)
    return hits


def check(built: list[str]) -> None:
    brand = load()
    conf = brand["check"]
    forbid, allow = conf["forbid"], conf.get("allow", [])
    hits: list[str] = []
    for p in tracked():
        if not matches(p, conf["paths"]) or matches(p, conf.get("exclude", [])):
            continue
        text = read_text(ROOT / p)
        if text is not None:
            hits += scan(p, text, forbid, allow)
    for b in built:
        data = Path(b).read_bytes()
        # Binaries hold UTF-8 string literals; latin-1 maps every byte, so offsets stay exact.
        hits += scan(b, data.decode("latin-1"), forbid, [a.encode("utf-8").decode("latin-1") for a in allow])
    if hits:
        for h in hits[:200]:
            print(h)
        raise BrandError(f"{len(hits)} upstream mark(s) left in shipped files")
    print(f"no upstream mark in {len(built)} built file(s) and the shipped sources")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("apply", help="brand this checkout in place")
    c = sub.add_parser("check", help="scan shipped sources and built files for upstream marks")
    c.add_argument("built", nargs="*", help="built files to scan (binaries, packages)")
    args = parser.parse_args()
    try:
        apply() if args.cmd == "apply" else check(args.built)
    except BrandError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
