#!/usr/bin/env python3
"""Merge the next upstream release into this checkout's HEAD.

Upstream ([upstream].repository in facthory/brand.toml) tags each release vX.Y.Z. The next
release is the oldest such tag HEAD does not contain, so releases land one at a time, in order.
The patch set adds files and touches upstream's tree in two known ways, which resolve here:

  [sync].removed   upstream files we removed: a merge that changed them keeps them removed;
  ATTRIBUTION.md   our block under the title: take upstream's file and write the block again
                   (facthory/icons/render.py --attribution).

Any other conflict aborts the merge and is reported, for a person or a Claude session.

  python3 facthory/sync.py next     print the next upstream release tag, or nothing
  python3 facthory/sync.py merge    merge it as a merge commit; exit 2 on a conflict

With $GITHUB_OUTPUT set, it also writes `tag=` and `conflicts=` there.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
ATTRIBUTION = "ATTRIBUTION.md"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=check)


def load() -> dict:
    with (ROOT / "facthory" / "brand.toml").open("rb") as f:
        return tomllib.load(f)


def output(**values: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            for k, v in values.items():
                f.write(f"{k}={v}\n")


def fetch_upstream(url: str) -> None:
    if "upstream" not in git("remote").stdout.split():
        git("remote", "add", "upstream", url)
    # Upstream's tags in their own namespace, so they never mix with ours.
    git("fetch", "--quiet", "--no-tags", "upstream", "+refs/tags/*:refs/upstream-tags/*")


def next_release() -> str | None:
    refs = git("for-each-ref", "--format=%(refname:strip=2)", "refs/upstream-tags").stdout.split()
    for _, tag in sorted((tuple(map(int, m.groups())), t) for t in refs if (m := RELEASE.match(t))):
        if git("merge-base", "--is-ancestor", f"refs/upstream-tags/{tag}", "HEAD", check=False).returncode != 0:
            return tag
    return None


def merge(tag: str, name: str, removed: list[str]) -> list[str]:
    """Merge `tag`; the paths left in conflict, or none when it merged."""
    r = git("merge", "--no-ff", "--no-edit", "-m", f"Merge upstream {name} {tag}", f"refs/upstream-tags/{tag}", check=False)
    if r.returncode == 0:
        return []
    unmerged = sorted(set(git("diff", "--name-only", "--diff-filter=U").stdout.split()))
    rest = [p for p in unmerged if p not in removed and p != ATTRIBUTION]
    if rest or not unmerged:
        git("merge", "--abort", check=False)
        return rest or ["(merge failed: " + r.stderr.strip().splitlines()[-1] + ")"]
    for p in unmerged:
        if p == ATTRIBUTION:
            git("checkout", "--theirs", "--", p)
            subprocess.run([sys.executable, str(ROOT / "facthory" / "icons" / "render.py"), "--attribution"], cwd=ROOT, check=True)
            git("add", "--", p)
        else:
            git("rm", "--quiet", "--", p)
    git("commit", "--quiet", "--no-edit")
    return []


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("next", "merge"):
        print(__doc__, file=sys.stderr)
        return 1
    brand = load()
    fetch_upstream(brand["upstream"]["repository"])
    tag = next_release()
    output(tag=tag or "")
    if not tag:
        print("up to date with upstream's releases")
        return 0
    print(tag)
    if cmd == "next":
        return 0
    conflicts = merge(tag, brand["upstream"]["name"], brand.get("sync", {}).get("removed", []))
    output(conflicts=" ".join(conflicts))
    if conflicts:
        print(f"merging {tag} conflicts in: {', '.join(conflicts)}", file=sys.stderr)
        return 2
    print(f"merged {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
