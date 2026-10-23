# Missed-Meeting Recovery

A **condition-triggered** Scout automation that catches you up after a meeting
you skipped.

**Trigger:** Scout checks every 15 minutes whether you missed or declined a
calendar meeting. It runs once when the condition is met.

For each meeting missed in the last 24 hours it:

1. Gathers the best available recap source: transcript, then meeting chat, then
   event details.
2. Summarizes decisions, outcomes, and open questions.
3. Extracts only the action items **assigned to you**, each with a confidence
   level and the supporting quote.
4. Returns a brief ordered by recency, ending with a consolidated checklist.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar and meeting
  transcripts/chats (for example through the WorkIQ connector).
- Transcripts only exist for meetings that were recorded or transcribed.
- The automation imports **disabled**. Review it, then enable it.
