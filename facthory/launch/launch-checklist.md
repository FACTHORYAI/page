# W7 launch checklist: Facthory Page, Grid and Deck

W7's exit criterion (data plane `docs/11-plan.md`, lane W):
**the three apps are public under Facthory names**, with downloads on facthory.com, the Microsoft
Store listings and a "switch from Microsoft" guide. W7 starts after W0, W2, W4, W6 and W9.

**Who**: **Owner** = Bandpey GmbH's owner or counsel (legal, accounts, money, public statements);
**Claude** = Claude Code sessions (code, builds, verification, drafts). Where both appear, the first
does the work and the second signs off.

**Status, 2026-10-25**: every package so far is merged to `main` in FACTHORYAI/page, grid and deck:
- W2, the brand patch set (#3 in each);
- W3, the upstream sync (#4);
- W4, signed releases and the in-app updater (#5);
- W6, the fidelity corpus and its runner (#6);
- W7 and W9, the listings, guides and this folder (#7).

bandpey-hq/github-infra#25 is merged and applied: the environments `upstream-sync`, `release` and
`github-pages` exist on all three repositories. Next come the sync App (runbook L), the owner's
accounts and signing (runbook M), then a first tagged release per app.

## Gate 1: W0, names cleared

- [ ] **Owner**: clearance search of **Facthory Page**, **Facthory Grid** and **Facthory Deck**
  (EUIPO, DPMA, USPTO; classes 9 and 42) finished, and the result recorded in `docs/14-office-apps.md`
  §14.4: no blocking mark, or a rename decision.
- [ ] **Owner**: **pending opposition against the FACTHORY EU trade mark application, EUTM
  019394527**: counsel's written view on launching under FACTHORY while it is pending (go, wait,
  or fallback), and what changes if the opposition succeeds (product names, domains, store
  listings). Record the decision in §14.4.
- [ ] **Owner**: **Apple's PAGES mark against "Facthory Page"**: counsel's view for the direct
  downloads and the Microsoft Store now, and the fallback for the Mac App Store later (§14.6:
  only that listing changes, for example "Facthory Page – Documents"). Recorded in §14.4.
- [ ] **Owner**: counsel reviews the launch material (§14.5): the three switching guides, the
  downloads copy, the store listings and the announcement, including:
  - the Microsoft trademark statement at the end of each guide;
  - "switching from Microsoft Word / Excel / PowerPoint" in body text, never in a name, title or
    heading;
  - the file-type labels the installers register ("Word Document", "Excel Workbook",
    "PowerPoint Presentation") and Facthory Page's option "Make Facthory Page the default for
    Word documents…": descriptive use, but confirm.
- [ ] **Owner**: the licence agreement with ArtCraft (§14.2) checked for anything it requires
  beyond MIT/Apache-2.0 at launch: credit wording, announcement, use of their name.

## Gate 2: W2, the brand, merged

Per repository (`FACTHORYAI/page`, `grid`, `deck`):

- [x] **Claude**: W2 pull requests merged to `main`; the branded build (`facthory.yml`) green on
  `main` (2026-10-25).
- [ ] **Claude**: `python3 facthory/rebrand.py check` passes on the release binaries of every
  platform (it runs in the release jobs).
- [ ] **Claude**: screenshots of each app on each OS showing the Facthory name and icon, the About
  box with "Based on WordCraft / GridCraft / DeckCraft by the ArtCraft team" and both copyrights,
  and no ArtCraft mark anywhere (Start screen, title bar, Help tab, File view).
- [ ] **Claude**: `LICENSE-MIT`, `LICENSE-APACHE` and `NOTICE` unchanged from upstream;
  `ATTRIBUTION.md` keeps every upstream credit and lists our icons; `docs/brand/` deleted in the
  build.
- [ ] **Claude**: every "Help and feedback" / "Report a problem" link opens the right issue
  tracker; Page's title-bar help button is off by default.
- [ ] **Claude**: no telemetry or crash-reporting endpoint in any build (upstream has none; confirm
  after each upstream merge).
- [ ] **Owner**: the three icons approved.
- [ ] **Claude**, then **Owner**: decide the Flatpak app id. `brand.toml` produces
  `com.facthory.page`, while §14.6 names `com.facthory.Page` for Flathub. Settle it before the first
  public release, because the id is hard to change later (desktop files, settings, Flathub
  verification).

## Gate 3: W4, signed installers verified on each OS

Accounts and secrets:

- [ ] **Owner**: Apple Developer ID Application certificate and notarization credentials for
  Bandpey GmbH in the `release` environment (`bandpey-hq/github-infra`).
- [ ] **Owner**: Windows code-signing credentials for Bandpey GmbH in the same environment.

Release pipeline, per repository:

- [ ] **Claude**: `facthory-release.yml` and `facthory/release.py` finished and merged (Page has a
  WIP version), then ported to Grid and Deck: macOS universal DMG and CLI zip; Windows MSI and
  portable zip for x64 and arm64; Linux AppImage (+ `.zsync`), `.deb`, `.rpm`, `.tar.gz` for
  x86_64 and aarch64; `SHA256SUMS`; `latest.json`.
- [ ] **Claude**, then **Owner**: Flatpak bundle: add it to the release workflow (the plan lists it)
  or drop it from the launch copy. The current drafts say "add only if it ships".
- [ ] **Claude**: release files follow `facthory<app>-<version>-<os>-<arch>.<ext>`, matching
  `downloads.md`; the AppImage update information points at `FACTHORYAI/<app>`.
- [ ] **Claude**: release builds embed the craft-fonts the upstream release uses (`CRAFT_FONTS_DIR`).
  Deck's metric-compatible fonts (Carlito, Caladea, Liberation) and the interface fonts for
  Chinese, Japanese and Arabic depend on it.
- [ ] **Claude**: the in-app updater built (it doesn't exist upstream; W4's exit and W9 both need
  it), reading `latest.json`; the privacy copy updated to mention the update check.

Verified on clean machines, per app (Page, Grid, Deck):

- [ ] **Claude**: **macOS**, Apple silicon and Intel, macOS 11 and the current release: the DMG
  opens without a Gatekeeper block; `spctl --assess` reports a notarized Developer ID; the app
  launches; Finder double-click and Open With open a file; Get Info › Change All works; the CLI zip
  runs; upgrade over the previous version keeps settings.
- [ ] **Claude**: **Windows 10 and 11 x64, Windows 11 ARM64**: MSI signature shows Bandpey GmbH;
  silent install (`msiexec /i … /qn`) and uninstall work (the Store needs silent install); Start
  menu entry; "Open with" lists the app; Page's Options button opens Default apps; Grid shows in
  Default apps; upgrade over the previous version; no upgrade or shared components with an
  installed upstream app; startup on Intel UHD, AMD and software-only graphics.
- [ ] **Claude**: **Linux**: AppImage on Ubuntu 22.04 and 24.04 (X11 and Wayland); `.deb` on
  Debian 12 and Ubuntu; `.rpm` on Fedora; `.tar.gz`; desktop entry, icon and file types
  registered; `xdg-mime` default works; AppImageUpdate fetches the next release.
- [ ] **Claude**: every file's hash matches `SHA256SUMS`.
- [ ] **Owner**: publish the first draft release of each app (the W4 workflow drafts releases for
  a person to publish).

## Gate 4: W6, the pass rate meets the bar

- [ ] **Claude**: a fidelity corpus of real-world `.docx`, `.xlsx` and `.pptx` files with the rights
  to use them (no customer files), with round-trip and rendering tests against Microsoft's output.
- [ ] **Claude**: the pass rate per app published (method, corpus size, date).
- [ ] **Claude** proposes, **Owner** decides: the bar for "ready", per app, and what we call an app
  that misses it. Upstream calls all three **alpha** (Deck "alpha, heading for beta"); the drafts
  say so, and must keep saying so unless W6 shows otherwise.
- [ ] **Claude**: the W6 numbers put into the three guides (the "Draft note" placeholders) and the
  store descriptions.

## Gate 5: W9, Microsoft Store listings live

- [ ] **Owner**: Partner Center account for Bandpey GmbH with business verification (D-U-N-S
  number or a registration document).
- [ ] **Owner**: EU Digital Services Act trader details: company address, a support phone number
  and email (never personal ones).
- [ ] **Owner**: privacy policy URL (facthory.com) for each listing.
- [ ] **Claude**, then **Owner**: IARC age-rating questionnaire (office apps: all ages).
- [ ] **Claude**: listing text for each app: the name always the full "Facthory Page / Grid /
  Deck"; never "Word", "Excel" or "PowerPoint" in the name, subtitle, keywords or icon; the
  description may say that it opens and saves `.docx` / `.xlsx` / `.pptx`; screenshots of our own
  sample files.
- [ ] **Claude**: one submission per app with the signed MSI at its versioned GitHub URL (complete,
  silent, unchanged per submission), "provided and updated by" Bandpey GmbH.
- [ ] **Claude**: each app installs from the Store and updates through our updater.
- [ ] **Claude**: the "Microsoft Store: coming soon" lines in the guides and downloads copy replaced
  with the live Store links.

## Gate 6: website pages published

- [ ] **Owner**: who publishes facthory.com, and where the guides live (the drafts assume
  `facthory.com/page`, `/grid`, `/deck`).
- [ ] **Claude**: `facthory.com/page`, `/grid` and `/deck` live before the first release: the About
  boxes and Linux metadata already link there.
- [ ] **Claude**: the downloads copy (`downloads.md`) built into those pages, buttons filled from
  each release's `latest.json` or the GitHub release, and every link checked.
- [ ] **Claude**: the three guides (`facthory/guide/switching.md` in each repository) published,
  draft notes removed.
- [ ] **Claude**: the link for "Facthory's workspace" in the guides set to the real sign-up or
  product page.
- [ ] **Owner**: privacy policy and legal notice (Impressum) pages live.

## Gate 7: launch announcement

- [ ] **Claude**: the announcement drafted: what the apps are, that they are free and open source,
  that they are based on ArtCraft's apps (credit), what they don't do (no real-time co-authoring),
  the alpha status, links.
- [ ] **Owner**: the announcement approved and the channels chosen; the owner posts, or tells
  Claude to.
- [ ] **Owner**: whether and how to tell ArtCraft before the announcement (§14.5: the owner's call).

## Gate 8: support ready

- [ ] **Owner**: `support@facthory.com` is a working mailbox (the build writes it into the Linux
  packages as the maintainer address) and the DSA support phone number is staffed.
- [ ] **Claude**: issues enabled on the three repositories, with issue templates (bug with
  version, OS and log file; file-fidelity report without confidential files; feature request) and
  labels; none exist today.
- [ ] **Claude**: a routine that triages new issues daily, forwards problems that also occur
  upstream to the upstream project, and answers known questions from the guides' FAQ.
- [ ] **Claude**: a known-issues section per app, kept current from the gap lists.

## Go / no-go

- [ ] **Owner**: every gate above checked, or each open item explicitly accepted, and the launch
  date set.
- [ ] **Claude**: the live Gantt chart updated when W7 starts and when it finishes.
