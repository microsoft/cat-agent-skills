# Pattern Radar

Two of the highest-leverage questions a busy knowledge worker can ask are *"what
should I write about?"* and *"what could I automate?"* — and the answers are
usually hiding in plain sight, in the work you already did this week.

Pattern Radar scans your recent **Microsoft 365 signals** — Inbox and Sent mail,
active chats and channels, and calendar subjects — and surfaces **recurring
patterns** worth turning into leverage:

- **Blog candidates** — things you keep explaining to different people.
- **Automation candidates** — multi-step tasks you keep doing by hand.

It's **read-only** and privacy-aware: it never sends anything and never names
customers or people in its output.

> Prefer this to run on a schedule? There's a companion **Pattern Radar
> (Scheduled)** automation that posts the same digest to Teams twice a week.

## Before you start

- **A connected Microsoft 365 account** — the skill reads mail subjects, chat/
  channel messages, and calendar subjects via the agent's `m365_*`-style tools.
- Tool names vary by host; the skill describes capabilities, not one vendor's
  exact tool names.

## How to use it

Ask, e.g.:

- *"/pattern-radar"*
- *"What should I write about this week?"*
- *"Find things I could automate from my recent work."*

It looks back over the **last 7 days**, clusters your signals, and returns **0–3
candidates**. Each candidate names the theme, the anonymized evidence, whether
it's a blog or automation opportunity, and a one-line rationale (for automations,
the trigger and the action).

## Good to know

- **Ruthless threshold.** A pattern only counts if it shows up **≥3 times across
  ≥2 distinct people/chats/threads/events**. One-offs are treated as noise, so a
  quiet week honestly returns *"No new patterns."*
- **Biased toward automation.** Blog and automation candidates get equal weight,
  but when an automation candidate qualifies it's preferred — offloading
  repetitive work is usually the bigger win.
- **Sent mail is gold.** It pays special attention to what *you* send (forwards,
  intros, status pings, "looping in X" handoffs) — that's where repetitive manual
  work hides.
- **Privacy first.** Read-only, always anonymized ("3 different customers", never
  the actual names), and it skips anything you've marked private or excluded.
