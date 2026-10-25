# Privacy policy: Facthory Page, Facthory Grid and Facthory Deck

Draft for W9, 2026-10-25, for counsel's review. Text in [square brackets] is a placeholder. The policy itself runs from "Privacy policy for the Facthory desktop apps" to "Changes to this policy"; the drafting notes at the end are for the owner and are not published.

---

# Privacy policy for the Facthory desktop apps

**Version of [date of publication]**

This policy covers the desktop apps **Facthory Page** (documents), **Facthory Grid** (spreadsheets) and **Facthory Deck** (presentations), including their command-line tools and their MCP servers, on Windows, macOS and Linux, however you got them: from facthory.com, from GitHub or from the Microsoft Store.

It does not cover the facthory.com website, Facthory's online services, GitHub or the Microsoft Store. Each has its own privacy policy.

## The short version

- The apps work on your computer and work fully offline.
- There is no account, no sign-in, no telemetry, no usage statistics, no crash reporting, no advertising and no tracking.
- Your documents, workbooks and presentations stay on your computer. The apps do not send them to us or to anyone else.
- The only connection the apps make on their own is the **update check**, once a day. It tells GitHub which version you have and, when it downloads an update, for which platform; nothing else.
- We, Bandpey GmbH, receive no personal data from the apps. We only receive what you send us yourself, for example when you email us.

## Who is responsible

The controller under the EU General Data Protection Regulation (GDPR) is:

Bandpey GmbH
[Street and number]
[Postcode] München
Germany

Commercial register: Amtsgericht München, HRB [number]
Managing director(s): [name(s)]
Email: [privacy@facthory.com]
Phone: [+49 …]

[Data protection officer: [name and contact], or: We have not appointed a data protection officer because the law does not require one for us. For privacy questions, write to the email address above.]

## What stays on your computer

The apps store the following on your computer only. We have no access to it.

| What | Why | Where on Windows |
| ---- | --- | ---------------- |
| Your files | You create, open and save them | Wherever you choose |
| Settings, such as interface language, theme and the author name you enter in the options | To remember your choices | `%APPDATA%\Facthory Page`, `%APPDATA%\Facthory Grid`, `%APPDATA%\Facthory Deck` |
| The list of recently opened files | To show it on the start page | Same folder |
| Recovery copies of unsaved work (Facthory Page and Facthory Deck) | So you do not lose work after a crash. Facthory Page makes no plain-text recovery copy of password-protected documents | Same folder |
| Log files | To help find the cause of a problem. Logs record technical events and errors, not your work; Facthory Page never writes document text into its log. Logs can contain file names, folder paths and error messages about a file. The apps keep the last three logs, each at most 16 MiB | `logs` in the same folder |
| A key file for the automation channel, only while you run an app with the control channel turned on | So that only programs you start can drive the app | Same folder, deleted when the app closes |

On macOS the folder is `~/Library/Application Support/Facthory Page` (and likewise for Grid and Deck); on Linux it is `~/.config/facthorypage` (and likewise), with Facthory Deck's recovery copies in `~/.local/share/facthorydeck/recovery`.

**The author name you enter** in the options is written into comments and tracked changes in files you save, as other office apps do. The apps also write document properties, such as the app's name, into saved files. You can see and change document properties in the File menu.

**Deleting it.** Uninstalling an app removes the program. Your settings, recent-file list, recovery copies and logs stay in the folder above until you delete that folder. Your own files are never touched.

## Connections the apps make

### Update check

Once a day the app asks `github.com/FACTHORYAI/<app>/releases` (where `<app>` is `page`, `grid` or `deck`) whether a newer version exists. The request carries the app version, nothing else. Like every connection to a website, it also reaches GitHub with your device's IP address and standard technical information about the connection; GitHub needs these to answer.

If a newer version exists, the app downloads it from the same GitHub release, which names your platform in the file it asks for, and installs it when you quit the app. Copies that update another way (Linux packages, portable copies) only show a link to the release.

- **Who processes this:** GitHub, Inc., USA, a subsidiary of Microsoft, under GitHub's own privacy statement. We do not receive your IP address or any information about individual requests. GitHub shows us only the total number of downloads of each release file.
- **Why:** so you get security fixes and improvements.
- **Legal basis:** our legitimate interest in keeping the apps secure and working (Art. 6(1)(f) GDPR). Update checks are on by default.
- **Your choice:** you can turn update checks off at any time: set `"enabled": false` in the file `update.json` in the app's settings folder, or the environment variable `FACTHORY_UPDATES=off` (for managed installations). "Skip this version" in the update notice skips one version. The apps work fully without update checks.


### Links you click

When you click a link in a document, workbook or presentation, the app asks your operating system to open it in your default web browser. From then on the browser and the website you visit process data under their own privacy policies.

### Help and problem reports

The "Help and feedback" and "Report a problem" commands open our public issue tracker on GitHub in your browser. Anything you post there is public and is processed by GitHub under its privacy statement. Do not post personal data, confidential documents or log files you have not checked; logs can contain file names and folder paths.

### Connections that stay on your computer

- **Automation (all three apps).** The command-line tools and their MCP servers let scripts and AI agents that you run yourself drive the apps. The MCP server talks to the program that started it over standard input and output. The optional control channel listens only on your own computer (address 127.0.0.1), only when you start an app with it, and only accepts programs that present the key from the key file.
- **Zotero (Facthory Page).** If you use the Zotero buttons, Facthory Page talks to the Zotero desktop app on your computer (127.0.0.1, port 23116).
- **Operating-system services.** Printing, fonts, spelling dictionaries you installed and Read Aloud (Facthory Page) use your operating system's own services on your computer. The apps do not send your text anywhere for this.

