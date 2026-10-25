# Downloads: copy for facthory.com

Copy for the three download pages (`facthory.com/page`, `facthory.com/grid`, `facthory.com/deck`,
the website URLs the apps' About boxes already link to), plus the shared sections they all use.

> **Notes for the web editor (not for publication)**
>
> - **File names are inferred, not yet published.** They follow the packaging scripts
>   (`packaging/macos/package.sh`, `packaging/linux/package.sh`, `packaging/windows/package.ps1`
>   and `*.wxs`) after `facthory/rebrand.py apply` renames `wordcraft`/`gridcraft`/`deckcraft` to
>   `facthorypage`/`facthorygrid`/`facthorydeck`, and the W4 release workflow in progress for
>   Facthory Page (`.github/workflows/facthory-release.yml`, `facthory/release.py`, WIP on branch
>   `w4-release`). Grid and Deck have no release workflow yet; check the names against the first
>   real release of each before the page goes live.
> - **That workflow builds**: macOS universal DMG and CLI zip; Windows MSI and portable zip for x64
>   and arm64 (no 32-bit x86, although upstream builds it); Linux AppImage (+ `.zsync`), `.deb`,
>   `.rpm` and `.tar.gz` for x86_64 and aarch64. **No Flatpak bundle yet**, although the plan
>   lists one: show the Flatpak button only if W4 adds it. FreeBSD, RISC-V and the web build are
>   not offered.
> - **Checksums** are in one file per release named `SHA256SUMS` (not `SHA256SUMS.txt` as
>   upstream names it). The release also carries `latest.json`, the update feed, which lists the
>   DMG, both MSIs and both AppImages with URL, size and SHA-256: the page can fill its main
>   buttons from `https://github.com/FACTHORYAI/<app>/releases/latest/download/latest.json`.
>   `.deb`, `.rpm`, `.tar.gz` and the zips are not in the feed; link them from the release
>   (`https://github.com/FACTHORYAI/<app>/releases/download/v<version>/<file>`).
> - **Versions follow upstream**: Facthory Page 0.10.0 is built from upstream 0.10.0; tags are
>   `v<version>`.
> - Never use "Word", "Excel" or "PowerPoint" in a heading, button, title or page name here (§14.6).

## File names

`<app>` is `page`, `grid` or `deck`; `<version>` is the release number, for example `0.10.0`.

| Platform | File |
| -------- | ---- |
| macOS app, universal (Apple silicon and Intel) | `facthory<app>-<version>-macos-universal.dmg` |
| macOS command-line tool, universal | `facthory<app>-cli-<version>-macos-universal.zip` |
| Windows installer, x64 or ARM64 | `facthory<app>-<version>-windows-x64.msi`, `facthory<app>-<version>-windows-arm64.msi` |
| Windows portable (no install) | `facthory<app>-<version>-windows-<x64\|arm64>-portable.zip` |
| Linux AppImage | `facthory<app>-<version>-linux-<x86_64\|aarch64>.AppImage` (+ `.AppImage.zsync` for delta updates) |
| Linux Debian/Ubuntu package | `facthory<app>-<version>-linux-<x86_64\|aarch64>.deb` |
| Linux Fedora/openSUSE package | `facthory<app>-<version>-linux-<x86_64\|aarch64>.rpm` |
| Linux tarball | `facthory<app>-<version>-linux-<x86_64\|aarch64>.tar.gz` |
| Linux Flatpak (if W4 ships it) | `facthory<app>-<version>-linux-<x86_64\|aarch64>.flatpak` |
| Checksums for all of the above | `SHA256SUMS` |

Installed names: the apps are **Facthory Page**, **Facthory Grid** and **Facthory Deck**; the
programs are `facthorypage`, `facthorygrid`, `facthorydeck` with `facthorypage-cli` and so on; the
app ids are `com.facthory.page`, `com.facthory.grid`, `com.facthory.deck`. On Windows they install
into `C:\Program Files\Facthory Page\` (and Grid, Deck).

---

## Facthory Page

**A word processor that opens and saves `.docx` documents.** Styles, tables, track changes,
references and mail merge, on your own computer: free, open source, no account, works offline.

*Early release (alpha).* [Switching to Facthory Page →](switch-page.md)

| Platform | Button | File |
| -------- | ------ | ---- |
| macOS 11+ | **Download for Mac** (Apple silicon and Intel) | `facthorypage-<version>-macos-universal.dmg` |
| Windows 10+ | **Download for Windows** (x64) | `facthorypage-<version>-windows-x64.msi` |
| Windows 11 on ARM | **Download for Windows on ARM** | `facthorypage-<version>-windows-arm64.msi` |
| Linux x86_64 | **AppImage** · **.deb** · **.rpm** · **.tar.gz** | `facthorypage-<version>-linux-x86_64.{AppImage,deb,rpm,tar.gz}` |
| Linux ARM64 | **AppImage** · **.deb** · **.rpm** · **.tar.gz** | `facthorypage-<version>-linux-aarch64.{AppImage,deb,rpm,tar.gz}` |

More: **Portable for Windows** (`facthorypage-<version>-windows-<arch>-portable.zip`) ·
**Command-line tool for Mac** (`facthorypage-cli-<version>-macos-universal.zip`; the Windows and
Linux downloads already include it) · **Microsoft Store**: coming soon ·
[All releases and checksums](https://github.com/FACTHORYAI/page/releases)

Opens and saves `.docx`, `.docm`, `.dotx`, `.dotm`, `.odt`, `.rtf`, `.html`, `.md`, `.tex` and
`.txt`; opens `.doc`; exports PDF.

**Licence and credit.** Free and open-source software under the MIT licence or the Apache License
2.0, at your option. Copyright © 2026 Bandpey GmbH. Facthory Page is based on WordCraft by the
ArtCraft team (copyright © 2026 the ArtCraft Team and its contributors).
[Source code](https://github.com/FACTHORYAI/page) ·
[Licence and notices](https://github.com/FACTHORYAI/page/blob/main/NOTICE) ·
[Report a problem](https://github.com/FACTHORYAI/page/issues)

---

## Facthory Grid

**A spreadsheet app that opens and saves `.xlsx` workbooks.** Formulas and over 500 functions,
tables, conditional formatting, PivotTables and charts, on your own computer: free, open source,
no account, works offline.

*Early release (alpha).* [Switching to Facthory Grid →](switch-grid.md)

| Platform | Button | File |
| -------- | ------ | ---- |
| macOS 11+ | **Download for Mac** (Apple silicon and Intel) | `facthorygrid-<version>-macos-universal.dmg` |
| Windows 10+ | **Download for Windows** (x64) | `facthorygrid-<version>-windows-x64.msi` |
| Windows 11 on ARM | **Download for Windows on ARM** | `facthorygrid-<version>-windows-arm64.msi` |
| Linux x86_64 | **AppImage** · **.deb** · **.rpm** · **.tar.gz** | `facthorygrid-<version>-linux-x86_64.{AppImage,deb,rpm,tar.gz}` |
| Linux ARM64 | **AppImage** · **.deb** · **.rpm** · **.tar.gz** | `facthorygrid-<version>-linux-aarch64.{AppImage,deb,rpm,tar.gz}` |

More: **Portable for Windows** (`facthorygrid-<version>-windows-<arch>-portable.zip`) ·
**Command-line tool for Mac** (`facthorygrid-cli-<version>-macos-universal.zip`; the Windows and
Linux downloads already include it) · **Microsoft Store**: coming soon ·
[All releases and checksums](https://github.com/FACTHORYAI/grid/releases)

Opens and saves `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, `.csv` and `.tsv`; imports `.xls`, `.xlsb`
and `.ods`; exports PDF and HTML.

**Licence and credit.** Free and open-source software under the MIT licence or the Apache License
2.0, at your option. Copyright © 2026 Bandpey GmbH. Facthory Grid is based on GridCraft by the
ArtCraft team (copyright © 2026 the ArtCraft Team and its contributors).
[Source code](https://github.com/FACTHORYAI/grid) ·
[Licence and notices](https://github.com/FACTHORYAI/grid/blob/main/NOTICE) ·
[Report a problem](https://github.com/FACTHORYAI/grid/issues)

---

## Facthory Deck

**A presentation app that opens and saves `.pptx` decks.** Masters and layouts, shapes, charts,
transitions and animations, presenter view, on your own computer: free, open source, no account,
works offline.

*Alpha, heading for beta: expect gaps and keep the originals of decks that matter.*
[Switching to Facthory Deck →](switch-deck.md)

| Platform | Button | File |
| -------- | ------ | ---- |
| macOS 11+ | **Download for Mac** (Apple silicon and Intel) | `facthorydeck-<version>-macos-universal.dmg` |
| Windows 10+ | **Download for Windows** (x64) | `facthorydeck-<version>-windows-x64.msi` |
| Windows 11 on ARM | **Download for Windows on ARM** | `facthorydeck-<version>-windows-arm64.msi` |
| Linux x86_64 | **AppImage** · **.deb** · **.rpm** · **.tar.gz** | `facthorydeck-<version>-linux-x86_64.{AppImage,deb,rpm,tar.gz}` |
| Linux ARM64 | **AppImage** · **.deb** · **.rpm** · **.tar.gz** | `facthorydeck-<version>-linux-aarch64.{AppImage,deb,rpm,tar.gz}` |

More: **Portable for Windows** (`facthorydeck-<version>-windows-<arch>-portable.zip`) ·
**Command-line tool for Mac** (`facthorydeck-cli-<version>-macos-universal.zip`; the Windows and
Linux downloads already include it) · **Microsoft Store**: coming soon ·
[All releases and checksums](https://github.com/FACTHORYAI/deck/releases)

Opens and saves `.pptx` and its own `.facthorydeck` format; opens `.potx` and `.ppsx`; exports PDF,
PNG, JPEG and animated GIF.

**Licence and credit.** Free and open-source software under the MIT licence or the Apache License
2.0, at your option. Copyright © 2026 Bandpey GmbH. Facthory Deck is based on DeckCraft by the
ArtCraft team (copyright © 2026 the ArtCraft Team and its contributors).
[Source code](https://github.com/FACTHORYAI/deck) ·
[Licence and notices](https://github.com/FACTHORYAI/deck/blob/main/NOTICE) ·
[Report a problem](https://github.com/FACTHORYAI/deck/issues)

---

## System requirements (all three apps)

| | Requirement |
| - | ----------- |
| **macOS** | macOS 11 Big Sur or later, on Apple silicon or Intel (one universal download). |
| **Windows** | Windows 10 or later, 64-bit (x64), or Windows 11 on ARM. A graphics card with DirectX 12 is used when present; otherwise the app switches to OpenGL by itself. Installing needs administrator rights. No extra runtime to install. |
| **Linux** | x86_64 or ARM64 with glibc 2.35 or newer (Ubuntu 22.04, Debian 12, Fedora 36 or newer); X11 or Wayland; a Vulkan or OpenGL (EGL) graphics driver, such as Mesa. Facthory Deck also needs ALSA (`libasound2`) for sound. |
| **Fonts** | Microsoft's fonts are not included. Installed fonts are used; open fonts with the same measurements (Carlito, Caladea, Liberation) stand in for the common Office fonts. Each app's guide has the details. |

> **Editor note:** the docs give no minimum memory or disk space; leave those out or measure them
> on the W4 test machines.

## Check your download

Every release has a file named `SHA256SUMS` listing the SHA-256 checksum of each download.
Download it into the same folder as your file, then:

**macOS** (Terminal): the two lines should show the same hash.

```sh
shasum -a 256 facthorypage-<version>-macos-universal.dmg
grep facthorypage-<version>-macos-universal.dmg SHA256SUMS
```

**Windows** (PowerShell): compare the result with the line for your file in `SHA256SUMS`.

```powershell
(Get-FileHash .\facthorypage-<version>-windows-x64.msi -Algorithm SHA256).Hash.ToLower()
```

**Linux**

```sh
sha256sum -c SHA256SUMS --ignore-missing
```

On Linux the command prints `OK` next to each file you have; on macOS and Windows the hashes
match when the file is intact.

The installers are also signed by **Bandpey GmbH**:

- **macOS**: the app is signed with a Developer ID and notarized by Apple. To check it:
  `spctl --assess --verbose "/Applications/Facthory Page.app"` should print `accepted` and
  `source=Notarized Developer ID`.
- **Windows**: right-click the `.msi`, choose **Properties › Digital Signatures**: the signer is
  Bandpey GmbH. Or in PowerShell: `Get-AuthenticodeSignature .\facthorypage-<version>-windows-x64.msi`.
  For a brand-new release, Windows SmartScreen may still ask before running it; check that the
  publisher reads Bandpey GmbH.
- **Linux** packages are not signed; use the checksums.

## Updates

The apps update themselves: once a day each one checks its release page on GitHub, downloads a
new version in the background, checks it, and installs it when you quit (the macOS app, the
Windows installer and the AppImage). `.deb` and `.rpm` installs update when you install the newer
package; portable copies show a link to the new release. Settings are kept.

## Privacy

No account and no sign-in. The apps work offline, send no telemetry and have no crash reporting;
your files stay on your computer unless you send them somewhere. The only connection the apps make
on their own is the daily update check with GitHub, which you can turn off (privacy policy).

## If the app doesn't start on Windows

Some graphics drivers crash when the app starts. Try another graphics backend from PowerShell
(Page shown; use `Facthory Grid\facthorygrid.exe` or `Facthory Deck\facthorydeck.exe` for the
others):

```powershell
$env:WGPU_BACKEND = "gl"        # or "vulkan", or "dx12"
& "C:\Program Files\Facthory Page\facthorypage.exe"
Remove-Item Env:WGPU_BACKEND    # back to the default afterwards
```

`gl` can crash on some AMD drivers and `vulkan` on some Intel UHD drivers; if one fails, try the
other. Either way, please [report it](https://github.com/FACTHORYAI/page/issues) with the log from
`%APPDATA%\Facthory Page\logs\`.

## Help

Each app has a guide for people coming from other office apps, and a public issue tracker on
GitHub for questions and problems: [Page](https://github.com/FACTHORYAI/page/issues) ·
[Grid](https://github.com/FACTHORYAI/grid/issues) · [Deck](https://github.com/FACTHORYAI/deck/issues).

Facthory Page, Facthory Grid and Facthory Deck are published by Bandpey GmbH.
