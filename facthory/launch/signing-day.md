# Signing day: the first signed releases of Facthory Page, Grid and Deck (W4)

W4's exit criterion (data plane `docs/11-plan.md`, lane W): **signed installers of the three apps
install and update cleanly on macOS, Windows and Linux.** The pipeline is built and merged
(`facthory-release.yml`, `facthory/release.py`, the updater, `facthory-packages.yml`; #5 in each
repository). What is missing is the owner's identities: Apple (R3) and Microsoft (R4), planned by
6 November 2026. This file is the order of work for the day each lands, so nothing waits on
Claude. The owner's account steps themselves are runbook M in `bandpey-hq/github-infra`
(`docs/browser-runbook.md`); this file does not repeat them.

**Status, 2026-10-30.**

- The last unsigned build of every release job was green on the pull requests of 25 October:
  macOS universal, Windows x64 and arm64, Linux x86_64 and aarch64, in all three repositories.
- Public repositories run on GitHub-hosted runners at no cost, so Windows and macOS builds don't
  wait for the organization's Actions minutes: page's scheduled Windows ARM64 build of 30 October
  (run 41058215053) billed 0 ms.
- Built on a Mac (M4 Max, macOS 27.0.1, Xcode 27.2), from a branded checkout, as the release job
  builds, ad-hoc signed: see [Local macOS builds](#local-macos-builds).
- Windows (R4), 2026-10-31: the Artifact Signing account `bandpey-signing` exists and Bandpey's
  identity validation is In Progress at Microsoft (1–20 business days); the certificate profile
  `bandpey-public` follows once it is Completed. Windows signs through GitHub's OIDC token, so no
  client secret exists (`facthory-release.yml`, and a brand rule on upstream's `sign.ps1`).
- In each repository's environment `release`: **0 of the 12 secrets set**. GitHub Pages is not
  enabled, release immutability is off, and no release exists yet.

## The secrets

Twelve, in Secret Manager (`signing/office-release.json` in github-infra), copied by
`scripts/release-secrets.sh copy` into the environment `release` of page, grid and deck. Only
`main` deploys from it, and no job waits for a person (the owner chose full automation on
1 November 2026): the macOS and Windows jobs of `facthory-release.yml` in a release or a signed
manual run (the Linux, install-check and publish jobs use no environment), and
`facthory-packages.yml`.

| Secret | What it is | From | Read by |
| ------ | ---------- | ---- | ------- |
| `APPLE_CERTIFICATE` | Base64 of the `.p12` export of **Developer ID Application: Bandpey GmbH (TEAMID)** | R3, runbook M2 | macOS job: `packaging/macos/import-cert.sh` |
| `APPLE_CERTIFICATE_PASSWORD` | The `.p12` export's password | R3, M2 | the same |
| `KEYCHAIN_PASSWORD` | Random; the job's temporary keychain | `release-secrets.sh keychain` | the same |
| `APPLE_ID` | The Apple Account that notarizes (a member of the Bandpey GmbH team) | R3, M2 | macOS job: `xcrun notarytool` in `package.sh` |
| `APPLE_PASSWORD` | That account's app-specific password `office-notarize` | R3, M2 | the same |
| `APPLE_TEAM_ID` | Bandpey GmbH's team id (10 characters) | R3, M2 | the same |
| `AZURE_TENANT_ID` | The Entra tenant of the signing app registration | R4, M3 | Windows jobs: `azure/login` |
| `AZURE_CLIENT_ID` | App registration `office-signing`, with a federated credential for each repository's environment `release` and the role Artifact Signing Certificate Profile Signer on `bandpey-public`. Not secret, and it has no client secret: the job signs in with GitHub's OIDC token | R4, M3 | the same |
| `AZURE_SIGNING_ENDPOINT` | The Artifact Signing account's regional endpoint, `https://weu.codesigning.azure.net`; a mismatch gives 403 | R4, M3 | Windows jobs: `packaging/windows/sign.ps1` |
| `AZURE_SIGNING_ACCOUNT` | The Artifact Signing account, `bandpey-signing` | R4, M3 | the same |
| `AZURE_CERT_PROFILE` | The Public Trust certificate profile, `bandpey-public` | R4, M3 | the same |
| `PACKAGES_GPG_KEY` | The apt and dnf repositories' signing key (RSA 4096, 5 years, no passphrase) | `release-secrets.sh packages-key` | `facthory-packages.yml`, when a release is published |

What each run requires:

- **A release**, which any push to `main` starts when the version in `Cargo.toml` has none yet,
  refuses to build unless both platforms can sign: the five `APPLE_*` and `KEYCHAIN_PASSWORD` for
  macOS, and the five `AZURE_*` (or a `WINDOWS_CERTIFICATE` pair) for Windows. So **the first
  release needs R3 and R4 both**; until then, a push to `main` with a new version fails at that
  check and publishes nothing.
- **A manual run from `main` with `sign`** signs what it can and builds the rest unsigned, as
  workflow artifacts, without a release. That is how each identity is tested the day it lands.
- **The release's last step** calls `facthory-packages.yml`, which fails without `PACKAGES_GPG_KEY`.
- Not W4: `SYNC_APP_PRIVATE_KEY` in the environment `upstream-sync` (W3, runbook L).

The Windows signing client is pinned by upstream's `sign.ps1` itself since WordCraft v0.11.0:
`Microsoft.Trusted.Signing.Client` 1.0.95, checked by SHA-256. (Microsoft renamed the package
`Microsoft.ArtifactSigning.Client`, whose 1.0.139 and later also check the endpoint before they send
credentials; our brand rule that switched to it is retired, since we follow upstream's packaging.)

## The day R3 lands (Apple)

1. **Owner**: runbook M2, then `scripts/release-secrets.sh status` (the five `APPLE_*` and
   `KEYCHAIN_PASSWORD` set) and `scripts/release-secrets.sh copy` (it skips what is not set yet).
2. **Claude**: start a manual run in each repository:

   ```sh
   gh workflow run facthory-release.yml -R FACTHORYAI/page --ref main -f sign=true
   ```

3. The Windows jobs build unsigned in this run; its install check on macOS runs unsigned too
   (only a release checks signatures there).
4. **Claude**: download `release-macos` and check, on a Mac:

   ```sh
   spctl --assess --type open --context context:primary-signature -vvv facthorypage-<v>-macos-universal.dmg   # source=Notarized Developer ID
   xcrun stapler validate facthorypage-<v>-macos-universal.dmg
   hdiutil attach -readonly -nobrowse facthorypage-<v>-macos-universal.dmg
   codesign -dv --verbose=2 "/Volumes/Facthory Page/Facthory Page.app" # Authority=Developer ID Application: Bandpey GmbH; TeamIdentifier set
   spctl --assess --type execute -vvv "/Volumes/Facthory Page/Facthory Page.app"
   ```

   Then the way a user meets it: download the DMG with a browser (so it carries the quarantine
   flag), drag the app to Applications, open it from Finder with no Gatekeeper warning, and open a
   `.docx` (`.xlsx`, `.pptx`) by double-click. Unzip the CLI zip and run `facthorypage-cli --version`;
   a bare executable can't carry a stapled ticket, so Gatekeeper checks it online.

   (The DMG check is the one `package.sh` itself runs on a notarized image; `--type install` is
   for installer packages. github-infra's runbook M5 still names `--type install`.)

## The day R4 lands (Microsoft)

How the Windows jobs sign: they sign in to Azure with GitHub's OIDC token (`azure/login`), fetch
the signing token at once, and only then run `package.ps1 -SkipBuild` on the binaries an unsigned
run built first, so the token cannot run out during a long build. The brand rule's
`ExcludeCredentials` makes the signing library use the Azure CLI's sign-in alone; version 1.0.95
accepts the setting and all nine names in it (checked in the package, 2026-10-31). A pull request
never signs in, and a configured `WINDOWS_CERTIFICATE` pair is used instead of Azure.

1. **Owner**, once Microsoft's validation shows Completed: the certificate profile `bandpey-public`
   (owner guide, P3 part 2); the app registration `office-signing` with a federated credential for
   the environment `release` of page, grid and deck (P11); then runbook M3's `put` of the five
   `AZURE_*` values, `status` and `copy`.
2. **Claude**: a manual run as above.
3. **Claude**: the Windows jobs' logs show `signtool verify /pa` passing on the `.exe` files and the
   MSI (`sign.ps1` verifies what it signs). Download `release-windows-x64` and `-arm64`, check
   the MSI's signer, then install it silently and remove it on a Windows runner or machine, in
   PowerShell (the MSI installs for the current account by default, without UAC; to test the
   installation for everyone, add `'ALLUSERS=1'` in an elevated PowerShell, since `/qn` can't
   show the UAC prompt).
   `msiexec` is a windowed program, so PowerShell waits for it only through `Start-Process -Wait`:

   ```powershell
   Get-AuthenticodeSignature .\facthorypage-<v>-windows-x64.msi | Format-List Status, SignerCertificate   # Valid; CN=Bandpey GmbH
   (Start-Process msiexec -ArgumentList '/i', 'facthorypage-<v>-windows-x64.msi', '/qn', '/l*v', 'install.log' -Wait -PassThru).ExitCode   # 0
   (Start-Process msiexec -ArgumentList '/x', 'facthorypage-<v>-windows-x64.msi', '/qn' -Wait -PassThru).ExitCode                         # 0
   ```

## The first release (R3 and R4 both in)

Nobody tags or publishes: a release is a run of `facthory-release.yml` on `main` whose version has
no release yet. The workflow itself creates the tag `v<version>` when it publishes (only it may:
a tag ruleset in github-infra), on the commit it built and checked.

1. **Owner**: runbook M4: `scripts/release-secrets.sh packages-key`, `copy` (12 of 12), then in
   each repository GitHub Pages from GitHub Actions and release immutability on.
2. **Claude**: start it with a manual run from `main` (no input), or let the next push to `main`
   start it. The version is the one in `Cargo.toml` (`0.12.0` for page and deck, `0.13.0` for grid
   today). The run builds and signs every platform, installs each platform's files on a machine of
   that platform with every signature checked (`facthory/install_check.py`), publishes the release
   with `SHA256SUMS` and `latest.json` at a 10% rollout, and builds the apt and dnf repositories at
   `https://facthoryai.github.io/<app>/`.
3. **Claude**: check the published release: the checks of the two days above on its files, every
   installer in `SHA256SUMS` (which doesn't list `latest.json`, written after it), and
   `latest.json` naming the version, a file for each platform, and `"rollout": 10`.
4. **Claude**: install from each channel: the DMG, the MSI (x64 and arm64), the AppImage, the
   `.deb` from the apt repository on Ubuntu, the `.rpm` from the dnf repository on Fedora.
6. **Owner**: Partner Center's package check on the published MSI's URL (it needs a public one,
   `msi-requirements.md`) confirms the Store accepts an Artifact Signing certificate
   (`owner-checklist.md`, step 4).

## The update test

The other half of the exit criterion. The updater reads the feed compiled into release builds
(`releases/latest/download/latest.json` of the same repository) and refuses a file from anywhere
else, so updates can only be tested between two **published** releases:

1. Install the first release from each channel and start it once.
2. The next release publishes itself. The natural one is the next upstream release merged by the
   sync (W3): upstream is at WordCraft v0.12.0, GridCraft v0.13.0 and DeckCraft v0.12.0 on
   30 October. It reaches 10% of copies first: for the test, set the repository variable
   `FACTHORY_ROLLOUT` to `full` and run `facthory-rollout.yml` by hand (or give the test copies
   `"bucket": 0` in their `update.json`), and clear the variable afterwards.
3. The app reads the feed at most once a day, across restarts: `last_check` in `update.json` in
   its settings folder (on macOS `~/Library/Application Support/Facthory Page/`) holds the time of
   the last read. Wait a day after step 1, or set `"last_check": 0` there, before step 4; a
   restart within the day shows no notice, and the updater only looks broken.
4. Start each installed app. Expected:
   - **macOS**, app in `/Applications`: the notice says the update installs when the app quits;
     after quitting, the new bundle is in place, still `Notarized Developer ID`, and opens.
   - **Windows**, MSI install: the notice, then on quit the MSI upgrade (no prompt for a copy
     installed for the current account; an administrator prompt for one installed for everyone);
     Apps & features lists one Facthory Page with the new version.
   - **Linux AppImage**: the new AppImage takes the old one's name.
   - **`.deb`, `.rpm`**: the notice says the system updates it; `apt upgrade` and `dnf upgrade`
     install the new version from our repositories.
   - Portable zips and tarballs: a notice linking to the release.
5. Settings (`update.json`, recent files) survive the update on every platform.

Without the sync App the next release can still be merged by hand (`python3 facthory/sync.py merge`
on a branch, then a pull request), but W3's own exit criterion counts only automatic merges.

## Local macOS builds

Cold release builds (empty `target/`, crates already downloaded) of the branded tree on an Apple M4
Max (16 cores, 128 GB), macOS 27.0.1, Xcode 27.2 (macOS 27.2 SDK), Rust 1.99.1, with craft-fonts
at each app's pinned commit: the release job's `cargo build` command, but one target at a time,
to time each (the job builds both in one run). Then `packaging/macos/dmg/generate.py` and
`packaging/macos/package.sh --arch universal --skip-build` (the job runs it without
`--skip-build`), ad-hoc signed:

| App | arm64 | x86_64 | Package (`lipo`, sign, DMG, CLI zip) | DMG | CLI zip |
| --- | ----- | ------ | ------------------------------------ | --- | ------- |
| Facthory Page 0.10.0 | 3 min 42 s | 3 min 21 s | 32 s | 107 MB | 85 MB |
| Facthory Grid 0.11.1 | 1 min 47 s | 1 min 19 s | 3 s | 24 MB | 11 MB |
| Facthory Deck 0.10.0 | 3 min 13 s | 3 min 32 s | 10 s | 83 MB | 69 MB |

What the builds showed:

- Both architectures build with the installed toolchain, so the DMG is universal (`lipo -info`:
  x86_64 arm64). `codesign --verify --deep --strict` passes on each app, inside the DMG and on a
  copy taken out of it. `rebrand.py check` finds no upstream mark in the universal binaries.
- `Info.plist`: `com.facthory.page` / `.grid` / `.deck`, version as in `Cargo.toml`, macOS 11 or
  later; Page opens Word, OpenDocument, RTF, Markdown, HTML and text files, Grid `.xlsx`, `.xlsm`,
  `.xlsb`, `.ods`, `.csv`, `.tsv`, Deck `.pptx`, `.ppsx`, `.potx`.
- Each app, copied out of its DMG, opened a document made by its own CLI (a `.docx` report, an
  `.xlsx` with a column chart, a `.pptx`) and showed it, and its About box reads "Facthory Page"
  ("Grid", "Deck"), "Based on WordCraft (GridCraft, DeckCraft) by the ArtCraft team", both
  copyrights, and our links. The files they write name Facthory in `docProps/app.xml`.
- The DMG windows' backgrounds, regenerated by `generate.py`, show our names.
- The first start of the ad-hoc signed Page waited about a minute before it ran, while macOS
  assessed it; Grid and Deck started at once. Expect no such wait from a notarized build: check it
  on signing day.
- macOS 27 warns that `hdiutil attach -mountpoint` is deprecated (in favour of
  `diskutil image attach`); it still works. Upstream's `package.sh` and our updater
  (`facthory/update/facthory_update.rs`, `prepare_bundle`) both use it: watch for its removal.
