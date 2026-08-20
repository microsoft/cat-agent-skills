# Breathing Room

Some weeks you can feel the density before you can name it. Six meetings a day, no window between them, mail going out at 22:00, and a Saturday that quietly turned into a working day. By the time it is obvious, the week is already gone.

Breathing Room reports that in numbers, from your own calendar and what you actually send. It tells you where the room is, where it is not, and which meetings are the most movable when there is one worth moving. Then it stops.

It is a mirror on rhythm, not a productivity tool. It never rates your output, never tells you to work more or less, and there is no "you should" anywhere in what it writes.

## Using it

Nothing to set up and nothing to configure. Once the skill is imported into Scout, ask for it in plain language:

- "how does today look", "where are my gaps" - the day ahead
- "how was my week", "how did last week go" - the week just past
- "what does next week look like", "am I filling up" - the days still to come
- "what can I move", "help me free up Thursday" - what could be reclaimed

It answers in the language you write in. To have it arrive on its own rather than waiting to be asked, see [Running on a schedule](#running-on-a-schedule).

## Three scopes

**`today`** looks at the day ahead and names slots. A five-hour back-to-back run is a fact you can act on this morning, so this scope is precise and imperative.

**`week`** looks back over one to four weeks. It is descriptive and numeric, names almost nothing, and carries at most one suggestion. Recurrence is required here: one mail at 22:00 is nothing, three evenings out of five is a pattern.

**`ahead`** looks three to ten days out, while declining is still possible. This is the scope that earns the skill its place. The other two describe what already happened.

## Recommendations

It is called Breathing Room, so when a day or a coming week is genuinely overloaded it does not just report it - it points to where the room could be reclaimed: the most movable meetings, each with why it can move (you are not the organiser, it is tentative, several invitees never replied, no agenda, a recurring series). It answers the same question on request too - "what can I move", "free up Thursday", "what could I decline". What it will not do is nag: a normal day gets no suggestions, the weekend is a trend with none, and there is never a "you should" - it names what is movable and why, and the decision stays yours.

## What it will not do

**It reports on you and nobody else.** Every signal comes from the calendar and sent items of the person running it. There is no mode, no setting and no phrasing that makes it look at a colleague or a team. Ask it how loaded someone else is and it will decline. This is a boundary in the instructions, not a preference.

**It says nothing about health.** No sleep, no stress, no fatigue, no advice. A calendar shows density, not a state of mind, and inferring one from the other would be both wrong and unwelcome.

**It never acts.** It does not decline, move, create or send anything. It reports; you decide.

## Only what you emit

Receiving forty emails on a Sunday says nothing about your own boundary. Sending one at 23:00 does.

So the skill counts meetings you organise or accepted, mail you sent, and Teams threads you started. It never counts inbound volume, unread anything, or meetings you declined. That single rule is what keeps it a mirror rather than a report on how busy other people are being at you.

## Three things it gets right that are easy to get wrong

**Most calendar hours are not load.** On a real calendar, all-day markers and free-marked events came to roughly two thirds of raw event hours. An out-of-office block spanning a week is not 120 hours of meetings. Everything is filtered before anything is counted: all-day, free, cancelled, and anything you declined. Skip that step and every number is wrong by a factor of three, which is worse than having no numbers at all.

**"Movable" has to be argued.** A suggestion that just says "move this meeting" is a calendar reminder. So each one carries its reason: you are not the organiser, the event is marked tentative, three of six invitees never responded, there is no agenda, it is a recurring series rather than a one-off. Note what is absent from that list: whether attendees were marked optional. That field is not available in the data, so the skill does not claim it. An invented justification is worse than a thinner one.

**Every observation carries a number.** "+38% versus your four-week average" does work that "you have been busy" never will. A finding with no number does not ship.

## The quiet-day line

`today` is gated. When the day is unremarkable you get exactly one line with a number and no suggestion, and nothing else.

That line exists because of a platform constraint rather than a design choice, and it is worth being straight about it. The intended behaviour was complete silence on a normal day, on the principle that silence is what gives weight to the days the skill does speak. In practice a scheduled run notifies you whether or not it wrote anything, and a notification that opens on nothing is the most irritating outcome available: it spends the interruption and returns nothing. One line with a number at least pays for it.

## Staying bearable for more than a week

This is what usually decides whether something like this survives, so it is deliberate rather than incidental.

At most two observations on a day, four on a week; beyond that they are ranked and cut. The same suggestion is never repeated on the same slot within a week. A suggestion ignored three times running snoozes itself for four weeks and **says so**, because a rule that goes quiet without announcing it reads as a bug. And weekend activity is reported as a trend with no suggestion attached: there is nothing useful to propose there, and proposing something anyway would be preachy.

## Time off

Leave is treated as leave, not as a quiet week. A day off is recognised and never flagged - there is no lunch window to protect on a day you are not working - and a coming week that is mostly time off is named as such rather than read as suspiciously light. Leave weeks are also kept out of the four-week average, so the first week back reads as the normal week it is instead of looking overloaded against a baseline that your holiday dragged down.

## What it stores

Almost nothing. The four-week baseline is recomputed from your calendar on every run rather than stored, which means it works on the first run and stays correct after two weeks of leave.

The only persisted state is what cannot be recomputed: which suggestions were made and whether they were followed, which rules are snoozed, and four settings.

```json
{
  "config": { "workStart": "09:00", "workEnd": "18:30", "workDays": [1,2,3,4,5],
              "sources": { "calendar": true, "mail": true, "teams": true } },
  "suggestions": [ { "ruleId": "lunch_gap", "date": "2026-07-24", "action": "move 12:30 sync", "outcome": "ignored" } ],
  "snoozed": { "weekend_activity": "2026-08-24" }
}
```

Four settings, sane defaults, nothing to configure before first use. Every additional setting is a user lost.

## What it looks like

`today`, gate fired:

```
Breathing Room - Monday

5h20 back-to-back, 9:00 to 14:20, no gap over 10 minutes.
No lunch window today.

- "Oltiva storyboard review" (11:00-11:30) is the most movable:
  you are not the organiser and 3 of 6 invitees have not responded
- Otherwise 15:30-16:15 is your only real gap - 45 min, still free
```

`today`, gate not fired:

```
Nothing worth flagging - 4h10 of meetings, two blocks over 45 min, lunch clear.
```

`week`:

```
Breathing Room - week of July 20

Meetings: 26h30, +38% vs your 4-week average.
Deep work blocks over 45 min: 3 this week, 7 on average.

Evening sends 4 days out of 5 (after 18:30, 11 emails, 6 Teams threads).
Wednesday and Thursday both past 22:00.

Two weekends out of the last four had sent activity.

Next week is already at 22h of meetings with 3 days still open.
```

Four findings, which is the ceiling: load, fragmentation, evenings, weekends. The closing line comes from `ahead`, folded into the weekly note by the automation, and does not count against the four.

`ahead`:

```
Breathing Room - looking ahead

Week of August 3 is already at 24h of meetings against a typical 22h week, with 2 days still open.
Thursday is the densest: 6 meetings, 3 marked tentative.

- "Partner weekly" (Thu 15:00-16:00) is the most movable: recurring series, no agenda, and you are not the organiser
```

On an overloaded coming week `ahead` points to the most movable meetings, as above. On a normal week it says nothing, because there is no room problem to solve - it shows where the room is, and never tells you what to decline.

## Language

The output follows the language you write in. The structure never changes, only the words. Two things are never translated: meeting titles and people's names, which come straight from your calendar and become unfindable if reworded, and the time format, which follows your locale.

## Permissions

Calendar access is required. Mail and Teams only feed the evening and weekend signal in the weekly report, and either can be turned off in `sources`. Nothing else is needed, and nothing outside your own calendar and sent items is ever read.

The skill never writes to your calendar or your mailbox, never sends, moves or declines anything. It may run a short computation over the data it just fetched, because five weeks of overlapping events is arithmetic and doing it in prose is where numbers drift. The only thing it keeps between runs is the small state above.

## Running on a schedule

It works on demand, but the point of a mirror is that it catches you before the week is gone, so it is built to run on its own. Ask Scout for it in plain language - "have Breathing Room run every morning", "send me the weekly one on Friday" - and it creates the automation for you.

There are two, and they are independent:

- **Morning check**, on working days, early enough to land before your first meeting. It stays quiet unless the day is genuinely dense: an unremarkable morning gets one line with a number and nothing else.
- **End of week**, once a week. This one always lands, including to tell you the week was quiet, and the coming week is folded into it while there is still time to act.

If you only want one, start with the weekly. It always produces something, so its first run actually shows you what the skill does.

Both are created disabled, deliberately. Run each once by hand, look at what it produces, then enable it yourself. Keep the Teams notification on: the report *is* the run output, so the notification is the only thing that surfaces it. Neither automation writes to your calendar, and neither ever looks at anyone but you.

## Config reference

| Setting | Default | What it changes |
|---|---|---|
| `workStart` | `09:00` | Before this counts as outside hours |
| `workEnd` | `18:30` | After this counts as outside hours |
| `workDays` | `[1,2,3,4,5]` | Days not listed count as non-working |
| `sources` | all on | Turn off any of calendar, mail, Teams |

Ask for a change in plain language, for example "my day ends at 17:30" or "stop looking at Teams".
