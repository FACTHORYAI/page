# The fidelity corpus (W6)

How faithfully Facthory Page opens, saves and draws real `.docx` files that Word wrote, as a
pass rate per step. Part of the Facthory patch set (`facthory/README.md`).

## The files

`corpus.toml` lists 111 files (12.8 MB), each one pinned by URL (a commit or a fixed
public-sector address) and SHA-256. **None is committed**: upstream's rule ("never commit files
produced by Word") holds, and the runner fetches them into a cache and checks them against
their pin.

- **Microsoft-made:** each file was written by Word, checked by `docProps/app.xml` and by
  traces only Office writes (`scan.py`).
- **Licences:** MIT 71, Apache-2.0 32, BSD-2-Clause 4, US federal government work, not subject to copyright in the US (17 U.S.C. 105) 1, dl-de/by-2-0 (Datenlizenz Deutschland Namensnennung 2.0) 1, Licence Ouverte / Open Licence (Etalab) 1, Open Government Licence v3.0 1. Each entry records its licence and where it was read.
- **Tiers:** `smoke` (20 small, feature-dense files whose renders may be published) and
  `full` (all).
- **Review:** `publish_renders = "review"` (13 files: user attachments, logos, names) need a
  content check before even our renders of them are shown publicly.
- **Mirrors:** public-sector entries marked `mirror = "required"` change at their origin; a copy
  belongs in our own bucket once it exists.

## Running it

```sh
python3 facthory/rebrand.py apply      # on a fresh checkout
cargo build --release -p facthorypage-cli
python3 facthory/corpus/fidelity.py --cli target/release/facthorypage-cli --tier smoke
```

`.github/workflows/facthory-fidelity.yml` runs it weekly over every file, by hand over a tier,
and on pull requests that change the corpus over the smoke tier. The pass rates are the job's
summary; `report.json` and `report.md` are its artifact.

| Step | Passes when |
| ---- | ----------- |
| open | `info`: the document opens |
| save | `convert` to `.docx` |
| roundtrip | the saved file opens and its text (`text`, word by word) is the original's |
| render | `convert` to PDF |
| pages | with `--reference`: our PDF has as many pages as Word's |

A crash (a panic or a signal) or a step over the time limit fails the file. A file passes when
every step it ran passed. A step with nothing to check (a presentation without slides has
nothing to render) is skipped and counts neither way.

## Microsoft's renders

Comparing with Word's own output needs Word. A person with a Microsoft 365 licence
exports each file on one fixed Windows machine: black-box, open, export, close, never looking
inside Office. The environment is held constant and recorded per run:
- the default printer (Microsoft Print to PDF) and its resolution;
- the Office build, with updates paused;
- the fonts, by hash;
- the proofing languages and regional format.

The exports go to a private bucket, never into git. `fidelity.py --reference DIR`, with
`DIR/<id>.pdf`, then compares page counts. `cargo xtask visual-diff ref.pdf ours.pdf out --private` (upstream's) compares page by page: SSIM, lines with the same break, the first line of each page. Reports publish our renders and the
scores; Word's pages and diff overlays stay private.

## The bar for "ready" (proposed; the owner sets it after the first full run)

- **Open and round trip:** at least 98% of files open and round-trip, none crashes, and Word opens our save without offering a repair.
- **Render:** at least 80% of files with Word's page count, and at least 90% of lines breaking at the same word (`cargo xtask visual-diff`).

## Adding files

Run `scan.py` (`python3 -I facthory/corpus/scan.py DIR > files.jsonl`) to see each candidate's
producer, Office traces, SHA-256 and features. Add an entry only for a file Word wrote, under
a licence that allows keeping and showing it. Pin a commit or a stable URL.

Thin spots a commissioned set, made in Microsoft 365 and released by Bandpey under CC0, would
fill: right-to-left and CJK content, Aptos and the 2023 theme, embedded fonts, large documents.
