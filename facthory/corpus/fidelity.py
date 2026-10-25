#!/usr/bin/env python3
"""Run the fidelity corpus (W6) through this build's command-line tool and report the pass rate.

  python3 facthory/corpus/fidelity.py --cli PATH [--tier smoke|full] [--cache DIR] [--out DIR]
                                      [--reference DIR] [--jobs N] [--timeout SECONDS]

facthory/corpus/corpus.toml lists the files, each pinned by URL and SHA-256 and never committed.
They are fetched into --cache, checked against their pin, kept between runs, and taken through
this app's steps:

  Page (.docx)   open (info), render (PDF), round trip (save as .docx; the text survives)
  Grid (.xlsx)   open, calc (Excel's cached values = our recalculation), round trip (`check`),
                 render (PDF)
  Deck (.pptx)   open (info), render (PDF), round trip (save as .pptx; the outline survives)

A crash (a panic or a signal) or a step over --timeout fails the file. --reference DIR holds
Microsoft's renders as <id>.pdf (facthory/corpus/README.md, reference renders); with it, and
poppler's pdfinfo, the report also compares page counts.

Writes <out>/report.json and <out>/report.md: each file's steps, and the pass rate per step and
overall. A file passes when every step it ran passed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = "facthory-fidelity/1 (+https://github.com/FACTHORYAI)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(entry: dict, cache: Path) -> Path:
    """The file, from the cache or its pinned URL; an error when it doesn't match its pin."""
    path = cache / f"{entry['sha256']}.{Path(entry['url']).suffix.lstrip('.').lower() or 'bin'}"
    if path.exists() and sha256(path) == entry["sha256"]:
        return path
    tmp = path.with_suffix(".part")
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(entry["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r, tmp.open("wb") as f:
                shutil.copyfileobj(r, f)
            got = sha256(tmp)
            if got != entry["sha256"]:
                raise ValueError(f"SHA-256 {got}, pinned {entry['sha256']}")
            os.replace(tmp, path)
            return path
        except Exception as e:  # noqa: BLE001 - reported per file
            last = e
            time.sleep(2 * (attempt + 1))
    tmp.unlink(missing_ok=True)
    raise RuntimeError(f"fetch: {last}")


def run(cmd: list[str], timeout: int) -> tuple[str, subprocess.CompletedProcess | None]:
    """'ok', 'fail', 'crash' or 'timeout', and the finished process."""
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return "timeout", None
    err = p.stderr.decode("utf-8", "replace")
    if p.returncode < 0 or "panicked at" in err:
        return "crash", p
    return ("ok" if p.returncode == 0 else "fail"), p


def why(p: subprocess.CompletedProcess | None) -> str:
    if p is None:
        return "timed out"
    text = (p.stderr or p.stdout).decode("utf-8", "replace").strip().splitlines()
    return (text[-1] if text else f"exit {p.returncode}")[:300]


def words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def pdf_pages(path: Path) -> int | None:
    if not shutil.which("pdfinfo") or not path.exists():
        return None
    p = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", p.stdout, re.M)
    return int(m.group(1)) if m else None


class Steps:
    """One app's steps over one file: each returns (outcome, detail)."""

    def __init__(self, cli: str, app: str, work: Path, timeout: int):
        self.cli, self.app, self.work, self.timeout = cli, app, work, timeout

    def all(self, f: Path, ext: str) -> dict[str, dict]:
        out: dict[str, dict] = {}

        def step(name: str, outcome: str, detail: str = "") -> bool:
            out[name] = {"outcome": outcome, "detail": detail}
            return outcome == "ok"

        pdf = self.work / "ours.pdf"
        if self.app == "grid":
            outcome, p = run([self.cli, "check", str(f), "--json"], self.timeout)
            report = None
            if p is not None and outcome != "crash":
                try:
                    report = json.loads(p.stdout)["files"][0]
                except (ValueError, KeyError, IndexError):
                    report = None
            if report is None:
                step("open", outcome if outcome != "ok" else "fail", why(p))
                return out
            if not step("open", "ok" if report.get("opened") else "fail", str(report.get("error") or "")):
                return out
            calc = report.get("calc", {})
            mismatched = calc.get("mismatched", 0)
            step("calc", "ok" if mismatched == 0 else "fail", f"{calc.get('matched', 0)} of {calc.get('checked', 0)} cells match")
            # Saved and reopened: the package needs no repair, and every category compares equal.
            rt = report.get("roundTrip", {})
            differing = rt.get("differing") or []
            clean = not rt.get("error") and not differing
            step("roundtrip", "ok" if clean else "fail", str(rt.get("error") or "differs: " + ", ".join(map(str, differing))) if not clean else "")
        else:
            outcome, p = run([self.cli, "info", str(f)], self.timeout)
            if not step("open", outcome, "" if outcome == "ok" else why(p)):
                return out
            rt = self.work / f"roundtrip.{ext}"
            outcome, p = run([self.cli, "convert", str(f), str(rt)], self.timeout)
            if step("save", outcome, "" if outcome == "ok" else why(p)):
                same, detail = self.same_text(f, rt)
                step("roundtrip", same, detail)
        outcome, p = run([self.cli, "convert", str(f), str(pdf)], self.timeout)
        detail = "" if outcome == "ok" else why(p)
        if outcome == "ok" and not (pdf.exists() and pdf.stat().st_size > 0):
            outcome, detail = "fail", "no PDF written"
        if step("render", outcome, detail):
            out["render"]["pages"] = pdf_pages(pdf)
        return out

    def same_text(self, a: Path, b: Path) -> tuple[str, str]:
        """Whether the round trip kept the text (Page) or the outline (Deck)."""
        texts = []
        for f in (a, b):
            if self.app == "page":
                outcome, p = run([self.cli, "text", str(f)], self.timeout)
                text = p.stdout.decode("utf-8", "replace") if p is not None else ""
            else:
                md = self.work / f"{f.stem}.md"
                outcome, p = run([self.cli, "convert", str(f), str(md)], self.timeout)
                text = md.read_text(encoding="utf-8", errors="replace") if outcome == "ok" and md.exists() else ""
            if outcome != "ok":
                return outcome, f"{f.name}: {why(p)}"
            texts.append(words(text))
        if texts[0] == texts[1]:
            return "ok", f"{len(texts[0])} words"
        return "fail", f"{len(texts[0])} words before, {len(texts[1])} after"


def one(entry: dict, args, app: str, ext: str) -> dict:
    result = {"id": entry["id"], "features": entry.get("features", []), "steps": {}}
    try:
        f = fetch(entry, args.cache)
    except Exception as e:  # noqa: BLE001 - reported per file
        result["steps"]["fetch"] = {"outcome": "fail", "detail": str(e)[:300]}
        return result
    with tempfile.TemporaryDirectory(prefix=f"fidelity-{entry['id']}-") as work:
        result["steps"] = Steps(args.cli, app, Path(work), args.timeout).all(f, ext)
        render = result["steps"].get("render", {})
        if args.reference and render.get("outcome") == "ok":
            ref = args.reference / f"{entry['id']}.pdf"
            theirs = pdf_pages(ref)
            if theirs is not None:
                ours = render.get("pages")
                result["steps"]["pages"] = {"outcome": "ok" if ours == theirs else "fail", "detail": f"ours {ours}, Microsoft's {theirs}"}
        if args.keep_renders and render.get("outcome") == "ok":
            args.keep_renders.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(work) / "ours.pdf", args.keep_renders / f"{entry['id']}.pdf")
    return result


def passed(r: dict) -> bool:
    return bool(r["steps"]) and all(s["outcome"] == "ok" for s in r["steps"].values())


def report(manifest: dict, results: list[dict], args, seconds: float) -> tuple[dict, str]:
    steps: dict[str, list[int]] = {}
    for r in results:
        for name, s in r["steps"].items():
            ok, total = steps.setdefault(name, [0, 0])
            steps[name] = [ok + (s["outcome"] == "ok"), total + 1]
    crashes = sorted(r["id"] for r in results if any(s["outcome"] == "crash" for s in r["steps"].values()))
    n, good = len(results), sum(passed(r) for r in results)
    data = {
        "schema": "facthory-fidelity/1",
        "app": manifest["app"],
        "tier": args.tier,
        "files": n,
        "passed": good,
        "pass_rate": round(good / n, 4) if n else None,
        "steps": {k: {"passed": v[0], "ran": v[1], "rate": round(v[0] / v[1], 4)} for k, v in steps.items()},
        "crashes": crashes,
        "seconds": round(seconds, 1),
        "results": results,
    }
    pct = lambda a, b: f"{100 * a / b:.1f}%" if b else "n/a"  # noqa: E731
    lines = [
        f"# Fidelity: {manifest['app']}, tier {args.tier}",
        "",
        f"**{good} of {n} files pass every step ({pct(good, n)}).** Crashes: {len(crashes)}."
        + ("" if args.reference else " No reference renders given: page counts not compared."),
        "",
        "| Step | Passed | Ran | Rate |",
        "| ---- | -----: | --: | ---: |",
        *[f"| {k} | {v[0]} | {v[1]} | {pct(v[0], v[1])} |" for k, v in steps.items()],
        "",
    ]
    failures = [(r["id"], name, s) for r in results for name, s in r["steps"].items() if s["outcome"] != "ok"]
    if failures:
        lines += ["## Not passing", "", "| File | Step | Outcome | Detail |", "| ---- | ---- | ------- | ------ |"]
        lines += [f"| `{i}` | {name} | {s['outcome']} | {s.get('detail', '').replace('|', '/')[:200]} |" for i, name, s in failures]
    return data, "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cli", required=True, help="the app's command-line tool, built from the branded tree")
    ap.add_argument("--manifest", type=Path, default=HERE / "corpus.toml")
    ap.add_argument("--tier", choices=["smoke", "full"], default="smoke", help="smoke: the tier-smoke files; full: all")
    ap.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "facthory-corpus")
    ap.add_argument("--out", type=Path, default=Path("fidelity"))
    ap.add_argument("--reference", type=Path, help="Microsoft's renders, <id>.pdf")
    ap.add_argument("--keep-renders", type=Path, help="copy our PDFs here, <id>.pdf")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--timeout", type=int, default=300, help="seconds per step")
    args = ap.parse_args()
    if not shutil.which(args.cli) and not Path(args.cli).exists():
        print(f"error: {args.cli} not found", file=sys.stderr)
        return 2
    with args.manifest.open("rb") as f:
        manifest = tomllib.load(f)
    app, ext = manifest["app"], manifest["format"]
    entries = [e for e in manifest["file"] if args.tier == "full" or e.get("tier") == "smoke"]
    args.cache.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda e: one(e, args, app, ext), entries))
    data, md = report(manifest, results, args, time.monotonic() - started)
    (args.out / "report.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (args.out / "report.md").write_text(md, encoding="utf-8")
    print(md.split("\n\n")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
