# Facthory Page: the Facthory patch set

This repository is a downstream distribution of
[WordCraft](https://github.com/storytold/wordcraft): `main` is WordCraft's history plus the files
listed here, and every WordCraft release is merged into it. Nothing in WordCraft's own files is
edited in the repository; the brand is applied to a fresh checkout when the app is built, so
upstream merges never conflict with it.

## The patch set

Files Facthory adds to upstream's tree, and nothing else:

| Path | What it is |
| ---- | ---------- |
| `facthory/brand.toml` | The brand as data: names, app ids, links, publisher, the exact edits, the installer GUID namespace, the mark check |
| `facthory/rebrand.py` | Applies `brand.toml` to a checkout (`apply`) and checks shipped files for upstream marks (`check`) |
| `facthory/icons/page.svg` | The Facthory Page icon (original artwork) |
| `facthory/icons/render.py` | Renders the icon set (`facthory/icons/app-icon/`, committed) with resvg, and credits it in `ATTRIBUTION.md` |
| `facthory/README.md` | This list |
| `.github/README.md` | The repository's front page |
| `.github/workflows/facthory.yml` | The branded build: apply, upstream's gate on the branded tree, release build, mark check |

And two upstream files changed:

| Path | Change | Why |
| ---- | ------ | --- |
| `.github/dependabot.yml` | Removed | Dependency updates reach us with upstream's releases; our own bump PRs would only diverge from upstream's lockfile |
| `ATTRIBUTION.md` | One block under the title (`<!-- facthory:begin … end -->`), written by `facthory/icons/render.py` | Upstream's `cargo xtask assets` needs a row for every image in the repository, ours included; upstream seldom edits the top of the file, and after a merge that touches it, `render.py --attribution` rewrites the block |

## What the brand changes in a build

`facthory/rebrand.py apply` makes these changes, all declared in `brand.toml`:

- **Name**: WordCraft becomes Facthory Page in the interface, every translation, the CLI, the MCP
  server, file metadata the app writes, the installers and the Linux metadata.
- **Identifiers**: `ai.storyteller.wordcraft` becomes `com.facthory.page` (bundle id, desktop id,
  AppStream id, icon names); crates, binaries and folders `wordcraft*` become `facthorypage*`;
  environment variables `WORDCRAFT_*` become `FACTHORY_PAGE_*`; Windows ProgIDs `FacthoryPage.*`.
- **Publisher**: Bandpey GmbH in the Windows file properties, the MSI and the Linux packages.
- **Windows Installer**: the UpgradeCode and every component GUID derive from our namespace, so
  Facthory Page never upgrades, replaces or shares components with an installed WordCraft.
- **Icons**: our own set replaces upstream's (`facthory/icons/app-icon/`).
- **Links**: website `facthory.com/page`, source `github.com/FACTHORYAI/page`; the community
  (Discord) buttons become "Help and feedback", open our issue tracker, and the title-bar button
  is off by default.
- **Marks removed**: `docs/brand/` (the ArtCraft name, wordmark and logos) is deleted.
- **Credits kept**: the About box says "Based on WordCraft by the ArtCraft team" and keeps
  upstream's copyright next to ours; `LICENSE-*` and `NOTICE` are never touched; `ATTRIBUTION.md`
  keeps every upstream credit and lists our icon as ours.

Telemetry and crash reporting: WordCraft has none, so there is nothing to turn off. Updates:
WordCraft has no built-in updater; ours comes with the signed releases.

## The check

`facthory/rebrand.py check [built files]` fails when an upstream mark (ArtCraft, WordCraft, the
sibling apps, upstream's domains and publisher) is left in the shipped text (`packaging/`,
`assets/`, build scripts) or in the built binaries, outside the credits `brand.toml` allows.
The branded build runs it on the release binaries.

## When upstream changes

Every rule in `brand.toml` states how many matches it expects. When upstream moves or rewords a
string the brand edits, `apply` fails and names the rule; adjust the rule, not upstream's file.
New upstream text that names WordCraft is rebranded by the tokens without a change here; new
marks the tokens miss fail the check.

## Icons

```sh
cargo install resvg
python3 facthory/icons/render.py
```
