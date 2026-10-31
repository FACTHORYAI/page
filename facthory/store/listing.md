# Microsoft Store listing: Facthory Page

Draft for W9, 2026-10-25. Listing language: English (United States). Product type in Partner Center: **EXE or MSI app**. Everything in a `text` block is ready to paste; the counts beside each heading were measured on the block. Field limits are from Partner Center's MSI/EXE submission checklist ([create-app-submission](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/create-app-submission), updated 2026-08-24) and Store Policies 7.20 ([store-policies](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies), effective 2026-10-22).

Facts come from the app's own docs (this repository: README, ROADMAP, docs/gaps.md, docs/file-format-parity.md, docs/zotero.md, docs/recovery.md) and the brand patch set (`facthory/brand.toml`). The tree still says WordCraft; this listing uses only the Facthory name, except the credit.

## Blockers before this listing can be submitted

| # | Blocker | Owner |
| - | ------- | ----- |
| 1 | Counsel signs off "Facthory Page" (W0: Apple's PAGES; the opposition against FACTHORY). Reserve the name only after that | Owner |
| 2 | `https://facthory.com/page` and the privacy policy page are live. The website field, the installer's "About" link (`ARPURLINFOABOUT`) and the description all point there, and Microsoft fails submissions that link to pages under construction | Owner publishes; Claude can draft the pages |
| 3 | A signed Facthory Page MSI (x64 and ARM64) on an immutable, versioned GitHub release URL (see [the MSI requirements](../launch/msi-requirements.md)) | Claude (pipeline) and owner (signing identity) |
| 4 | ~~The in-app updater (W4) ships in that MSI~~ Done: FACTHORYAI/page#5. The Store does not update MSI apps, so the updater must stay on in the Store's copy (it is: the Store installs the same MSI) | Resolved |
| 5 | Screenshots rendered from the branded build (upstream's images show the WordCraft name and cannot be used) | Claude |

## Product name

| Field | Limit | Value |
| ----- | ----- | ----- |
| Product name | Must be a reserved name; up to 256 characters; no marketing or descriptive text (Policy 10.1.1) | `Facthory Page` |

Never "Page" alone, never with "Word" (§14.6).

## Short description (<!--n:short-->201<!--/--> characters; limit 1,000, keep under 270)

<!-- block:short -->
```text
Write, format and review documents in a familiar ribbon interface. Facthory Page opens and saves .docx files, works fully offline, needs no account and collects no data about you. Free and open source.
```

## Description (<!--n:desc-->2,974<!--/--> characters; limit 10,000; plain text, no URLs or HTML)

<!-- block:desc -->
```text
Facthory Page is a free, open-source word processor for Windows. It opens and saves .docx documents, works fully offline and needs no account. The ribbon, styles, keyboard shortcuts and page layout follow the workflow people already know, so you can start writing straight away.

WHAT YOU CAN DO TODAY
• Write and format: fonts, character and paragraph formatting, tabs, borders and shading, bullets and multilevel numbering, a live Styles gallery, themes and style sets, copy formatting, find and replace.
• Lay out pages: margins, orientation, columns, section breaks, headers and footers, page numbers, watermarks, page borders, line numbers, drop caps and automatic hyphenation.
• Tables and objects: tables with styles, merged cells and header rows that repeat on every page; pictures with crop and colour corrections; shapes and text boxes with text wrapping.
• References: tables of contents, footnotes and endnotes, citations and bibliographies in APA, MLA, Chicago and IEEE styles, captions, cross-references and an index. Works with the Zotero desktop app.
• Review: track changes, comments, accept and reject, compare documents, word count, an accessibility checker, and spelling and grammar as you type (English built in; more languages with installed dictionaries).
• Mailings: mail merge from CSV files and spreadsheets, envelopes and labels.
• Files: opens and saves .docx (including password-protected files), .odt, .rtf, .html, Markdown, LaTeX and plain text; opens legacy .doc files; exports PDF with selectable text, links and bookmarks; prints directly.
• Automate: every command can also be run from a command-line tool or a built-in MCP server, so scripts and AI agents that you run on your own computer can write and edit documents. No AI is built into the app.
• Dark mode, and an interface in more than 20 languages that follows your system language.

PRIVATE BY DESIGN
Facthory Page has no telemetry, no crash reporting, no advertising and no account. Your documents stay on your computer, and the app does not send them anywhere. The only connection it makes on its own is a daily check with its release page on GitHub for a newer version.

GOOD TO KNOW
Facthory Page is an early release and still maturing. Complex documents made in other word processors may not lay out exactly the same yet, and page breaks can fall in different places. Charts and diagrams from other apps are not yet fully editable. Macros in .docm files are kept but never run. Legacy .doc files open but are saved as .docx. Real-time co-authoring, add-ins and cloud storage are not part of the app. Keep a copy of important documents while you try it, and tell us what does not work: every report helps.

OPEN SOURCE
Facthory Page is open source under the MIT License or the Apache License 2.0, at your option. It is published by Bandpey GmbH (Facthory), Munich, and is based on WordCraft by the ArtCraft team. Source code, release notes and the issue tracker are on GitHub.
```

Notes on the text:
- No Microsoft product name appears. File formats are named by extension only (§14.6). "Ribbon" and "Styles gallery" are generic UI terms used by many office suites. Microsoft's own feature name "Format Painter" is written "copy formatting".
- "Diagrams" replaces SmartArt, which is a Microsoft trademark.
- The limitations come from `docs/gaps.md` (pagination, charts and diagrams, `.doc` read-only, macros kept but not run, no co-authoring) and Policy 10.1.1, which asks for "any important limitations".
- "Early release" is the honest stage: upstream calls it alpha (about 60 % ready for real work, `README.md` Roadmap). See the open question in [the owner checklist](../launch/owner-checklist.md) on Microsoft's "submit your app only when it's finished" guidance.
- Update the language claim if the brand build drops any catalog: `crates/ui-egui/src/i18n` holds 26 catalogs plus English today.

## Product features (<!--lines:features-->11<!--/--> features, longest <!--max:features-->100<!--/--> characters; limit 20 features of 200 characters, no bullets)

<!-- block:features -->
```text
Opens and saves .docx documents, including password-protected files
Also reads and writes .odt, .rtf, .html, Markdown, LaTeX and plain text, and opens legacy .doc files
Exports PDF with selectable text, links and bookmarks, and prints directly
Familiar ribbon, styles, themes and keyboard shortcuts
Track changes, comments, compare documents and an accessibility checker
Tables of contents, footnotes, citations, bibliographies, captions and indexes
Mail merge from CSV files and spreadsheets, plus envelopes and labels
Works fully offline: no account, no telemetry, no crash reporting
Scripts and local AI agents can drive every command through a CLI and an MCP server
Dark mode and an interface in more than 20 languages
Free and open source under MIT or Apache-2.0
```

## Search terms (<!--lines:keywords-->7<!--/--> terms, <!--words:keywords-->12<!--/--> unique words, longest <!--max:keywords-->15<!--/--> characters; limit 7 terms, 40 characters each, 21 unique words; Policy 10.1.3: no pricing terms, no other products' titles)

<!-- block:keywords -->
```text
docx editor
document editor
writing app
track changes
mail merge
open source
offline
```

Left out on purpose: "free" (a pricing term, Policy 10.1.3), every Microsoft, Google, Apple or LibreOffice product name, "office" (reads as a product title), and "word processor" (generic, but it contains "word", which §14.6 bars from keywords; use it only with counsel's sign-off).

## Category (Properties page)

| Field | Value | Why |
| ----- | ----- | --- |
| Category | **Productivity** (no subcategories exist) | "Apps which help user to complete a particular task more efficiently" ([categories](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/categories-and-subcategories)) |
| Secondary category | **Business**, subcategory blank | Microsoft's examples for Business include "Document reader/scanner/editor" |

## System requirements

Properties page checkboxes (minimum / recommended):

| Item | Minimum | Recommended |
| ---- | ------- | ----------- |
| Keyboard | ✓ | ✓ |
| Mouse | ✓ | ✓ |
| Touch screen, camera, NFC, Bluetooth LE, telephony, microphone | — | — |
| Memory | leave blank until measured | leave blank until measured |
| DirectX | leave blank (the app falls back to OpenGL or a software renderer) | DirectX 12 |
| Dedicated GPU memory, processor, graphics | leave blank | leave blank |

Do not tick "pen and ink" until pen input is tested on Windows. Do not tick "tested to meet accessibility guidelines": Microsoft requires Narrator, high-contrast and keyboard testing first, and screen-reader access to the page canvas is still untested (`docs/gaps.md` #18).

Additional system requirements, minimum (<!--lines:addmin-->4<!--/--> items, longest <!--max:addmin-->95<!--/--> characters; limit 11 of 200 characters):

<!-- block:addmin -->
```text
Windows 10 or Windows 11, 64-bit (x64 or ARM64)
A graphics adapter with DirectX 12 or OpenGL; older PCs fall back to a slower software renderer
Optional: the Zotero desktop app for Zotero citations
Optional: Hunspell dictionaries for spelling in languages other than English
```

Recommended (<!--lines:addrec-->1<!--/--> items):

<!-- block:addrec -->
```text
A graphics adapter with a current DirectX 12 driver
```

Memory and disk space: measure the installed size and a 100-page document's working set on the release build, then add them here. Do not guess.

## What's new in this version (limit 1,500 characters)

Leave blank on the first submission (Microsoft's instruction). Template for updates:

```text
Facthory Page <version>

New
• <one line per user-visible addition>

Fixed
• <one line per user-visible fix>

Known issues
• <only if something new is known to be broken>

Full release notes are on GitHub under release v<version>.
```

## Copyright, licence terms, developer

| Field | Limit | Value |
| ----- | ----- | ----- |
| Copyright and trademark info (<!--n:copyright-->127<!--/--> chars) | 200 | see block |
| Applicable license terms (<!--n:license-->763<!--/--> chars) | 10,000, **required** | see block |
| Developed by (<!--n:devby-->64<!--/--> chars) | 255 | see block |

<!-- block:copyright -->
```text
© 2026 Bandpey GmbH. Based on WordCraft, © 2026 ArtCraft Team and the WordCraft contributors. Licensed under MIT OR Apache-2.0.
```

<!-- block:license -->
```text
Facthory Page is free and open-source software. You may use, copy, modify and distribute it under the terms of either the MIT License or the Apache License, Version 2.0, at your option.

MIT License: https://github.com/FACTHORYAI/page/blob/main/LICENSE-MIT
Apache License 2.0: https://github.com/FACTHORYAI/page/blob/main/LICENSE-APACHE
Notices: https://github.com/FACTHORYAI/page/blob/main/NOTICE
Third-party fonts and assets and their licences: https://github.com/FACTHORYAI/page/blob/main/ATTRIBUTION.md

The software is provided "as is", without warranty of any kind, as both licences state. Facthory Page is based on WordCraft by the ArtCraft team; their copyright and licence notices are kept. The Facthory name and logos are not licensed under these terms.
```

<!-- block:devby -->
```text
Bandpey GmbH (Facthory), based on WordCraft by the ArtCraft team
```

A trademark sentence ("Facthory is a trademark of Bandpey GmbH") is left out until counsel advises, because the FACTHORY application faces an opposition.

## Support info (Properties page)

| Field | Value |
| ----- | ----- |
| Does this product access, collect or transmit personal information? | **Yes.** Policy 10.5.1 says Win32 products "inherently have access to Personal Information" and must always have a privacy policy; the update check also reaches GitHub, which sees the user's IP address |
| Privacy policy URL | `https://facthory.com/privacy/apps` (**to publish**; one policy for all three apps, text in [the privacy policy draft](../launch/privacy-policy.md)). If the page is not live in time, Partner Center also accepts the policy text pasted directly ([support-info](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/support-info)) |
| Website | `https://facthory.com/page` (**to publish**) |
| Support contact info | `https://github.com/FACTHORYAI/page/issues` |
| Contact details (phone, address; required for company accounts) | the company's registered address and support phone from [the owner checklist](../launch/owner-checklist.md), step 3 |

## Screenshots

PNG, landscape, at least 1366 × 768 (render at 1920 × 1080 or 2560 × 1440), at most 50 MB each, 1 required, up to 10 ([MSIX image specs](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/screenshots-and-images); the MSI page links the same rules). Captions up to 200 characters. Keep important content in the top two-thirds (the Store may overlay text on the bottom third). No added logos, frames or marketing text. Render each from the **branded** build with the headless renderer (`cargo run -p facthorypage-ui-egui --example ui_shot` after `facthory/rebrand.py apply`), light theme unless stated, English interface, sample content only (no personal names, paths or user folders in recent-file lists).

| # | Shows | Caption (longest <!--max:captions-->76<!--/--> chars) |
| - | ----- | ------- |
| 1 | Home tab over the built-in sample handbook: Styles gallery with live previews, Navigation pane with headings, rulers, a word selected | `Write in a familiar ribbon interface with live styles and a navigation pane.` |
| 2 | Review tab, track changes on: an insertion and a deletion, three comment balloons in the margin | `Track changes and comments, then accept or reject each one.` |
| 3 | References tab, two pages: a table of contents with dotted leaders, a styled table, a footnote | `Tables of contents, footnotes, citations and bibliographies.` |
| 4 | Layout tab at 80 %: drop cap, a picture with text wrapping, line numbers, page border | `Lay out pages with columns, text wrapping, drop caps and page borders.` |
| 5 | File start page: template thumbnails and an empty recent list | `Start from a template, or open .docx, .odt, .rtf and more.` |
| 6 | Dark mode with formatting marks and the Insert tab | `Dark mode, with formatting marks when you need them.` |
| 7 | Export to PDF dialog over a document | `Export PDF with selectable text, links and bookmarks.` |

<!-- block:captions -->
```text
Write in a familiar ribbon interface with live styles and a navigation pane.
Track changes and comments, then accept or reject each one.
Tables of contents, footnotes, citations and bibliographies.
Lay out pages with columns, text wrapping, drop caps and page borders.
Start from a template, or open .docx, .odt, .rtf and more.
Dark mode, with formatting marks when you need them.
Export PDF with selectable text, links and bookmarks.
```

## Store logos

| Asset | Size (PNG, ≤ 50 MB) | Status for MSI apps | Source |
| ----- | ------------------- | ------------------- | ------ |
| 1:1 box art | 2160 × 2160 (or 1080 × 1080) | **Required** | Render `facthory/icons/page.svg` with resvg; icon centred on a plain background in the brand colour; no text in the bottom third |
| 2:3 poster art | 1440 × 2160 (or 720 × 1080) | Recommended | Same icon, with "Facthory Page" in the top two-thirds if text is used (contrast at least 4.5:1) |
| 1:1 app tile icon | 300 × 300 | Recommended on the MSIX page; the MSI listing CSV has no column for it, so upload it only if the MSI listing page offers the slot | `facthory/icons/app-icon/` render |

Sizes from the [MSIX screenshots and images page](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/screenshots-and-images); "required: 1:1 box art, recommended: 2:3 poster art" from the [MSI page](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/screenshots-and-images) and the MSI listing CSV ([import and export](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/import-and-export-store-listings): `StoreLogos1` 1:1, `StoreLogos2` 2:3). The icon must not resemble Microsoft's blue "W" (§14.5).

## Packages page

| Field | x64 package | ARM64 package |
| ----- | ----------- | ------------- |
| Package URL | `https://github.com/FACTHORYAI/page/releases/download/v<version>/facthorypage-<version>-windows-x64.msi` | `…/facthorypage-<version>-windows-arm64.msi` |
| Architecture | x64 | arm64 |
| App type | MSI (the Store runs it with `/qn`) | MSI |
| Languages | English (en-us) | English (en-us) |

Declare more languages only together with a translated listing for each (Policy 10.7). German is the natural second listing.

## Notes for certification (<!--n:notes-->1,440<!--/--> characters; limit 2,000)

<!-- block:notes -->
```text
Facthory Page is a desktop word processor delivered as an MSI that installs for the current user by default (no UAC prompt); an installation for all users is offered in its interactive setup and asks for elevation. No account, sign-in or server is needed and the app works fully offline.

How to test: start Facthory Page from the Start menu. On the File start page choose a template (for example the sample handbook) or Blank document. Type and format text, insert a table, then use File > Save As to save a .docx and File > Export to create a PDF. The Review tab shows track changes and comments.

Network: the app does not connect to any server of ours. If update checks are on, it asks GitHub's release feed for this app whether a newer version exists. Links inside documents open in the default browser.

No generative AI is built in. The command-line tool facthorypage-cli.exe, installed next to the app, includes an MCP server: a local automation interface that scripts or AI agents the user runs can use. It talks over standard input and output, and the app's optional control channel listens only on 127.0.0.1, only when started with --control, and requires a key.

Uninstall through Settings > Apps removes all installed files and registry entries. Per-user settings, logs and recovery copies the app created in %APPDATA%\Facthory Page are left in place, as is usual for user data.

Contact: <support email>. Notes written <date>.
```
