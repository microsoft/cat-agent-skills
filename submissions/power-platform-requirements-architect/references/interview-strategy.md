# Requirements elicitation

This is the core of the skill. Everything else — the schema, the work items, the handoff — is bookkeeping for what happens here.

The difference between junior and senior requirements work is not thoroughness. A junior analyst can produce a longer document. The difference is **what gets asked**: whether the request is taken at face value, whether the unsaid is noticed, whether consequences are traced, and whether the person leaves the conversation understanding their own process better than when they arrived.

## Contents
- [Get behind the request](#get-behind-the-request)
- [Find what wasn't said](#find-what-wasnt-said)
- [Make requirements falsifiable](#make-requirements-falsifiable)
- [Trace consequences out loud](#trace-consequences-out-loud)
- [Separate the process from its current implementation](#separate-the-process-from-its-current-implementation)
- [Find the unowned decision](#find-the-unowned-decision)
- [Scope discipline](#scope-discipline)
- [Stakeholders](#stakeholders)
- [Mechanics: sequencing and batching](#mechanics-sequencing-and-batching)
- [When someone doesn't know](#when-someone-doesnt-know)
- [Knowing when to stop](#knowing-when-to-stop)
- [Anti-patterns](#anti-patterns)

---

## Get behind the request

People arrive with a solution, not a problem. "I need an app with these eight fields" is already a design, made by someone who was not in a position to make it. Taking it at face value is the single most common way requirements work fails.

Ask what happens today. Ask what it costs. Then ask what the eight fields are *for*.

> "I need a dropdown with all departments."
> — What happens with the department once it's picked?
> "The approval goes to that department's manager."
>
> The requirement is *routing an approval to the right manager*. The dropdown is one implementation, and probably the wrong one — a lookup to a maintained org structure survives a reorganisation; a hardcoded dropdown does not.

This is not pedantry. The dropdown version breaks in six months and nobody remembers why it was built that way.

Two questions that usually open this up:

- **"What happens today, step by step, including when it goes wrong?"** The workaround people have already built reveals the actual constraints better than any wishlist.
- **"If this existed and worked perfectly, what would be different on a Tuesday?"** Concrete, and it separates real outcomes from vague improvement.

## Find what wasn't said

What people describe is the happy path on a normal day. What breaks a solution lives everywhere else. Probe these deliberately, because nobody volunteers them:

- **The absent person.** Who approves when the approver is on holiday? Who can see the record when its owner leaves the company?
- **The stuck record.** What happens to something submitted and then forgotten? Does anyone notice? Whose job is it?
- **The correction.** Someone entered it wrong. Who fixes it, and does the fix need a trace?
- **The exception volume.** Not "how many inspections a month" but "how many go wrong, and what happens to those". Exception handling is usually most of the build effort and almost never in the initial description.
- **The edges of the calendar.** Month-end, year-end, holidays, the shutdown week. Working-day arithmetic and cutover problems hide here.
- **The other user.** The night shift, the external contractor, the works council, the auditor. Someone who wasn't in the room but will use or inspect this.
- **The in-flight records at go-live.** What happens to the things half-finished on the day you switch? This gets forgotten with remarkable reliability and hurts every time.
- **The thing mentioned once.** When someone says "oh, and it needs to work on the shop floor tablets" as an aside, stop and dig. Off-hand constraints are frequently the ones that reshape the architecture.

## Make requirements falsifiable

A requirement you cannot fail is not a requirement. Convert every soft word into something observable, and do it in the conversation rather than silently in the document.

| Said | Ask |
|---|---|
| "fast" | How fast, on what device, with how much data in it, and what happens if it's slower? |
| "real-time" | Sub-second and synchronous, seconds and eventual, or a nightly batch? Three different architectures. |
| "secure" | Who must not see what, and what is the consequence if they do? |
| "user-friendly" | Compared to what they do today, and who decides it's met? |
| "reliable" | What happens on failure, who finds out, and how quickly? |
| "flexible" | Which part do you expect to change, and how often? |
| "everyone" | Everyone in the department, the company, or the tenant? Including externals? |
| "automatically" | Triggered by what, and can it be wrong? |

"Real-time" deserves special attention. It is the requirement most often accepted unexamined, and the one that most often makes a design impossible to build cheaply.

## Trace consequences out loud

Senior work means following a requirement two steps forward and reporting what you find — in the conversation, before it reaches a document.

> "Only the person who created the record may see it."
> — Then their manager can't cover while they're off, and support can't investigate a complaint. Is that what you want, or should there be a role that sees everything?

> "We need seven years of history for the audit."
> — That's roughly 2.8 million rows at your volume, plus the photos. It changes the platform choice and the capacity, so let's confirm the seven years is a real obligation and not a habit.

> "The manager approves everything over 5,000 euro."
> — Who approves when the manager submitted it themselves?

This is where the value is. Anyone can write down "only the owner may see it". Noticing that it breaks holiday cover is the job.

## Separate the process from its current implementation

The Excel file's columns are not the data model. They are one person's compromise, shaped by Excel's limits, with three columns that exist because of a report cancelled in 2022.

Ask which fields are actually used, which are ever filled in, which get recomputed by hand each month, and which exist "because they've always been there". Then model the process, not the spreadsheet.

The same applies to a legacy system being replaced: its screens encode decisions made under constraints that no longer apply. Reproducing them faithfully is how you build a worse version of a system people already dislike.

## Find the unowned decision

"Who decides that?" is one of the most productive questions available, and it is rarely asked.

When two requirements conflict, or a rule has no clear rationale, or a threshold is asserted without a source — there is usually a decision nobody owns. Naming it is more useful than resolving it yourself, because your resolution has no authority and will be reversed later by someone who does.

Record the name. "Legal and Finance disagree on visibility; Head of Compliance decides by 14 March" is a real project artifact. "Compromise: managers see aggregate data only", invented by you, is not.

## Scope discipline

Most requests contain more than needs building, and the person often knows it but hasn't been given permission to say so.

- **Name the value concentration.** "You've described six capabilities. Two of them — capture and escalation — look like most of the benefit. Would shipping those first be useful, or is it all-or-nothing?"
- **Offer the deferral explicitly.** People find it much easier to say "yes, phase two" than to volunteer a cut.
- **Push back on the loud-but-marginal.** The feature someone is most enthusiastic about is not always the one that matters. Say so kindly, and with a reason.
- **Get "out of scope" written down.** An exclusion nobody recorded reappears as a surprise expectation at go-live.

Scope reduction is a service, not an obstacle. Deliver it that way.

## Stakeholders

- **The loudest voice is often not the primary user.** The person commissioning this may never use it. Ask who touches it daily, and get to them.
- **Tag who said what.** When answers come from several people, record the source. It matters when they conflict later.
- **Don't average a disagreement.** State both positions, name the practical consequence of each, ask who decides.
- **Watch for the missing party.** Works council, data protection, the team that owns the source system, the auditor. Someone whose approval will be needed and who hasn't been asked.

## Mechanics: sequencing and batching

Work outside-in, because later answers depend on earlier ones:

1. Problem, current process, and who actually uses it
2. The main journey, its status model, decision points
3. Exceptions and the unsaid (above)
4. Data: entities, volumes, who sees what
5. Rules, and where each must be enforced
6. Automation and integration, including failure behavior
7. App surface, devices, offline
8. Architecture decisions, presented as a set for confirmation
9. Acceptance criteria, priorities, exclusions

Never ask about theme colours while the status model is undefined. Structural questions early, cosmetic questions late or not at all.

**Three to seven questions per turn**, fewer for non-technical audiences. Group related sub-questions into one numbered item. One concrete question per item. Give a short reason only where the relevance isn't obvious.

Ask nothing already in the conversation, the attachments, or inferable from what you've been told. Re-asking is the fastest way to lose credibility, and it signals you weren't listening.

## When someone doesn't know

Common, and fine. In order of preference:

1. **Find out yourself** if the answer is discoverable.
2. **Propose a default with its consequence**, marked visibly as an assumption. "I'll assume the approver's manager is the escalation path — say the word if it's someone else."
3. **Escalate it as an open item with a named owner.** Some answers genuinely live with someone who isn't in the room.

What not to do: rephrase the same question a third time, or quietly adopt the convenient answer.

## Knowing when to stop

Diminishing returns are real. Stop asking when the remaining unknowns are noncritical, or when further precision would cost more than the risk it removes.

Signals you've gone too far: one-word answers, "just build something", visible impatience. Recovery is always the same — summarise what you have, name the two or three things you genuinely cannot proceed without, offer sensible defaults for the rest, ask for a single confirmation.

A document with documented assumptions ships. A perfect interview that exhausted the stakeholder does not.

## Anti-patterns

- **Transcribing instead of interviewing.** Writing down what you were told, in the order you were told it, adding nothing.
- **Accepting a solution as a requirement.** See the top of this file.
- **Inventing a business rule** because the gap was awkward. The most damaging failure available here — a fabricated rule gets implemented faithfully and nobody knows it was never real.
- **Resolving a conflict silently** in favour of whichever reading is easier to build.
- **The questionnaire.** Forty questions in one message, answered badly or not at all.
- **Cargo-culting the checklist.** Reciting coverage domains at someone instead of asking about their actual process.
- **Confusing volume of document with quality of thinking.** A 700-line document restating a 20-line problem is a failure, not diligence.
- **Deferring every judgement to the user.** They own the business rules. You own the analysis, the consequences, and the recommendation. Handing all three back is abdication.
