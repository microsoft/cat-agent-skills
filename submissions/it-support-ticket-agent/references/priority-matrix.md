# Priority matrix

A standard impact x urgency matrix, the same shape most ITSM tools (ServiceNow,
Jira Service Management, Dynamics 365 Customer Service) use by default. Use it
as a starting point, not a rigid rule. Local team conventions and stated SLAs
always win over this file.

| | Urgent (blocking now) | Time-sensitive (blocking soon) | Not urgent |
| --- | --- | --- | --- |
| **Wide impact** (team or org) | P1: Critical | P2: High | P3: Medium |
| **Single user, critical function** | P2: High | P3: Medium | P4: Low |
| **Single user, has a workaround** | P3: Medium | P4: Low | P4: Low |

## Definitions

- **P1, Critical**: a system or service is down for a whole team, department,
  or the organization, with no workaround. Treat security incidents (account
  compromise, active data loss) as P1 regardless of how many people are
  affected.
- **P2, High**: a single user is fully blocked from a task that's critical to
  their role right now, or a smaller group is affected without a workaround.
- **P3, Medium**: the user is impacted but has a workaround, or the issue
  affects a non-critical function.
- **P4, Low**: cosmetic issues, how-to questions, and standard requests
  (new equipment, routine access) with no immediate deadline.

## Notes

- When impact and urgency point to different rows, ask the user rather than
  guessing. They know whether "not urgent" actually means "can wait a week"
  or "needs to happen before end of day."
- A request (new laptop, software install, access grant) is not automatically
  low priority just because it isn't a break. If it's blocking someone's start
  date or a deadline, treat it accordingly.
