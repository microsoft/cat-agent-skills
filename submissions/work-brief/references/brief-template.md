# Brief template

Use this structure. Consistency matters more than completeness - the user scans the same shape every morning and learns where to look.

## Structure

```
# [Period] brief - [date]

[Coverage line: one line - sources, lookback range, look-ahead range, timezone, and any source that failed or was partial. Exact format below.]

## Before your next meetings
[Only items where an upcoming meeting creates a deadline the user has not noticed.
 Each: the meeting, when, and what the user owes before it, with the source thread.]

## You owe people
[owed-by-user items. Each: the ask, who asked, age, deadline stated or implied,
 and the single next step.]

## Waiting on others
[owed-by-other items. Each: what, who owns it, how long, whether already chased.]

## Hot topics
[Top N. One short paragraph each: what it is, why it is live, which sources it spans.]

## Week ahead
[Schedule table, one row per day. Then a short flags list: conflicts (which
 meetings clash and when), agenda-less meetings above the threshold, unanswered
 or tentative invites, notable 1:1s. Do not repeat the same flag in every row.]

## Do first
[Ordered list. Each line: the action, why now, and the source.]

## Worth a look
[Only if present: suspicious items, or anything that could not be classified.]
```

"Before your next meetings" leads because it is the only section with a hard deadline attached. If it is empty, drop it and lead with "You owe people".

Drop any section with no content, except "You owe people" and "Do first". If those are genuinely empty, say so explicitly. Silence reads as failure.

## Item lines

Every item in "Before your next meetings", "You owe people", and "Waiting on others" uses the same shape, so the eye lands in the same place each morning:

`**[Counterpart or subject]** - [the ask, in the source's words]; [age]; [deadline stated as X, or implied, not stated]; next: [the single next step]. ([source: thread subject, chat name, or meeting title])`

Keep each item to one or two lines. Drop a field that genuinely does not apply rather than padding it, but never drop the source.

## Rendering

**Schedule view.** One row per day: the date, then that day's meetings in start-time order with duration and attendee count. Keep the flag cell to a short marker and put the detail in the flags list under the table, so the same "double-booked" text is not repeated down every row. Prefix or colour by type using the config mapping: internal, client, 1:1, focus, personal.

**Adaptive card.** In `teams-self-chat` and `email` modes the brief may render as an adaptive card: a title with the coverage line as subtitle, one container per section with a bold header, and the schedule as a day-to-blocks fact list rather than a wide table. If the card fails to build or render, degrade to the plain markdown structure above rather than dropping the section - adaptive rendering breaks often enough on mobile that the fallback will get used.

**Dates and weekdays.** Derive each day's weekday from its date in the anchored time zone, and list every day in the look-ahead window in order, from the run date forward. Do not skip a day or shift a weekday label by one - a row headed with the wrong weekday sends the user to the wrong day. If a day has no meetings, keep its row and mark it clear rather than dropping it.

**Length.** Readable in about two minutes. If a section runs past the configured item cap, keep the top items by the ranking rules and add a count of what was left out.

**Tone.** Plain and factual. No motivational framing, no "great week ahead". The user is scanning for problems.

**Dashes.** Write the whole brief with plain hyphens only. Never use an em dash or an en dash, in a heading, a date range, or prose - write a range as `18-24 Jul` or `18 to 24 Jul`, never with the longer dash characters. The rendered brief is read every morning, so the punctuation has to be consistent and typeable.

**People.** Plain-text names only. Never @mention.

**Language.** Write the whole brief in the resolved output language (Step 0): section headers, prose, the coverage line, weekday and month names, and the "deadline stated / implied" labels. The section names in this template are canonical English labels - translate them to the output language rather than emitting them verbatim, keeping the same order and meaning. Two things stay in their original language: material quoted from a source (an ask "in the source's words" is a quote, never a translation), and the internal classification state keys (`owed-by-user` and the rest never appear in the brief anyway). If the brief quotes a French ask inside an English brief, that is correct - the quote is evidence, not prose.

**Certainty.** Distinguish what a source states from what you inferred. Write "deadline stated as Thursday" or "deadline implied, not stated". A brief reading as more certain than its sources is worse than one that admits the gap.

**Sources.** Every line traces back to something: a thread subject, a chat name, a meeting title. A claim with no traceable source should not be in the brief.

## Coverage line

Always first, and always one line, not a paragraph. Base shape:

`Coverage: [sources] - lookback [start] to [end] - look-ahead [start] to [end] - [timezone][ - partial or failed notes]`

Use plain hyphens in the date ranges. Three cases:

- All sources read: name them, both windows, and the timezone.
- A source failed or was partial: append it to the same line, e.g. `- Teams: most-active chats only`. If a source failed entirely, lead the line with the failure and state that its section is incomplete.
- A source is disabled in config: say it is disabled rather than silently omitting it, so a misconfiguration stays visible.
