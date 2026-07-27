# IT Support Ticket Agent

Turns "my laptop won't turn on" or "I need access to the shared drive" into a
properly triaged, complete ticket, without making the user fill out a form.

## What it does

Asks only what's needed to triage and route the issue, assigns a priority
using a standard impact/urgency matrix, checks for a faster fix first (an
outage page, a self-service reset link), then creates the ticket if this
platform has a connector for that, or hands back a clean, ready-to-submit
draft if it doesn't.

## Honest about what it can and can't do

This skill doesn't ship its own connection to ServiceNow, Jira, or any other
ticketing system. If your Copilot Studio agent or Cowork setup has a
ticket-creation action or flow configured, this skill uses it and reports back
whatever that tool actually returns. If nothing is configured, it says so and
gives you the finished ticket text instead of pretending one was filed.

For security incidents such as a compromised account or a lost device, it
treats the situation as urgent immediately and tells you the right first
step, rather than only logging a ticket and waiting.

## Reference

`references/priority-matrix.md` has the impact/urgency matrix this skill uses,
the same shape as the defaults in ServiceNow, Jira Service Management, and
Dynamics 365 Customer Service.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
