# Reschedule Declined 1:1

A **condition-triggered** Scout automation that helps you recover a one-on-one
after it is declined.

**Trigger:** Scout checks every 15 minutes for a newly declined one-on-one
meeting in your calendar or inbox responses. It runs once when the condition is
met.

For each declined 1:1 it:

1. Confirms it is a true one-on-one (organizer plus one attendee).
2. Captures the original time, duration, timezone, and whether it is recurring.
3. Checks both participants' working hours, conflicts, and out-of-office blocks.
4. Finds the **3 best replacement slots** in the next 7 business days.
5. Drafts a short message proposing those options, ready for your review.

**It never sends the message automatically.**

## Before you enable it

- Scout needs access to your Microsoft 365 calendar and mail, including the
  ability to view other attendees' availability (for example through the
  WorkIQ connector).
- The automation imports **disabled**. Review it, then enable it.
