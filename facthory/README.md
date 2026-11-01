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
| `facthory/icons/page.svg` | The Facthory Page icon: with icons' `notepad-text` in its Chrome style (MIT, `LICENSE-withicons.txt`), recoloured |
| `facthory/icons/page-macos.svg` | The same icon on a light tile, for the macOS files (macOS frames an icon without a tile) |
| `facthory/icons/LICENSE-withicons.txt` | The icon's MIT licence; `render.py` copies its text into `ATTRIBUTION.md`, which the packages ship |
| `facthory/icons/render.py` | Renders the icon set (`facthory/icons/app-icon/`, committed) with resvg, and credits it in `ATTRIBUTION.md` |
| `facthory/sync.py` | Merges the next upstream release (W3), resolving the two known conflicts below |
| `facthory/README.md` | This list |
| `facthory/.gitignore` | Keeps Python's bytecode out of the repository |
| `.github/README.md` | The repository's front page |
| `.github/workflows/facthory.yml` | The branded build: apply, upstream's gate on the branded tree, release build, mark check |
| `.github/workflows/upstream-sync.yml` | Every three hours: merge the next upstream release on `sync/<tag>`, open its pull request, merge it when the branded build passes |
| `.github/workflows/facthory-release.yml` | Releases with no person: on `main`, a version without a release builds, signs, install-checks and publishes `v<version>` |
| `facthory/release.py` | Collects a release's files and writes `SHA256SUMS`, the update feed `latest.json` (with its rollout) and the notes |
| `facthory/install_check.py` | Installs a release's files on macOS, Windows or Linux as a user would, over the newest release's, and checks versions and signatures |
| `.github/workflows/facthory-rollout.yml` | Halts a release's staged rollout (marks it a pre-release, so the one before is the latest again) or resumes it, by hand |
| `facthory/packages.py` | Builds the apt and dnf repositories from the newest releases' `.deb` and `.rpm` files, signed |
| `.github/workflows/facthory-packages.yml` | Publishes those repositories on GitHub Pages: called by the release, or when a person publishes one |
| `facthory/dmg/background.svg` | The disk image window, from upstream's, in our colours and with our name |
| `facthory/update/facthory_update.rs` | The updater, copied into the app at build time (see Updates) |
| `facthory/update/updates_ui.rs` | Replaces upstream's update window (`crates/ui-egui/src/updates_ui.rs`): Help's Check for Updates opens our latest release; upstream's updater is left out (see Updates) |
| `.github/workflows/facthory-fidelity.yml` | The fidelity corpus run: weekly, by hand, and on corpus changes; pass rates as the job summary |
| `facthory/corpus/` | The fidelity corpus (W6): `corpus.toml` (real Office files, pinned, never committed), `fidelity.py` (the runner), `scan.py` (checks a candidate file), and its README |
| `facthory/store/listing.md` | The Microsoft Store listing (W9): every field ready to paste, with what must happen before it is submitted |
| `facthory/guide/switching.md` | The switching guide (W7): install, open your files, what is the same, what is missing |
| `facthory/launch/` | Launch material for all three apps: the launch and Store checklists, the privacy policy, the age rating, the MSI requirements, the downloads copy |

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
WordCraft has its own updater (craft-update), which checks and installs upstream's releases by
upstream's repositories and ids; our builds leave it out, and ours reads the update feed of our
releases (see Updates).

## Releases

