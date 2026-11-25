# Intake and session design

Read this in steps 1 to 3 of the workflow.

## Contents
1. Intake: what to ask, what to infer
2. Learning objectives
3. Module structure (the five-part arc)
4. Timing rules
5. Session shapes by length
6. Format adjustments: in person, virtual, hybrid

## 1. Intake: what to ask, what to infer

Read the sources first. Then ask only what the sources cannot answer, in one message, with a default for
each question so the user can reply "defaults are fine".

| Question | Default when the user does not say | Ask when |
|---|---|---|
| Audience: who they are and their level (beginner, practitioner, expert) | Mixed practitioners, no prior training on the topic | Always, unless the request names it |
| Goal: what participants do differently afterward | Derived from the sources' main purpose | The sources serve several goals |
| Duration | 90 minutes | Always, unless stated |
| Format: in person, virtual or hybrid | Virtual | Always, unless stated |
| Group size | 12 to 20 | Exercises depend on it (breakouts, pairs) |
| Delivery constraints: tools, rooms, access, accessibility needs, language | None | The topic needs a live demo or a specific tool |
| Brand template (.pptx or .potx) | Neutral palette | Always offer; never require |
| Optional outputs: pre-read, survey, follow-up email draft, HTML page | Survey and follow-up email draft on; pre-read and HTML off | Offer once in the intake |

Never ask for facts the sources hold. Never ask a second round of questions; build on the defaults and
list them under "Assumptions" in the report.

## 2. Learning objectives

- Three to five objectives for a session up to half a day; up to eight for a full day.
- Each objective starts with an observable verb: explain, compare, map, build, decide, apply, plan,
  identify, prioritize, draft. Never "understand", "know", "learn about" or "be aware of".
- Each objective names something a facilitator can see at the end: an artifact, a decision or a short
  explanation.
- Each objective is backed by at least one source unit. An objective with no source behind it is a gap:
  drop it or flag it.
- Number them O1, O2 and so on. Every objective is covered by at least one module; every module names
  the objectives it serves.

## 3. Module structure (the five-part arc)

Build each module, and the session as a whole, on this arc. Short modules can merge parts; the order
stays.

| Part | Purpose | Typical share of a module |
|---|---|---|
| Why it matters | The problem or opportunity, in the audience's terms. One consequence or contrast. | 10% |
| Teach | One concept per slide, with the mechanics, not only definitions. Ends with what participants will do next. | 20 to 25% |
| Do it | A hands-on exercise or discussion grounded in the sources. Setup, timebox, share-back. | 40 to 50% |
| Best practices | Pitfalls with fixes, recommended practices, what good looks like. | 10 to 15% |
| Take away | Checkpoint, commitment or next step with an owner and a date. | 10% |

Rules:
- An objectives slide follows the title: "By the end of this session you will be able to".
- At least 40% of the session is hands-on or discussion. Lectures longer than 15 minutes without an
  activity are split.
- Every module except a break has at least one activity.
- A checkpoint closes each hands-on module: two or three things everyone should have done.
- The session ends with a commitment: one next step, one owner, one check date.
- Each module gets a section divider that carries its duration label.

## 4. Timing rules

- Every duration label (agenda rows, section dividers, chapter bars, exercise timeboxes) is 5, 10, 15,
  20, 30, 45 or 60 minutes. Round up: 9 becomes 10, 11 or 12 becomes 15, 23 becomes 30.
- A module longer than 60 minutes is split into two modules.
- Module minutes add up exactly to the session length. Rebalance with
  `python scripts/timing.py plan --total <T> "Module=minutes" ...`; pin fixed blocks such as lunch with
  `!` ("Lunch=45!"). It rounds down only when the total forces it and says so.
- Activity timeboxes inside a module add up to no more than the module's minutes. Leave room for the
  setup and the debrief: a 30-minute module holds a 20-minute exercise.
- A number quoted from a source ("the process takes 90 minutes today") is a fact, not a label. Keep it
  as the source says.
- Validate with `python scripts/timing.py check workshop.json`. It fails on any non-allowed label and on
  any sum that differs from `total_minutes`.

## 5. Session shapes by length

Starting points; adapt to the content. All add up exactly.

| Length | Shape |
|---|---|
| 60 min | Welcome 5, Teach 15, Exercise 20, Best practices 10, Commit 10 |
| 90 min | Welcome 10, Teach 15, Exercise 30, Break 5, Exercise 20, Commit 10 |
| 120 min | Welcome 10, Teach 20, Exercise 30, Break 10, Teach 15, Exercise 20, Commit 15 |
| Half day (240 min) | Opening 20, Teach 30, Exercise 45, Break 15, Teach 30, Exercise 60, Best practices 20, Commit 20 |
| Full day (420 min) | Opening 20, Teach 30, Exercise 45, Break 15, Teach 30, Exercise 45, Lunch 45, Teach 30, Exercise 60, Break 15, Exercise 45, Best practices 20, Commit 20 |

## 6. Format adjustments

**Virtual**
- Break every 60 to 90 minutes. No single talking block over 10 minutes.
- Use chat, polls, reactions and breakout rooms; name the tool in the activity materials.
- Prepare a shared document or whiteboard per breakout room before the session.
- Fallback for every breakout: run the activity in the main room.

**In person**
- Plan room setup (tables of four to six), wall space, sticky notes and printed exercise sheets.
- Fallback for every projected demo: a printed or slide version.

**Hybrid**
- Pair each remote participant with a room buddy or keep remote participants in their own group.
- Every activity works on a shared digital surface; the room uses the same one.
- Assign a co-facilitator to watch the chat.
