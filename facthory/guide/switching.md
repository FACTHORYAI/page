# Switching to Facthory Page

Facthory Page is a free, open-source word processor for macOS, Windows and Linux. It opens and
saves `.docx` documents, has a ribbon and keyboard shortcuts you already know, and runs entirely on
your computer: no account, no subscription, no telemetry, and it works offline.

This guide is for people moving over from Microsoft Word. It covers installing, opening your
documents, what is the same, what is different or missing today, and where to get help.

> **An early release.** Facthory Page follows its upstream project closely, and upstream calls the
> app **alpha**: the everyday work (writing, formatting, styles, lists, tables, references, review,
> mail merge, opening and saving `.docx`) works end to end, but some documents will not look exactly
> as they do in Word. Keep the originals of documents that matter until you have checked them.

Facthory Page is based on WordCraft by the ArtCraft team.

> **Draft note (remove before publishing):** add Facthory's own fidelity result here once W6
> reports it: "On Facthory's test set of N real-world documents, X% open, save and reopen without
> visible change."

## 1. Install

Download from [facthory.com/page](https://facthory.com/page) or the
[GitHub releases](https://github.com/FACTHORYAI/page/releases/latest). Each release lists a
SHA-256 checksum for every file; the downloads page explains how to check one.

| System | File | How |
| ------ | ---- | --- |
| **macOS** 11 or later, Apple silicon or Intel | `facthorypage-<version>-macos-universal.dmg` | Open the DMG and drag Facthory Page to Applications. Signed and notarized by Bandpey GmbH; macOS only asks the usual first-launch question for downloaded apps. |
| **Windows** 10 or later (x64), Windows 11 on ARM | `facthorypage-<version>-windows-x64.msi` or `…-windows-arm64.msi` | Run the installer. It installs for you alone without administrator rights; its first page also offers an installation for everyone on the computer, which asks for them. Signed by Bandpey GmbH. |
| **Linux** x86_64 or ARM64 | `.AppImage`, `.deb`, `.rpm` or `.tar.gz` | See below. |

On Linux:

```sh
# AppImage: runs on most distributions, no install needed
chmod +x facthorypage-<version>-linux-x86_64.AppImage && ./facthorypage-<version>-linux-x86_64.AppImage

# Debian, Ubuntu, Mint, Pop!_OS
sudo apt install ./facthorypage-<version>-linux-x86_64.deb

# Fedora, openSUSE
sudo dnf install ./facthorypage-<version>-linux-x86_64.rpm
```

Use `aarch64` in place of `x86_64` on ARM64 machines. The Linux builds need glibc 2.35 or newer
(Ubuntu 22.04, Debian 12, Fedora 36 or newer).

The Microsoft Store listing is coming soon.

> **Draft note:** Flatpak comes through Flathub (W10, with the sandboxed builds); add its row then.

**You can keep Microsoft Office installed.** The installers register Facthory Page for Word, RTF
and OpenDocument files without taking over your defaults, so nothing changes until you choose.

## 2. Open your documents

- **File › Open**, drag a file onto the window, or right-click a file and choose **Open With ›
  Facthory Page**.
- Opens and saves: `.docx`, `.docm`, `.dotx`, `.dotm`, `.odt`, `.rtf`, `.html`, `.md` (Markdown),
  `.tex` (LaTeX) and `.txt`, plus the single-file XML formats Word can save.
- Opens only: legacy 97-2003 `.doc` and `.dot`. Save them as `.docx`.
- Exports: PDF (with selectable text, links and bookmarks) and page images.
- Password-protected `.docx` files open and save with their password.

### Make Facthory Page your default

- **Windows**: in Facthory Page choose **File › Options › General › Make Facthory Page the
  default…**. Windows does not let apps set this themselves, so the button opens
  **Settings › Apps › Default apps** on Facthory Page's page, where you pick it for each file type.
  Alternatively, right-click a `.docx`, choose **Open with › Choose another app**, select Facthory
  Page and tick **Always**.
- **macOS**: select a `.docx` in Finder, choose **File › Get Info**, pick Facthory Page under
  **Open with**, then click **Change All**. Repeat for `.doc` or other types you use. (File ›
  Options in the app shows the same steps.)
- **Linux**: if you installed the `.deb` or `.rpm`, the same **File › Options › General** button
  makes Facthory Page the default for Word, RTF and ODT files. With the AppImage, use your
  desktop's file manager (**Properties › Open With › Set as default**), or run:

  ```sh
  xdg-mime default com.facthory.page.desktop \
    application/vnd.openxmlformats-officedocument.wordprocessingml.document
  ```

## 3. What looks and works the same

- **The ribbon.** File, Home, Insert, Draw, Design, Layout, References, Mailings, Review, View and
  Developer, plus the contextual tabs (Table Design, Table Layout, Picture Format, Shape Format,
  Header & Footer, Equation, Outlining). Of the 513 ribbon and menu features in the project's
  feature catalogue, **498 (97.1%) have a working command** (measured; the full list is in
  [docs/parity-checklist.md](https://github.com/FACTHORYAI/page/blob/main/docs/parity-checklist.md)).
  You can customise the ribbon and the Quick Access Toolbar.
- **Keyboard.** The usual Ctrl (⌘ on Mac) shortcuts, plus F4 to repeat, F7 for spelling, F8 to
  extend a selection, Alt+Shift+arrows to move paragraphs, the field keys (F9 family) and Alt+Q to
  search commands. Press **Alt** or **F10** for ribbon key tips. On macOS the shortcuts follow the
  Mac version of Word (⌘⇧S Save As, ⌘⌥A New Comment). **152 commands have a default shortcut**
  (counted 2026-10-13; Word has about 250), and **Tools › Customize Keyboard** lets you add your
  own ([docs/ui-parity.md](https://github.com/FACTHORYAI/page/blob/main/docs/ui-parity.md)).
- **Typing.** Enter continues a list, Tab demotes it, `* ` and `1. ` start lists, smart quotes,
  AutoCorrect and dashes behave as in Word; each behaviour was compared keystroke by keystroke
  ([docs/typing-parity.md](https://github.com/FACTHORYAI/page/blob/main/docs/typing-parity.md)).
- **The features you use every week.** Styles and the live Styles gallery, themes, lists, tables
  (with table styles, formulas and repeated header rows), headers and footers, sections, columns,
  pictures and text wrapping, track changes and comments, compare documents, tables of contents,
  footnotes, citations (APA, MLA, Chicago, IEEE), captions, index, mail merge, envelopes and
  labels, equations, Navigation pane, Read mode, Focus, dark mode.
- **Printing** to your printer with printer choice, copies, collation, duplex and grayscale.
- **Recovery.** Unsaved work is copied locally while you write; **File › Recover** brings it back
  after a crash.
- **More than 20 interface languages**, following your system language by default.

## 4. What is different or missing today

These come from the project's own gap list
([docs/gaps.md](https://github.com/FACTHORYAI/page/blob/main/docs/gaps.md)) and parity documents.

- **Page breaks can fall differently.** Word's default font since 2024, Aptos, has no open font
  with the same measurements, so text set in Aptos wraps a little earlier. On a test set of 251
  documents compared with Word's own PDFs, **229 (91%) had the same number of pages**, and about
  **half of all page breaks (50.1%) fell at the same word** (measured by upstream, 2026-10-17).
  Column balancing and footnotes that continue onto the next page are not done yet.
- **Real-world `.docx` testing is still under way.** Word opens the files Facthory Page saves,
  but upstream's tests are mostly built from synthetic files; its own estimate of `.docx` fidelity
  is about 65%.
- **Charts and SmartArt** from Word are drawn and kept when you save, but they can't be edited
  yet (charts and SmartArt you create in Facthory Page can). Combo, 3-D and stock charts show as a
  placeholder with their title. Embedded OLE objects and ink from Word show as their picture.
- **Macros are kept but never run.** `.docm` files keep their VBA on save. There are no Office
  add-ins.
- **`.doc` is read-only**: save as `.docx`. Some password-protected `.doc` files don't open.
- **Spelling and grammar** for English are built in. Polish, Russian, Portuguese, Czech, Italian,
  Croatian and Turkish spelling use a Hunspell dictionary installed on your system
  ([how to install one](https://github.com/FACTHORYAI/page/blob/main/docs/spelling-dictionaries.md)).
  Most of the other languages Word proofs are not covered yet.
- **Not there yet:** Dictate, Translate, Online Pictures and Online Video, 3D models, Screenshot,
  View Side by Side and Arrange All, mail merge from Outlook contacts or databases (CSV and
  spreadsheets work), email merge, opening a PDF as an editable document, pages per sheet when
  printing. Word has about 100 dialogs; Facthory Page has about 60 so far.
- **Known stability reports.** A startup crash on some Intel UHD graphics on Windows, and freezes
  in a few font-heavy cases, are still open. If the app doesn't start on Windows, the
  troubleshooting note on the [downloads page](https://facthory.com/page) shows how to pick
  another graphics backend.
- **Screen readers**: the document is exposed to accessibility tools but has not yet been tested
  with real screen readers.

Upstream's own estimates, for orientation: about **63%** ready for someone who uses the core
features, about **55%** for a typical professional's weekly work (estimates, 2026-10-10;
[ROADMAP.md](https://github.com/FACTHORYAI/page/blob/main/ROADMAP.md)).

## 5. Fonts

Microsoft's fonts (Calibri, Cambria, Aptos and others) are not included; their licence does not
allow it.

- **If a font is installed on your computer, Facthory Page uses it.** Windows, for example,
  includes Calibri, Cambria, Arial and Times New Roman.
- **If it isn't**, Facthory Page draws the text with an open font that has the same measurements:
  **Carlito** for Calibri, **Caladea** for Cambria, **Liberation Sans, Serif and Mono** for Arial,
  Times New Roman and Courier New, so lines and pages break where they did in Word, or very close.
- Install those open fonts for the best match; they are not bundled with Facthory Page. On
  Debian or Ubuntu: `sudo apt install fonts-crosextra-carlito fonts-crosextra-caladea
  fonts-liberation2`; on other systems, look for Carlito, Caladea and Liberation in your package
  manager or download them from their projects.
- **Aptos** has no metric-compatible open substitute yet, so documents in Aptos reflow slightly.

## 6. Sharing files back and forth

Save as `.docx` and send the file as usual: people who use Microsoft Word open it as any other Word
document. Track changes, comments, styles, tables, headers and footers, footnotes and fields travel
both ways.

To keep round trips smooth:

- Keep the original of an important document until you have compared it once.
- Use fonts the other person has, or the metric-compatible ones above.
- Send a PDF when the layout must be exact.
- Don't rely on macros, legacy `.doc` output or editing charts that came from Word.

## 7. Working together

Facthory Page is a desktop app for working with Office files on your computer. **It does not do
real-time co-editing**, and it does not join co-authoring sessions in Microsoft 365. Send files
as above, or use track changes and comments to review.

To write together, use [Facthory's workspace](https://facthory.com), where your team's projects
and docs live and are edited together. Opening and saving files directly in Facthory projects is
planned.

## 8. Automation: CLI and MCP

Every button in Facthory Page is a command that scripts and AI agents can run.

- **Command line** (`facthorypage-cli`): convert, inspect and edit documents without a window.

  ```sh
  facthorypage-cli convert report.docx report.pdf     # also odt, rtf, html, md, tex, txt, png
  facthorypage-cli text report.docx                   # plain text
  facthorypage-cli run --script job.json              # run commands, then save to .docx and .pdf
  ```

- **MCP server** for local AI agents, headless or connected to the window you are looking at:

  ```sh
  claude mcp add facthory-page -- facthorypage-cli mcp
  facthorypage --control 7981 &   # then let the agent drive the open app:
  claude mcp add facthory-page-app -- facthorypage-cli mcp --connect 127.0.0.1:7981
  ```

  Keep an agent to chosen folders with `--automation-read-root DIR --automation-write-root DIR`,
  and name it with `--author "…"` so its tracked changes are labelled.

Where the CLI is: on Linux the `.deb` and `.rpm` install `facthorypage-cli` on your `PATH` (the
`.tar.gz` has it in `bin/`); on Windows it is in `C:\Program Files\Facthory Page\` (add that folder
to `PATH` to call it by name); on macOS it is inside the app,
`/Applications/Facthory Page.app/Contents/MacOS/facthorypage-cli`, and also a separate download,
`facthorypage-cli-<version>-macos-universal.zip`. Details:
[docs/mcp.md](https://github.com/FACTHORYAI/page/blob/main/docs/mcp.md).

## 9. Getting help

- **Help › Help and Feedback** in the app, or [open an issue on
  GitHub](https://github.com/FACTHORYAI/page/issues). Search first; someone may have hit it too.
- Attach the log file: `~/.config/facthorypage/logs/` on Linux,
  `~/Library/Application Support/Facthory Page/logs/` on macOS, `%APPDATA%\Facthory Page\logs\` on
  Windows. Logs never contain your document's text.
- Never attach a confidential document to a public issue; describe it or make a small sample.

## FAQ

**Is it really free?** Yes. Facthory Page is open source under MIT or Apache-2.0, with no
subscription and no paid tier.

**Do I need an account?** No. Nothing to sign in to.

**Does it send my documents anywhere?** No. It works offline and has no telemetry or crash
reporting. Spelling and grammar run on your computer.

**Can I use it next to Microsoft Office?** Yes. Installing it changes none of your defaults.

**Will my documents look exactly the same?** Most will look the same or very close. Page breaks
can differ, mainly in documents set in Aptos (see sections 4 and 5).

**Can I run my macros?** No. Macros are preserved in `.docm` files but not run.

**Can several people edit one document at the same time?** Not in Facthory Page. Use Facthory's
workspace for that (section 7).

**How do I update?** Facthory Page checks for a new version once a day, downloads it in the
background and installs it when you quit (or right away with **Restart now**); your settings are
kept. Linux `.deb` and `.rpm` installs update with your package manager.

**Does it run on a phone or tablet?** Not at the moment.

---

Microsoft, Microsoft Office, Microsoft 365 and Word are trademarks of the Microsoft group of
companies. Facthory Page is not affiliated with, sponsored or endorsed by Microsoft. Facthory Page
is published by Bandpey GmbH.
