#!/usr/bin/env python3
"""Widen the newest release's update rollout, a step at a time.

  python3 facthory/rollout.py               the rollout workflow, with GH_TOKEN and GITHUB_REPOSITORY
  python3 facthory/rollout.py --self-test   checks the schedule, offline

The newest published release's update feed (latest.json, facthory/release.py) carries "rollout",
the percentage of copies the update is offered to (facthory/update/facthory_update.rs). The
release workflow publishes a release at 10; this raises it by the release's age:

  from publishing   10
  after a day       25
  after two days    50
  after three days  100

The repository variable FACTHORY_ROLLOUT overrides: "halt" offers the update to no copy until
the variable changes (copies that took it keep it), "full" offers it to every copy at once. The
share never drops otherwise, so a rollout finished early stays finished.
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# (hours since publishing, percentage of copies)
STEPS = [(0, 10), (24, 25), (48, 50), (72, 100)]


def target(hours: float, current: int, mode: str) -> int:
    """The share to offer now: by the schedule, never below what is offered already."""
    if mode == "halt":
        return 0
    if mode == "full":
        return 100
    planned = max(share for after, share in STEPS if hours >= after) if hours >= 0 else STEPS[0][1]
    return max(current, planned)


def self_test() -> None:
    assert target(0, 10, "") == 10
    assert target(23.9, 10, "") == 10
    assert target(24, 10, "") == 25
    assert target(50, 25, "") == 50
    assert target(100, 50, "") == 100
    # Finished early by hand: stays finished.
    assert target(1, 100, "") == 100
    # A halt holds every copy back, and lifting it resumes by the release's age.
    assert target(30, 25, "halt") == 0
    assert target(30, 0, "") == 25
    assert target(5, 10, "full") == 100
    # A clock that puts publishing in the future still starts at the first step.
    assert target(-3, 10, "") == 10
    print("ok: the rollout schedule")


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        return 0
    repo = os.environ["GITHUB_REPOSITORY"]
    mode = os.environ.get("FACTHORY_ROLLOUT", "").strip().lower()
    if mode not in ("", "halt", "full"):
        print(f"::error::FACTHORY_ROLLOUT is {mode!r}; it may be empty, halt or full", file=sys.stderr)
        return 1
    try:
        release = json.loads(gh("release", "view", "--repo", repo, "--json", "tagName,publishedAt"))
    except subprocess.CalledProcessError:
        print("No published release yet: nothing to roll out.")
        return 0
    tag = release["tagName"]
    published = datetime.datetime.fromisoformat(release["publishedAt"].replace("Z", "+00:00"))
    hours = (datetime.datetime.now(datetime.timezone.utc) - published).total_seconds() / 3600
    with tempfile.TemporaryDirectory() as tmp:
        gh("release", "download", tag, "--repo", repo, "--pattern", "latest.json", "--dir", tmp)
        path = Path(tmp) / "latest.json"
        feed = json.loads(path.read_text(encoding="utf-8"))
        current = feed.get("rollout", 100)
        current = current if isinstance(current, int) and 0 <= current <= 100 else 0
        share = target(hours, current, mode)
        summary = f"{tag}, published {hours:.0f} hours ago: offered to {current}% of copies"
        if share == current:
            print(f"{summary}; unchanged.")
            return 0
        feed["rollout"] = share
        path.write_text(json.dumps(feed, indent=2) + "\n", encoding="utf-8")
        gh("release", "upload", tag, str(path), "--repo", repo, "--clobber")
    print(f"{summary}; now {share}%{' (halted by FACTHORY_ROLLOUT)' if mode == 'halt' else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
