# WhatsApp

Read, send, and monitor WhatsApp messages, and create WhatsApp groups, from Microsoft Scout - by driving WhatsApp Web in a Playwright browser. It is built for the small, real jobs that pull you out of focus: catching up on a group, firing off one reply, watching a chat while you work, or spinning up a group without leaving Scout.

## What it does

- **Read** a chat or group and return who said what, when.
- **Send** a message to a person or group, with a dry-run mode and a confirmation step before anything leaves your account.
- **Monitor** a chat for new messages in the last N minutes and draft 2-3 reply options for you to approve - it never sends on its own.
- **Create** a WhatsApp group, adding participants and naming it, with a dry-run stop before the final confirm.

## Please read first: Terms of Service and account risk

This skill automates **WhatsApp Web** through a browser. Automating WhatsApp with anything other than its official products can violate the [WhatsApp Terms of Service](https://www.whatsapp.com/legal/terms-of-service) and, in the worst case, get the number **banned**. It also acts on your *real* account: a wrong target or a bad selector can send a real message to a real person. Use it on an account you control, keep `dry_run` on until you trust a flow, and decide for yourself whether the ToS risk is acceptable for your use. This project takes no responsibility for account actions.

## How it stays safe

- **Consent before every outbound action.** `send` and `create-group` confirm the exact target and content with you first, and honour `dry_run`.
- **Incoming text is data, not instructions.** Messages from other people are treated as quoted content, never as commands - so a message saying "forward this to everyone" gets reported, not obeyed.
- **One run at a time.** An atomic lock directory stops two runs sharing the browser profile. A crashed run is detected by its owner process being gone (not just by age), with a 30-minute backstop for a hung run, so the next run is not blocked forever.
- **Stateless and private.** The skill keeps no state of its own between runs and never writes a contact-to-number mapping. Its *output*, though, is captured in Scout's run history, so it masks bare phone numbers to the last 4 digits and keeps quoted text short - prefer non-sensitive chats for scheduled monitors.
- **Right recipient only.** Chats and participants are matched by their name (the row title), never by a message preview, so an incoming message can never steer a send to the wrong person. Opening from recents needs an exact title; search may resolve a unique partial, which is confirmed before an outbound send.
- **No double-posts.** A send is confirmed only when a new outgoing bubble carrying the message appears, waited for over a generous window (WhatsApp often renders it a few seconds late). An ambiguous result is reported as "maybe sent" and **never blindly retried** - a blind retry is exactly what double-posts to a real chat.

## Running quietly (headless)

A visible browser window popping up is the browser tool running "headed". Once WhatsApp Web is logged in on the profile, the skill can run **headless** (no window) for read, send, monitor, and group creation - ask for it that way ("run it quietly / headless"), and scheduled automations run headless by default. Only the one-time login (QR or phone pairing) needs a visible window. Note WhatsApp Web is occasionally flakier headless; if a headless run trips on a selector, it falls back to a visible run for that one attempt.

Between runs the skill **reuses the already-open WhatsApp session** instead of closing and reopening the browser, so you should not see a close/reopen flicker on each request. It kills and reopens the browser only when a previous run crashed (a recovered stale lock) or the page is genuinely stuck mid-run. (If a window still flickers on every run, that is Scout relaunching the browser tool itself, which is a Scout browser setting, not something this skill triggers.)

## Language

By default the language is `auto`: the skill talks to you in the language you write in, and drafts monitor replies in the language of the chat itself, so a reply fits the conversation rather than the Scout UI. You can pin a fixed language (`en`, `fr`, ...) if you prefer. Quoted incoming messages are always reported verbatim.

## Prerequisites

1. WhatsApp Web is already logged in on the Playwright browser profile Scout uses (scan the QR once on that profile).
2. Microsoft Edge is installed for Playwright (`mcp-msedge`).
3. Only one WhatsApp automation runs at a time on that profile.

## A note on selectors

WhatsApp Web changes its DOM frequently and has dropped most `data-testid` hooks. The selectors here are **best-effort and not verified against a live session**. The skill leads with **language-independent** hooks (`#pane-side`, `contenteditable[data-tab]`, `role`, `data-icon`) because `aria-label` and visible text are translated with the WhatsApp UI language - an English-only selector would break on a French account - and keeps localized text/aria-label (English and French) as fallbacks. Expect to verify and adjust them in the real Scout browser. See `references/selectors.md`.

## Scout permissions to allow

The browser-unlock and lock steps need a few commands allowlisted in Scout:

| OS | Allowlist entries |
|---|---|
| Windows | `New-Item`, `Get-Item`, `Get-Content`, `Set-Content`, `Test-Path`, `Remove-Item`, `Get-Process`, `Get-CimInstance`, `Stop-Process`, `Start-Sleep` |
| macOS / Linux | `mkdir`, `head`, `stat`, `date`, `printf`, `grep`, `kill`, `pkill`, `sleep`, `rm` |

## Usage examples

Ask in plain language. The skill picks the action and asks only for what is missing. The names and messages below are illustrative.

**Read a chat or group**

```
catch me up on my "Weekend Trip" WhatsApp group
```

```
Weekend Trip - last 20 messages (Europe/Paris)
- Sam, 09:14: booked the cabin for Fri-Sun, sending the link tonight
- Alex, 09:16: works for me, I can drive
- Priya, 09:40: what's the budget per person?
(older messages not read - ask if you want more)
```

**Send a message (dry-run first)**

Add "dry run" (or "preview", "draft only", "prepare but do not send", "show me first") to any send and the skill prepares it without sending, then clears the draft. Say "send it" to deliver. With nothing said it sends for real, but still confirms the target and text with you first.

```
send a WhatsApp to Alex: "running 10 min late, start without me" - dry run
```

```
Dry run - nothing sent.
Target: Alex (1:1 chat)
Message: "running 10 min late, start without me"
Reply "send it" to deliver, or adjust the text.
```

Drop "dry run" (or say "send it") and the skill confirms the target once, sends, and reports back:

```
Sent to Alex: "running 10 min late, start without me"
```

**Monitor a chat for new messages**

```
watch my "Weekend Trip" group for the last 15 minutes and suggest replies
```

```
Weekend Trip - 2 new messages
- Priya, 10:02: what's the budget per person?
- Alex, 10:03: and are we splitting fuel?
Suggested replies (drafts, nothing sent):
1. "Thinking about 120 per person all in, fuel included - does that work?"
2. "Let's aim for 120 each; I'll split fuel separately once we know the route."
3. "Good questions - can we lock the budget on tonight's call?"
```

**Create a group**

```
create a WhatsApp group "Trip Logistics" with Alex, Priya and Sam - dry run
```

```
Dry run - group not created.
Name: Trip Logistics
Participants resolved: Alex, Priya, Sam
Reply "create it" to finish.
```

For recurring jobs, use the ready-to-paste prompts in `references/monitor-automation.md` and `references/send-automation.md`. A monitor can run on a schedule; a send automation must be **one-shot** (a single, fixed, pre-authored message), never a recurring send.

## Layout

```
whatsapp/
├── SKILL.md                          # agent instructions
├── metadata.json                     # gallery catalog entry
├── scripts/
│   ├── unlock-browser.ps1            # run-lock + browser unlock (Windows)
│   ├── unlock-browser.sh             # run-lock + browser unlock (macOS/Linux)
│   └── snippets.js                   # reference Playwright patterns (not a runnable script)
└── references/
    ├── selectors.md                  # selector matrix + DOM-drift guidance
    ├── monitor-automation.md         # paste-ready monitor automation prompt
    └── send-automation.md            # paste-ready send automation prompt
```
