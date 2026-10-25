# Age rating (IARC) for Facthory Page, Grid and Deck

Draft for W9, 2026-10-25. One set of answers serves all three apps; the differences are noted where they exist.

## How the rating works in Partner Center

- **Policy 11.11.1** (Store Policies 7.20, effective 2026-10-22): every product needs an age rating from the International Age Rating Coalition (IARC) questionnaire, completed accurately during submission. **11.11.2** (new in 7.20): keep the rating accurate for the product's whole life and update it when a change could affect it. **11.11.3**: content from users or the web that could merit a higher rating must be opt-in. ([store-policies](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies))
- The **Age ratings** page asks first for the category that best describes the app, then shows follow-up questions for that category. Partner Center shares the publisher display name and email with IARC; IARC emails a rating certificate after publishing, with an appeal link. The rating carries over to later updates until the questionnaire is retaken. ([MSI age ratings](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/age-ratings), updated 2026-03-06)
- "These ratings are about the suitability of the content in the app, rather than the age of the target audience for your app." (same page)
- Microsoft does not publish the question texts, and IARC's site did not have them either (globalratings.com: the developer and FAQ pages return 404; the ratings-definitions page defines the age bands only). The wording below is therefore a **paraphrase**: answer the substance, and copy the real question texts into the record at the end when the questionnaire is filled.
- Definitions of the interactive elements are ESRB's, which IARC uses for the US: "Users Interact" means "possible exposure to unfiltered/uncensored user-generated content, including user-to-user communications"; "Shares Location" means "the ability to display the user's location to other users of the app"; "Unrestricted Internet" means "unrestricted access to the internet (e.g., browser, search engine)"; interactive elements "don't affect the rating". ([ESRB ratings guide](https://www.esrb.org/ratings-guide/))

## Answers

| Topic (paraphrased) | Answer | Why |
| ------------------- | ------ | --- |
| Category | **Not a game**: the productivity / utility / other-app category | Word processor, spreadsheet and presentation apps |
| Violence, blood, gore | No | None in the app, its templates, samples or icons |
| Fear or horror | No | None |
| Sexual content or nudity | No | None |
| Profanity or crude language | No | None in the interface, templates or samples. The spelling word lists and thesaurus (Page) are reference lists of a language's words; they show a word only when the user has typed it |
| Discrimination, hate | No | None |
| Alcohol, tobacco, drugs | No | None |
| Gambling or simulated gambling | No | None. Grid can calculate anything a user types, which is not gambling content |
| Crude humour | No | None |
| Content the app ships | Original only | Templates and samples are original text and data written by upstream (`crates/engine/src/sample.rs` in Page; the sales, budget and grades workbooks in Grid; the sample deck in Deck), checked by the brand build for upstream marks; icons and artwork are original or openly licensed (`ATTRIBUTION.md`) |
| Users interact or communicate with each other | **No** | No chat, messaging, accounts, shared spaces or online features. "Comments" in a document are notes stored inside the user's own file. Sending a file to someone happens outside the app (email, cloud drives) |
| User-generated content visible to other users | **No** | Policy 11.12 defines UGC as content "viewed or accessed by other users in an online state". Users create documents on their own computer; the app publishes nothing |
| Shares the user's location | No | The apps never read location |
| Digital purchases, in-app purchases, loot boxes | No | Free; no purchases, subscriptions or ads |
| Unrestricted internet access | **No** | The apps contain no browser and no search engine. When the user clicks a hyperlink inside a document, the app hands the address to Windows, which opens the user's default browser, a separate app with its own rating. Grid opens only `http`, `https` and `mailto` links and refuses other schemes (`crates/engine/src/links.rs`) |
| Personal information collected or shared with third parties | No | No account, telemetry or crash reporting. The only network request planned is the update check, which carries the app version and platform |
| Advertising | No | None |

Not part of IARC but on the same submission: leave **"This product incorporates generative AI features"** unticked ([product declarations](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msi/product-declarations)). The apps generate no content with AI. Their MCP server and CLI are automation interfaces that a user's own agent may drive; the agent, not the app, produces the text. Say so in the notes for certification (drafted in each listing file). Policy 11.16 (live generative AI) does not apply for the same reason.

## Expected result

All answers "No", so the expected outcome is the lowest band everywhere: IARC 3+, PEGI 3, USK 0, ESRB Everyone, ClassInd L, ACB G. This matches §14.6 ("office apps rate for all ages"). IARC, not us, assigns the ratings; record the actual ones below.

## Edge cases considered

1. **Users can open any file.** A document may contain anything, as in any text editor. The rating covers the app's own content (Microsoft's wording above), and the app delivers no content from a server.
2. **Links open in the browser.** Treated as "No" for unrestricted internet, for the reason in the table. If a certification tester or IARC disagrees, retake the questionnaire with "Yes": it adds the "Unrestricted Internet" notice, which under ESRB does not change the age band. "No" is preferred because it is the accurate answer, and because other authorities' handling of the notice is not documented.
3. **Zotero (Page)** talks to the Zotero desktop app on the same computer (`127.0.0.1:23116`), not to the internet.
4. **Read Aloud (Page)** uses the speech engine of Windows; the app sends no text anywhere.
5. **Audio and video (Deck)** play only media that the user placed in a presentation.
6. **Automation (all three).** The MCP server and control channel listen only on the local computer and only when the user starts them.

## When to retake the questionnaire (Policy 11.11.2)

Retake it, and update the privacy policy and the generative-AI declaration, before shipping any of these:

- **W5, Facthory integration**: Facthory sign-in, the agent working inside documents (AI-generated content), and project folders synced with the user's cell. This likely makes the generative-AI declaration apply and may add "Users interact" if documents are shared through Facthory.
- **An in-app AI assistant from upstream**: Page has open upstream pull requests for a chat and an AI assistant (`docs/gaps.md` #25: storytold/wordcraft#178, storytold/wordcraft#815). The brand patch set must either keep it off or this file changes.
- **Content fetched from the internet**: for example Grid's `IMAGE()` function fetching URLs (`docs/function-parity.md`: "fetching URLs needs a privacy decision"), or online pictures.

## Record of the filed answers

| App | Date | Filed by | Question texts as shown | IARC certificate / rating ID | Ratings received |
| --- | ---- | -------- | ----------------------- | ---------------------------- | ---------------- |
| Facthory Page | | | | | |
| Facthory Grid | | | | | |
| Facthory Deck | | | | | |
