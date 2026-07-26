# Communication Style Analyzer

Ever wanted an assistant to write *like you*? This skill reads a sample of your
own **Teams messages and sent emails** and distills them into a structured
profile of your writing voice — how you greet people, your tone and formality,
how long your messages run, your punctuation and emoji habits, your sign-offs,
your go-to phrases, and your quirks.

It then **saves that profile to memory**, so other skills and automations (like
an out-of-office auto-responder) can draft messages that actually sound like you.

## Before you start

- **A connected Microsoft 365 account** — the skill reads your Sent mail and your
  Teams chats via the agent's `m365_*`-style tools.
- **A host with persistent memory** (remember/recall). The profile is written to
  memory so it survives across sessions.
- Tool names vary by host; the skill describes capabilities (list emails/chats,
  read bodies, remember) rather than hard-coding a single vendor's names.

## How to use it

Just ask, e.g.:

- *"Analyze my communication style."*
- *"Build a writing-style profile I can reuse."*
- *"Capture my voice before I set up my OOO auto-reply."*

The skill gathers 20–30 sent emails and 50+ Teams messages across many different
chats, analyzes them across eight dimensions, shows you a summary table, and
saves the profile to memory. Recall it any time with a query like *"writing
style"*.

## Good to know

- **Diversity matters.** It samples across 20–25 different chats (1:1, group, and
  meeting chats; internal and external) so the profile reflects how you adapt,
  not just one relationship.
- **It captures *how*, not *what*.** The saved profile describes your style —
  greetings, cadence, phrases — not the verbatim content of private messages.
- **Nothing leaves your environment.** Analysis runs against your own M365 data
  inside your agent; no content is sent to any third party.
- **Keep it fresh.** Re-run it every few months so the profile tracks how your
  voice evolves.
- **Great as a building block.** Pair it with an OOO/auto-responder skill so
  automated replies are written in your voice.