### AI agents and scripts you connect

No AI is built into the apps. If you connect an AI agent or another program to an app through its MCP server or command-line tool, that program can read and change your files. What it does with them, for example sending them to an online AI service, is decided by you and that program's provider under their terms, not by us. We do not receive anything from such programs.

## Where you got the app

If you install an app from the Microsoft Store, Microsoft processes data about your Store account and the installation under Microsoft's privacy statement. Microsoft may give us aggregated statistics, such as the number of installs per country, that do not identify you. If you download an app from GitHub, GitHub processes the download under its privacy statement. If you download it from facthory.com, the website's privacy policy applies.

## When you contact us

If you email us at [support@facthory.com] or [privacy@facthory.com], or call us, we process your name, contact details and what you write, to answer you. The legal basis is our legitimate interest in answering enquiries (Art. 6(1)(f) GDPR), or steps towards or under a contract with you (Art. 6(1)(b) GDPR) if your request is about one. We delete your messages when your request is settled, unless the law requires us to keep them longer (for example commercial and tax retention periods of six or ten years under German law, where they apply).

## What we do not do

We do not sell personal data, show advertising, build profiles, or make automated decisions about you. The apps contain no third-party analytics, advertising or tracking code.

## Children

The apps are general-purpose office apps. They collect no personal data from anyone, including children.

## Your rights

Under the GDPR you have the right to access the personal data we hold about you (Art. 15), to have it corrected (Art. 16) or erased (Art. 17), to restrict its processing (Art. 18), to receive it in a portable format (Art. 20), and to object to processing based on our legitimate interest (Art. 21). Where processing is based on your consent, you can withdraw it at any time with effect for the future. Because the apps send us no data, in most cases we hold nothing about you unless you contacted us.

To use these rights, write to [privacy@facthory.com] or to the postal address above.

You also have the right to lodge a complaint with a data protection supervisory authority, in particular in the EU member state where you live or work. The authority responsible for us is the Bayerisches Landesamt für Datenschutzaufsicht (BayLDA), Ansbach, Germany, www.lda.bayern.de.

## Security

We sign the installers so that you can check they come from us and were not altered. The apps keep your data on your computer; protecting that computer and your files is up to you and your operating system.

## Changes to this policy

We change this policy before we change what the apps do with data, for example before adding a Facthory sign-in or online features, and we update the version date above. The app stores carry a link to the current version.

---

## Drafting notes for the owner (do not publish)

1. **Where it lives.** One page for all three apps, proposed at `https://facthory.com/privacy/apps` (to publish), linked from each Microsoft Store listing, each app's About box and the website. If the page is not live in time, Partner Center also accepts the policy text pasted directly ([support info](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/support-info)). Publish a German version as well: the company and many users are in Germany.
2. **Why a policy at all.** Store Policy 10.5.1 requires one for every Win32 product, which "inherently" has access to personal information, and asks the policy to say what is accessed, collected or transmitted, how it is used, stored and secured, to whom it is disclosed, the user's controls and how to access their information ([store-policies](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies)). Each of those is answered above.
3. **The updater as built (W4, FACTHORYAI/page#5).** Update checks are on by default, once a day. The feed request's only identifying content is the user agent `facthory-update/<version>`; the download names the platform's file. W4 must never add an install id, a user id or anything else to these requests. Turning checks off is a settings file or an environment variable today; if counsel wants a switch in the app's options for the objection right, that is a follow-up in the apps. The IP address sentence is there because GDPR treats an IP address as personal data and GitHub necessarily sees it.
4. **Facts checked in the code on 2026-10-25.** No telemetry or crash reporting (`facthory/README.md` in each app: "WordCraft has none"); Page never logs document text (`page/README.md`, Logs; Grid and Deck document no such rule, so the policy promises it for Page only, and W2 could add the rule and a test to Grid and Deck); log rotation and the 16 MiB cap (all three READMEs); control channel bound to 127.0.0.1 with a key file (`apps/*/src/control_server.rs`); Zotero on 127.0.0.1:23116 (`page/crates/zotero/src/wire.rs`); Read Aloud through the operating system's speech program (`page/crates/engine/src/speech.rs`); links limited to http, https and mailto in Grid (`grid/crates/engine/src/links.rs`); the default author name and the options field (`page/crates/engine/src/session.rs`); recovery copies (`page/docs/recovery.md`; Deck `crates/engine/src/recovery.rs`). Settings folders follow the brand tokens (`WordCraft` → `Facthory Page`, `wordcraft` → `facthorypage`).
5. **Things that would make this policy wrong.** Re-check before every release that adds any of these: W5 (Facthory sign-in, the agent link, project sync: account identifiers and document content go to the user's cell, so new sections and new legal bases are needed); an upstream AI assistant (Page has open upstream pull requests storytold/wordcraft#178 and storytold/wordcraft#815); Grid's `IMAGE()` fetching URLs; online pictures, templates or fonts; any crash reporter. Upstream merges arrive daily (W3), so the brand check could also guard against new network code.
6. **GitHub's role.** Described as an independent provider (GitHub serves public files under its own terms; we get only aggregate download counts). Counsel to confirm this characterisation and whether a transfer statement is needed for the update check.
7. **Contact data.** The support email and phone used here must match the "Contact Information for Customers" in Partner Center and the DSA trader details (`owner-checklist.md` step 3). `support@facthory.com` is the address the brand patch set already writes into the apps (`brand.toml`: `wordcraft@storyteller.ai` → `support@facthory.com`), so that mailbox must exist and be monitored.
8. **Website.** The website needs its own privacy policy and an Impressum (§ 5 Digitale-Dienste-Gesetz, DDG); neither is covered here.
