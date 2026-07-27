# Selectors and DOM-drift guidance

WhatsApp Web is a moving target. It ships obfuscated class names, changes its DOM on most releases, and has removed the `data-testid` attributes that older automations relied on. Treat every selector here as a **starting hypothesis to verify in the live Scout browser**, not a guarantee.

## Principles

1. **Lead with language-independent hooks.** `aria-label` and visible text are translated with the WhatsApp UI language (`Chat list` becomes `Liste des discussions` in French), so an English-text selector silently matches nothing on a non-English account. Prefer things that do not change with language: the ids `#pane-side` / `#side`, `contenteditable` with `data-tab`, `role`, and `data-icon` values.
2. **Text and aria-label are fallbacks, and must list every language.** When only text or `aria-label` identifies a target, provide the English and French variants side by side. Adding a new UI language means adding its strings here.
3. **Always carry fallbacks.** For each target, try primary, then fallback 1, then fallback 2. If all miss, fail loudly naming the step - never click a "best guess" element.
4. **Wait for state, not time.** Prefer waiting for a selector to appear over fixed sleeps; keep the sleeps only as a floor for WhatsApp's animations.

## Matrix

Primary column is language-independent wherever a language-independent hook exists. The localized column lists English / French; extend it for any other UI language in use.

| Purpose | Primary (language-independent) | Fallback | Localized (EN / FR) | Notes |
|---|---|---|---|---|
| App ready / logged in | `#pane-side` | `#side` | `[aria-label="Chat list"]` / `[aria-label="Liste des discussions"]` | Wait for this (up to 120s) instead of a fixed sleep. Its absence + a QR canvas means not logged in. |
| Chat list rows | `#pane-side div[role="listitem"]` | `div[role="row"]` | visible-text match in `#pane-side` | `#pane-side` is the left list container. |
| Search input | `div[contenteditable="true"][data-tab="3"]` | `[data-icon="search"]` then its input | `[aria-label*="Search"]` / `[aria-label*="Recherch"]` | Click the search area first, then type. |
| Message composer | `div[contenteditable="true"][data-tab="10"]` | `footer div[contenteditable="true"]` | `[aria-label="Type a message"]` / `[aria-label="Tapez un message"]` | `data-tab` numbers drift across releases - verify. |
| Submit a message | press Enter in the composer | `span[data-icon="send"]` | `button[aria-label="Send"]` / `button[aria-label="Envoyer"]` | Enter is the usual submit; click the send icon only if Enter does not clear the composer. |
| Send confirmation | composer becomes empty after submit | outgoing bubble appears | last message timestamp updates | Language-independent; confirm the send actually landed. |
| Message metadata | `[data-pre-plain-text]` | `span.copyable-text[data-pre-plain-text]` | visible bubble text + timestamp | Holds `[time, date] Sender:` (locale-dependent value, but the attribute name is stable). |
| Back / recover | `span[data-icon="back"]` | press Escape | `[aria-label="Back"]` / `[aria-label="Retour"]` | Reset to the chat list when a step is stuck. |
| New chat | `[data-icon="new-chat-outline"]` | `span[data-icon="chat"]` | `[aria-label="New chat"]` / `[aria-label="Nouvelle discussion"]` | Entry point for New group. |
| Group name input | `[contenteditable="true"]` in the naming step | - | `[aria-label*="group subject" i]` / `[aria-label*="objet du groupe" i]` | Appears on the second step. |
| "Use here" dialog (text only) | `button:has-text("Use here")` | `button:has-text("Utiliser ici")` | `button:has-text("Utiliser")` | No language-independent hook; list each language. |
| No results found (text only) | `:has-text("No results found")` | `:has-text("Aucun résultat")` | empty result pane | Search/participant miss - report, never pick a different chat. |
| New group entry (text only) | menu item `New group` | menu item `Nouveau groupe` | list item under the menu | No language-independent hook; list each language. |
| Add participant | search field inside the group dialog (`[contenteditable="true"]`) | - | `[aria-label*="Search"]` / `[aria-label*="Recherch"]` | Type name, pick the matching row; detect "No results" per participant. |

