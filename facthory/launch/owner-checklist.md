# Owner checklist: Microsoft Store listings for Facthory Page, Grid and Deck (W9)

Draft for W9, 2026-10-25. Steps are in order; a step starts when the ones it depends on are done. Each step says who can do it:

- **Owner**: only the owner (or someone the owner authorises at Bandpey GmbH) can do it: accounts, identity checks, legal declarations, money, publishing.
- **Counsel**: needs a lawyer's sign-off.
- **Claude**: Claude can prepare or do it in the repositories, without contacting anyone or creating accounts.

Nothing in this checklist has been done yet. No account was created, nothing was filed or posted.

## Step 0. Decisions before starting (Owner, Counsel)

| # | Decision | Recommendation |
| - | -------- | -------------- |
| 0.1 | Are the names cleared? | **Wait for counsel.** The W0 clearance search must clear "Facthory Page" against Apple's PAGES (same goods: word processing software), and the pending opposition against the FACTHORY application could force a rename of all three apps. A Store name reservation creates no trademark right; Microsoft warns that "using a trademarked name could lead to your app being removed from the Store, forcing you to rename and re-submit" ([reserve a name](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/reserve-your-apps-name)). Reserve only after counsel's sign-off |
| 0.2 | Which apps go first? | **Page and Grid first, Deck after its beta blockers** (closing discards edits without asking, storytold/deckcraft#60; startup crashes on some Windows GPUs; no printing). Microsoft's guidance is "Submit your app only when it's finished" ([certification](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/app-certification-process)). Details in [Facthory Deck's listing](https://github.com/FACTHORYAI/deck/blob/main/facthory/store/listing.md) |
| 0.3 | Ship before the in-app updater (W4)? | **No.** The Store never updates MSI apps for existing users ([update page](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/publish-update-to-your-app-on-store)), so Store installs made before W4 would stay on their first version. The plan already puts W9 after W4 |
| 0.4 | Is "early release" acceptable in a public store? | Upstream rates the apps at about 50–60 % ready for real work; W7 waits for W6's "ready" bar. The listings state their limits honestly (Policy 10.1.1 asks for "any important limitations"). Submitting before W6 means Store customers meet the gaps the listings describe, and the reviews will say so |
| 0.5 | Which code-signing identity? | **Azure Artifact Signing**, confirmed on the first MSI by Partner Center's pre-check, with an OV certificate as the fallback. See step 4 |
| 0.6 | Publisher name | **Bandpey GmbH** everywhere: Partner Center publisher display name, MSI `Manufacturer`, certificate subject, DSA trader name (§14.6) |

## Step 1. Partner Center company account (Owner)

1. **Check for an existing account first.** §14.5 says Bandpey GmbH already holds "the Windows signing accounts". If Bandpey has a Partner Center account (for example from hardware or driver signing), add the Windows and Xbox apps program to it instead of opening a second account.
2. Otherwise start at **https://storedeveloper.microsoft.com**, choose **Company account**. There is **no registration fee** for either account type in this flow, and it is the only supported entry point for new company onboarding ([open a developer account](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account), updated 2026-07-17). An individual account cannot be converted to a company account later.
3. Sign in with a **Microsoft Entra ID work account** of Bandpey's tenant (recommended: the whole tenant is onboarded and the signer becomes Owner; others get roles later) or a Microsoft account that belongs to the company.
4. Business details: the **D-U-N-S number** (step 2) or an official business document.
5. Contact details:
   - **Email for verification**: an individual's work email on the company's domain. No Gmail or similar, no group alias or distribution list, no plus-addressing; Microsoft sends a one-time password. If the email domain does not match the company's records, Microsoft asks for a domain registration record or invoice that shows the entity. Make sure the registrant of the domain (facthory.com or Bandpey's own domain) is **Bandpey GmbH**.
   - **Support contact for the Store listing**: see step 3.
6. Accept the App Developer Agreement.
7. Verification runs in this order: mandatory due diligence (blocking), then business and employment verification. Each completes automatically within a minute or goes to manual review, which "typically take[s] 2–5 business days"; each type allows up to three appeals. Changing the company name, address or email domain afterwards restarts verification.
8. After it completes: **Publish to Store** → Partner Center → Apps and games. Note the **Seller ID** (Account settings): Artifact Signing's identity validation asks for it (step 4).

