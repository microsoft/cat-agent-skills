# Prompt to Set Agenda

A Scout meeting-readiness assistant.

**Runs:** every weekday at 8:00 AM, with a Teams notification on each run.

For every non-cancelled meeting in the next 48 hours it prepares an agenda
package:

- Context summary and one-sentence objective
- 3-7 prioritized topics with time allocations and suggested owners
- Decisions that should be made in the meeting
- Recommended pre-reads
- Expected outcomes with next-step placeholders (owner and due date)

It uses chat and thread context to infer topics. It produces
recommendations only: it does not send messages or modify meetings.

## Before you enable it

- Scout needs access to your Microsoft 365 calendar, mail, and Teams (for
  example through the WorkIQ connector).
- The automation imports **disabled**. Review it, then enable it.
