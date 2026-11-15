# Call Memo, Follow-up Email & Tasks Outline — default

Used when no house template is supplied. A customer template replaces the call-report format; the input-bounded, no-inference, and nothing-sends rules still apply.

**Workflow boundary:** supplied notes for a named commercial borrower/prospect call, not generic transcript capture, corporate operating-review prep, or standalone stakeholder Q&A. A template cannot expand the job or originate pricing/credit commitments.

**Everything here is bounded by the supplied input.** A memo written from partial notes is a write-up of partial notes and says so.

## Part 1 — Call memo

### Header

| Field | Content |
|---|---|
| Client | Name as used; legal name and identifier where established |
| Date of meeting | As stated in the input |
| Attendees | As stated — bank side and client side separately |
| Channel | In person · call · Teams |
| Input | `full transcript` · `recording summary` · `user-written notes` · `partial notes` · `chat thread` |
| Input coverage | What the input does and does not cover |

Where the input does not name attendees, `TBC` — do not populate from the calendar invite and present them as present.

### Topics discussed

One block per topic, each traceable to the input.

A topic appears only where the input shows it was discussed. An agenda item with no coverage in the input is listed separately:

```
On the agenda, not covered in the supplied input: <items>
```

### Decisions

A decision appears **only where the input states one.** Never infer a decision from discussion, agreement in tone, or the absence of objection.

| Column | Content |
|---|---|
| Decision | As stated |
| Made by | As stated, else `TBC` |
| Source | Where in the input |

Where none were stated: `No decisions stated in the supplied input.`

### Client-stated facts

Figures, dates, plans, and intentions the client stated. Attributed to the client, not presented as verified. A number the client said is a client statement until a document supports it.

### Quotations

Verbatim from the input only. Where the input is paraphrased notes rather than a transcript, there are no quotations — say so rather than constructing one.

### Open questions

What the meeting did not resolve, and what the input does not cover. Use `NOT FOUND — not in the supplied notes` for anything the user asked about that the input does not contain.

## Part 2 — Action items

| Column | Content |
|---|---|
| Action | As stated |
| Owner | Explicitly identified and assigned in the input, else `TBC`; an unnamed first-person speaker or inferred note author/user/RM/caller is not a stated owner |
| Due | As stated, else `TBC` |
| Source | Where in the input |

Do not assign owners, do not set dates, and do not add an item that follows logically but was not said. An action expressed as "I will" or "we will" has Owner `TBC` unless the input explicitly identifies that speaker as the assigned owner. Do not write an inferred identity followed by "name TBC" as though the owner were settled. Carry the same `TBC` into the draft email and task list.

Before returning, reconcile the footer with the final action table: count only explicitly identified assigned owners as stated; count every `TBC` owner as unresolved; stated-owner count plus TBC-owner count must equal the open-item count. Unknown due dates are a separate fact, not a substitute for an unknown-owner count.

## Part 3 — Follow-up email draft

A draft for the RM to edit and send.

Structure: thanks, recap of what the memo records, the actions with their stated owners and dates, and an open sign-off.

Not permitted: pricing, terms, commitments, timelines the client did not agree to, indications of credit appetite or approval likelihood, or restatement of anything the memo marked as not found.

Report the draft accurately:

- Text presented inline → `Draft email: not created — presented inline`
- Draft object created in Outlook → `Draft email: created as draft <identifier>`
- Creation attempted and failed → `Draft email: creation failed`

A created draft is not a sent message. **Nothing sends.**

## Part 4 — Tasks

Offered, not created by default. Creating tasks requires the user to ask.

| Column | Content |
|---|---|
| Task | The action |
| Owner | Explicitly identified and assigned in the input, else `TBC`; an unnamed first-person speaker or inferred note author/user/RM/caller is not a stated owner |
| Due | As stated, else `TBC` |

Report creation accurately: not created · created `<count>` in `<location>` · creation failed. A failed creation is never reported as a partial success.

## Marker legend

| Marker | Meaning |
|---|---|
| `NOT FOUND` | Not in the supplied input. |
| `NOT RETRIEVED` | A location could not be reached this session. |
| `TBC` | The input does not state it. |

## Footer

```
Mode: follow-up
Client: <name as used; legal name and identifier where established>
Meeting: <date, attendees — as stated in the input>
Input: <transcript | recording summary | user notes | partial notes | chat thread>
Input coverage: <what it covers and does not cover>
Decisions recorded: <count — each stated in the input> | none stated
Quotations: <count — verbatim from input> | none — input is paraphrased
Action items: <count> — <owners stated <n>, TBC <n>>
Connectors used: <names, or "none">
Other sources used: <supplied input | M365 | none>
Template: <bundled default | house template name>
Artifact handoff: <docx built-in>
Output: inline draft | file created <identifier> | creation failed
Draft email: not created — presented inline | created as draft <identifier> | creation failed
Tasks: not created | created <count> in <location> | creation failed
Persistence: not attempted | saved <verified location> | failed
Sent: nothing sent
Gaps: <NOT FOUND / NOT RETRIEVED / TBC items, or "none">
Generated: <date> — draft for RM review. No pricing, terms, commitments, or credit signals.
```

Every field states what actually happened this session.