Claude prepares: a one-page sheet of the exact values to type (legal name, address, register number, emails, phone), once the owner provides them.

## Step 2. Business verification for the EU Digital Services Act (Owner)

Microsoft's "Know Your Business Customer" check for company accounts implements the DSA's trader rules: a trader "must submit either their DUNS ID or one form of a recognized business verification document" ([company account verification](https://learn.microsoft.com/en-us/windows/apps/publish/store-business-verification-reqs), updated 2026-03-09). Accounts without it have been blocked from editing apps since 17 February 2025.

- **D-U-N-S (recommended, fastest).** Bandpey GmbH is enrolled in the Apple Developer Program as an organization, which also uses a D-U-N-S number: reuse that number if Apple's enrollment used one.
- **Or documents.** Primary: certificate of registration or formation documents, for a GmbH a current extract from the commercial register (Handelsregisterauszug) with the register website shown. Every document must be issued within the past 12 months; if the primary document is older, add a secondary one (bank or utility letter, register extract, tax certificate, D-U-N-S certification). Reviews by OneVet "may take significantly longer" than a D-U-N-S number.
- Where: Partner Center → Account settings → Legal info → **Developer** tab → Contact info → Update → **Additional Information for Verification**. Then check **EU Digital Service Act compliance status** on the same page.
- Partner Center account details (entity name, address, domain) must match the documents.

## Step 3. Trader and customer contact details (Owner)

Partner Center → Account settings → Legal info → Developer → **Contact Information for Customers**, and each app's Properties page → Support info → **Contact details** (phone and address, "required for business/company accounts").

| Field | Value (company details only, never personal ones) |
| ----- | ------------------------------------------------- |
| Trader name | Bandpey GmbH |
| Registered address | [street and number], [postcode] München, Germany |
| Support phone | [+49 … company line; a number with voicemail is acceptable] |
| Support email | [support@facthory.com; a company mailbox. The apps already show this address (`brand.toml`), so it must exist and be read] |
| Website | `https://facthory.com` (must begin with `https://`) |
| Trade register and number | Amtsgericht München, HRB [number] |

**What becomes public.** The DSA (Regulation (EU) 2022/2065, Art. 30(1) and 30(7)) requires the store to collect the trader's name, address, telephone number and email, ID, payment account, trade register and number, and a self-certification, and to show to EU customers the **name, address, phone number and email**, the **trade register and registration number**, and the **self-certification**, at least where the product is presented ([Art. 30](https://www.eu-digital-services-act.com/Digital_Services_Act_Article_30.html)). Microsoft's Policy 10.14 says company accounts' "customer support contact information … will be displayed on your product's Product Detail Page (PDP) in certain regions", and every product page carries the self-certification "This seller has certified that it will only offer products or services that comply with all applicable laws." Microsoft's FAQ: "a phone number, physical address and email are required", and suggests a P.O. box, a voicemail number or an email alias with an automatic reply for developers who do not want to publish their own (the same page also accepts a registered agent's address). The app-level phone and address fields are "generally not displayed" and serve regulatory and dispute purposes, including France's consumer-protection rules ([support info](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/support-info)).

Use the **same** details in Partner Center, the privacy policy, the website's Impressum and Apple's trader details.

## Step 4. Code signing (Owner holds the identity; Claude wires the pipeline)

Policy 10.2.9: the MSI and every PE file in it must be signed "with a code signing certificate that chains up to a certificate issued by a Certificate Authority (CA) that is part of the Microsoft Trusted Root Program". Microsoft does not re-sign MSI/EXE submissions. The pipeline (`packaging/windows/sign.ps1`, `facthory-release.yml`) already accepts either a `.pfx` certificate or Azure Trusted Signing secrets, and refuses to build a tagged release unsigned.

| Option | Cost and effort | Store acceptance | Fit |
| ------ | --------------- | ---------------- | --- |
| **A. Azure Artifact Signing** (formerly Trusted Signing), Public Trust | About $9.99 a month; a **paid** Azure subscription (free, trial and sponsored subscriptions are refused); organization identity validation in the Azure portal, 1–20 business days, documents issued within 12 months, primary email on a domain the company owns, a representative's ID check; available to organizations in the EU ([quickstart](https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart), [code signing options](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)) | **Meets the policy as written**: its root, "Microsoft Identity Verification Root Certificate Authority 2020", is listed as **Included**, with the Code Signing EKU, in the Trusted Root Program's CCADB report (downloaded 2026-10-25). The identity-validation form even has a "Seller ID" field that "applies only to Microsoft Store customers". **But** no Microsoft page says in so many words that Artifact Signing certificates are accepted for Store MSI submissions, and the "Code signing options" table marks Artifact Signing "Store eligible ❌", while marking OV and EV certificates the same way although those are exactly what Store MSIs need; the column reads as "is this a Store distribution path", not as a certificate rule | Best fit: the certificate names the validated legal entity (no custom CN or O, so it says **Bandpey GmbH**), no hardware token, CI-friendly, already wired. Certificates live three days, so every signature is timestamped (the pipeline does) |
| **B. OV certificate** from a public CA (DigiCert, Sectigo, GlobalSign …) | $150–300 a year; the private key must sit on an HSM or a cloud key service (CA/Browser Forum, since June 2023) | Unambiguous: the CA is in the Trusted Root Program | Fallback if the pre-check rejects A |
| C. SignPath Foundation (free for open source) | Free, with eligibility review | CA-issued | **Not suitable**: the certificate is issued to the foundation, so the publisher would not read "Bandpey GmbH" |

Order of work:
1. **Owner**: A, chosen. Done 2026-10-31: the Artifact Signing account `bandpey-signing` (West Europe) and the Public organization identity validation (with the Seller ID), In Progress at Microsoft. Next, once it is Completed: the Public Trust certificate profile `bandpey-public`, and the app registration `office-signing` with the "Artifact Signing Certificate Profile Signer" role on it and a GitHub federated credential for each repository's environment `release` (owner guide, P3 part 2 and P11).
2. **Owner**: put the secrets into the `release` environment (`bandpey-hq/github-infra`): `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_SIGNING_ENDPOINT` (`https://weu.codesigning.azure.net`), `AZURE_SIGNING_ACCOUNT` (`bandpey-signing`), `AZURE_CERT_PROFILE` (`bandpey-public`). No client secret: the release job signs in to Azure with GitHub's OIDC token (owner's rule, 2026-10-31).
3. **Claude**: the signing client package that `sign.ps1` downloads is pinned by upstream itself since WordCraft v0.11.0 (`Microsoft.Trusted.Signing.Client` 1.0.95, by SHA-256; see `signing-day.md`); add the Store preflight job (signature of every PE inside the MSI), and run Partner Center's package pre-check result back into this checklist (`msi-requirements.md`, rows 4–6).

SmartScreen reputation builds over time with either option; the Store install itself shows no SmartScreen prompt, and since the upstream catch-up (WordCraft v0.12.0) the MSI installs for the current account without UAC unless the person chooses an installation for everyone.

## Step 5. Reserve the three names (Owner, after counsel)

Partner Center → Apps and games → **New product** → **EXE or MSI app** → enter the name → **Check availability** → **Reserve product name**. One product per app: `Facthory Page`, `Facthory Grid`, `Facthory Deck`.

- A reservation lapses if it is not used within **three months**: reserve when submission is less than three months away.
- Several names can be reserved per product; the final one is picked at submission. Names may not contain marketing or descriptive text (Policy 10.1.1), so a fallback such as "Facthory Page – Documents" (§14.6, for Apple) is a counsel question here too.
- If a name is blocked by another developer's unused reservation and we hold the rights, Microsoft takes reports through its infringement form (linked on the reservation page).
- Renaming after launch is possible (reserve the new name; submit packages whose product name matches), but links and reviews stay with the product, not the name.

## Step 6. Hosting the MSIs (Claude prepares; a person publishes each release)

- Each signed release is drafted by `facthory-release.yml` as a GitHub release `v<version>` and published by a person after checking it (that workflow's own rule). The Store URL is `https://github.com/FACTHORYAI/<app>/releases/download/v<version>/facthory<app>-<version>-windows-<x64|arm64>.msi`.
- **Claude**: prepare the change that turns on GitHub **immutable releases** for the three repositories through `bandpey-hq/github-infra`, so a published installer can never be replaced (Policy 10.2.9: "The binary associated with that URL must not change after submission").
- **Claude**: add release workflows to Grid and Deck (done: #5 in each, 2026-10-25).
- Never delete a release whose URL is in a live or pending submission.

## Step 7. Web pages (Owner publishes; Claude drafts)

Before submitting, these must be live, because the listing, the installer and certification link to them ("make sure that your app does not contain … links to web pages that are under construction"):

- `https://facthory.com/page`, `/grid`, `/deck` (Website field; the installer's "About" link). **To publish.**
- `https://facthory.com/privacy/apps` with the text of `privacy-policy.md`, in English and German. **To publish.** (Partner Center also accepts the policy text pasted in, if the page is late.)
- An Impressum on facthory.com.
- The `support@facthory.com` mailbox, monitored.

## Step 8. Submissions, one per app (Owner submits; Claude prepares everything)

Partner Center → the product → **Start submission**. Partner Center gives every user on the account full rights over EXE and MSI apps ("The roles and permissions set for account users do not currently apply to EXE or MSI apps"), so add users sparingly.

| Section | What to enter | Prepared in |
| ------- | ------------- | ----------- |
| Availability | Markets: all; Discoverability: available in the Microsoft Store; Pricing: **Free** | — |
| Properties | Category Productivity; secondary category Business; support info (privacy URL, website, support contact); contact details (step 3); "accesses personal information": **Yes**; declarations: none ticked (no drivers or services, no accessibility claim yet, no pen claim, **no generative AI**); system requirements; notes for certification | `listing-<app>.md` |
| Age ratings | IARC questionnaire | `age-rating.md` |
| Packages | Two packages (x64, ARM64): versioned URL, architecture, app type MSI, language en-us; then **Run** package validation and fix anything it reports | `listing-<app>.md`, `msi-requirements.md` |
| Store listings | English (United States): product name, description, features, screenshots, 1:1 box art, short description, search terms, copyright, applicable license terms, developed by. Partner Center can export a CSV template; Claude can fill it for import | `listing-<app>.md` |

**Claude** prepares: final listing text, the filled CSV, screenshots and logos rendered from the branded builds, the notes for certification with the date, and the package URLs.

## Step 9. Certification (Microsoft; Owner answers)

Up to three business days per submission; a failure comes by email with a report naming the test or policy. Fix, then submit again. Once published, the listing appears in about 15 minutes. Microsoft spot-checks published apps later. Questions on a report: reply to the report email or `reportapp@microsoft.com`.

## Step 10. After launch (mostly Claude)

- **Updates.** The Store does not update existing installs; the in-app updater does. Update the Store submission's package URLs on a slower rhythm than upstream's releases (for example weekly) so new Store customers start close to the latest version. **Claude** can automate this with the MSI/EXE [submission API](https://learn.microsoft.com/en-us/windows/apps/publish/store-submission-api) once the **owner** creates a Microsoft Entra application, adds it to Partner Center with the Manager role, and stores its tenant id, client id, secret and the seller id as secrets.
- **Keep declarations true.** Before W5 (Facthory sign-in, the agent inside documents, project sync) ships in the Windows build: update the privacy policy, retake the IARC questionnaire (Policy 11.11.2), and tick the generative-AI declaration if the agent writes into documents.
- **Watch** Partner Center's install and health reports: Policy 10.4.4 says MSI/EXE products "must not have an unreasonably low installation success rate".
- **Sunsetting**: if an app is ever withdrawn, Policy 10.4.3 requires notice on the product page.

## Open questions for the owner

1. Has counsel cleared the three names (W0, Apple's PAGES, the FACTHORY opposition)? Until then, no reservation.
2. Does Bandpey GmbH already have a Partner Center account (from Windows signing), and which "Windows signing account" does §14.5 mean: Artifact Signing or a CA certificate?
3. Which D-U-N-S number did the Apple organization enrollment use?
4. Company address, support phone, support and privacy email, commercial register number for the DSA details, the privacy policy and the Impressum.
5. Deck with the other two, or after its beta blockers?
6. Wait for W6's "ready" bar before the first submission (the plan's W7 does), or list as early releases sooner?
7. Update checks on or off by default (W4)? The privacy policy's legal-basis sentence depends on it.
8. Who publishes each GitHub release (the release workflow requires a person), and may Claude automate Store package updates through the submission API?
