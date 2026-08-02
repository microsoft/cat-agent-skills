# Pattern Radar (Scheduled)

A Scout automation that runs **Pattern Radar** for you twice a week
(**Wednesday and Friday at 4:00 PM**) and posts a single **Teams summary** — so
the highest-leverage insights come to you without you asking.

Each run scans your recent **Microsoft 365 signals** (Inbox + Sent mail, active
chats and channels, calendar subjects) over the last 7 days and surfaces up to
three recurring patterns worth productizing:

- **Blog candidates** — things you keep explaining to different people.
- **Automation candidates** — multi-step tasks you keep doing by hand.

It's **read-only** (it never sends messages on your behalf except its own
summary) and **privacy-aware** (customers and people are always anonymized).

> Prefer to run it on demand instead of on a schedule? See the companion
> **Pattern Radar** skill, which does the same analysis interactively.

## What it does on each run

1. Recalls when it last ran (and flags if it's catching up after a gap).
2. Pulls the last 7 days of mail subjects, active chat/channel messages, and
   calendar subjects — breadth over depth.
3. Clusters them, keeping only patterns that appear **≥3 times across ≥2
   distinct people/threads/events**.
4. Posts **0–3 candidates** to Teams (or *"✅ No new patterns this run."* when
   the week is quiet), biased toward surfacing at least one automation
   opportunity.
5. Remembers the theme labels it surfaced (no private data) so it doesn't repeat
   itself next run.

## Before you import

- **A connected Microsoft 365 account** in Scout, with tools to read mail, chats,
  channels, and calendar.
- **Memory (remember/recall)** enabled — the automation tracks its last run and
  what it previously surfaced.
- The automation ships **disabled** (`enabled: false`). Review it, then enable it
  in Scout to activate the Wed/Fri schedule. Adjust the days/time to taste.

## Good to know

- **Nothing is sent on your behalf.** The only outbound action is the Teams
  summary to you; it never replies to chats, channels, or email.
- **Ruthless threshold.** One-offs are ignored; a genuinely quiet week returns
  "no new patterns" rather than manufacturing noise.
- **Anonymized by design.** Evidence reads "3 different customers", never the
  actual names; calendar specifics and file paths are kept out of the summary.
- **Tune the cadence.** Wednesday/Friday at 4 PM is just a default — change the
  schedule in Scout after import.