No person takes part. Every push to `main` runs `.github/workflows/facthory-release.yml`: when
the version in `Cargo.toml` (normally upstream's release the sync just merged) has no release
yet and is newer than the newest one, the run is a release. Each platform brands a fresh checkout
and runs upstream's packaging scripts, which sign with the secrets of the environment `release`
(`bandpey-hq/github-infra`, which only `main` may use and no person approves):

| Platform | Files | Signing |
| -------- | ----- | ------- |
| macOS | `facthorypage-<v>-macos-universal.dmg`, CLI zip | Developer ID, notarized and stapled |
| Windows | `facthorypage-<v>-windows-x64.msi` and `-arm64.msi`, portable zips | Authenticode |
| Linux | AppImage (with `.zsync`), `.deb`, `.rpm`, `.tar.gz`; x86_64 and aarch64 | SHA-256 sums |

Then `facthory/install_check.py` installs each platform's files on a machine of that platform,
as a user would: the DMG's app and the CLI on macOS; the MSI for each architecture on Windows,
over the newest release's MSI, which it must upgrade into one installed copy, then uninstalled;
the AppImage, and the `.deb` and `.rpm` (over the newest release's) on Linux. Each program must
report the new version, and a release's signatures must hold (Developer ID and notarization on
macOS, Authenticode by Bandpey GmbH on Windows). Only when every platform passes does the run
publish the GitHub release `v<version>`, which also creates the tag (only this workflow may), with
`SHA256SUMS` and `latest.json`, then call `facthory-packages.yml`. A version older than the newest
release, or one that is not `major.minor.patch`, is never released.

A pull request that touches the release or the packaging builds and install-checks everything
unsigned, as does a manual run, which signs on `main` when asked (`sign`); both keep the files as
workflow artifacts.

`latest.json`, at `releases/latest/download/latest.json`, is the update feed: the version, when
it was published, the rollout and, per platform, the file the app updates itself from with its
size and SHA-256. The rollout is a schedule written once, since a release can't change after it
is published: 10% of copies at first, 25% after a day, 50% after two and every copy after three.
The apps work out the share from the release's age. `facthory-rollout.yml` stops a rollout by hand
(`halt` marks the release a pre-release, so the release before it is the latest again and its feed
offers no update; copies that took it keep it) and `resume` restores it. The `.deb` and `.rpm`
repositories carry the new version at once, since the system's package manager updates those.

Publishing a release also runs `.github/workflows/facthory-packages.yml`: the `.deb` and `.rpm`
files of the two newest releases become a signed apt repository and a dnf repository on this
repository's GitHub Pages site, `https://facthoryai.github.io/page/`, whose front page says how
to add them. Installs from there update with the system.

## Updates

`facthory/update/facthory_update.rs` is copied into the app when the brand is applied, and
`main.rs` gets four calls to it (`brand.toml`): start, the notice, and the install as the app
quits. Once a day it reads `latest.json`. When that names a newer version and the rollout has
reached this copy (each copy draws a lasting bucket, 0 to 99, kept as `bucket` in `update.json`,
and takes the update once the feed's rollout exceeds it), it downloads this
platform's file in the background and checks its size and SHA-256 against the feed. On macOS
and Windows it also checks that the system accepts the file's signature and that the signer is
the one who signed the running app. A notice then says the update installs when the app quits,
with "Restart now":

| Copy | How it updates |
| ---- | -------------- |
| macOS app in a writable folder | The new bundle takes the old one's place after the app quits |
| Windows, installed with the MSI | The MSI upgrades it after the app quits: a copy for the current account (the installer's default) without asking, one for everyone with the administrator prompt |
| Linux AppImage in a writable folder | The new AppImage takes the old one's name |
| `.deb`, `.rpm` | The system's updates, from our repositories; the notice says so |
| Portable zips, tarballs, unsigned builds | A notice with a link to the release |

Downloads use the system's `curl`, so the app carries no TLS stack. Only builds made by the
release workflow (`FACTHORY_UPDATE_FEED`) check. Updates are off in runs without preferences,
with `FACTHORY_UPDATES=off` in the environment, or with `{"enabled": false}` in `update.json` in
the settings folder; "Skip this version" is kept there too.

## The check

`facthory/rebrand.py check [built files]` fails when an upstream mark (ArtCraft, WordCraft, the
sibling apps, upstream's domains and publisher) is left in the shipped text (`packaging/`,
`assets/`, build scripts) or in the built binaries, outside the credits `brand.toml` allows.
The branded build runs it on the release binaries.

## Upstream sync

`.github/workflows/upstream-sync.yml` runs as the GitHub App **facthory-office-sync**
(bandpey-hq/github-infra, `apps/office-sync.json`), because upstream's releases change its own
workflows and the Actions token may not push those. Its key is a secret of the environment
`upstream-sync`, which only `main` may use; until the App exists, the workflow does nothing.

1. Every three hours, `facthory/sync.py merge` takes the oldest upstream release `main` lacks
   and merges it on `sync/<tag>`. A change upstream made to a file we removed keeps it removed;
   a conflict in `ATTRIBUTION.md` takes upstream's file and writes our block again. Any other
   conflict opens an issue and stops there.
2. The App opens the pull request; the checks run on it as on any other.
3. When the Facthory Page build passes on exactly that commit, the workflow merges it. When it
   fails, it says so on the pull request: usually a rule in `brand.toml` that upstream's change
   no longer matches. Fix the rule on the branch; the merge follows the green build.

One sync pull request is open at a time, so releases land in order.

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