## Matching a chat or participant by name

A chat row's visible text is `name + last-message preview + timestamp`. Never match a target by the row's full text: an incoming message whose preview contains the target name would rank to the top and be opened by mistake (a targeting-hijack path). Match on the **name element only** - the row's `span[title]` `title` attribute.

Opening from the recents list requires an **exact** normalised title match. Searching may resolve a **unique partial** title (you type part of a name), but if more than one title matches, stop and ask - never open a best guess. For any outbound action, confirm the resolved full title with the user before acting when it came from a partial match, since a partial can resolve to a chat they did not mean.

### Search results come in sections - count only Chats

WhatsApp search returns grouped sections, each under a short header:

- **Chats** / **Discussions** - the actual conversations. This is the only section that holds a real target chat.
- **Contacts** - address-book matches, not open chats.
- **Messages** - occurrences of the query *inside* chats. A single chat with several matching messages appears many times here; these are **not** separate chats.

Scope target resolution to the Chats section (detect the header labels, keep the listitems under Chats until the next header). Counting Messages rows is what makes one conversation look like "3 different groups". `chatSectionResults` in `scripts/snippets.js` does this best-effort by tagging chats-section rows with `data-wa-idx`.

In the **New group** dialog the participant results are a separate list, not `#pane-side` (which is the main chat list and stays visible behind the dialog). Scope participant matching to the dialog's own list and match by title, or the first row of the main chat list gets added by mistake.

## Confirming a send

Composer-clear alone does not prove a message was sent - a reconnect or "use here" takeover clears it with nothing sent. Require **both**: the composer is empty **and** a NEW `#main .message-out` bubble (count before/after; a pre-existing identical bubble is not proof) carries the sent text.

Wait a **generous window** for the new bubble - WhatsApp often renders it a few seconds late, so poll up to ~12s, not a couple of seconds. A too-short window reports `send-unconfirmed` on a message that actually went out, which is what tempts a double-send.

**`send-unconfirmed` means "maybe sent", so never auto-retry.** A blind resend double-posts. A resend needs a fresh human instruction, and even then, first fingerprint the recent outgoing bubbles by the message's exact text (`outgoingExists`) and skip the send if it is already there.

## Login: QR or phone pairing

The chat list only appears once the profile is authenticated. If it does not appear and a login screen shows, there are two setup paths (both one-time, manual - never automate them):

- **QR:** phone, Linked Devices, scan the code on this profile.
- **Phone pairing (no camera):** on the login screen choose "Link with phone number instead", enter the number, and type the 8-character code shown into WhatsApp on the phone. Useful for headless profiles.

## Opening a chat by number

`https://web.whatsapp.com/send?phone=<international-number>` opens a chat directly with a number (digits only, with country code, no `+`). Watch for the "Phone number shared via url is invalid" state and report it rather than proceeding.

## UI recovery

If a step is stuck, recover **once**: click Back / press Escape to return to the chat list, or reload `https://web.whatsapp.com` and wait for the chat list. Then retry the step. If it still fails, fail explicitly - a recovery loop hides the real break.

## Locale-dependent metadata

`data-pre-plain-text` encodes time and date in the account's locale:

- 24-hour EU: `[14:35, 26/07/2026] Alice:`
- 12-hour US: `[2:35 PM, 7/26/2026] Alice:`

Parse both the 24-hour and AM/PM time forms and both `DD/MM/YYYY` and `M/D/YYYY` date orders. If a value will not parse cleanly, return the raw string rather than emit a wrong timestamp.

## When selectors break

If a primary and its fallbacks all miss, that usually means WhatsApp changed the DOM. Fail the run with a message that names the exact step ("composer not found"), so the fix is a selector update in this file and `scripts/snippets.js`, not a silent misfire.
