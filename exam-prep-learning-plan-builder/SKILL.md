---
name: exam-prep-learning-plan-builder
description: Build a personalized, day-by-day study plan for an upcoming exam, certification, or test. Use this skill whenever someone mentions studying for an exam, prepping for a certification, needs a study schedule, is trying to pass a test by a certain date, or asks for help organizing exam prep, even if they don't use the word "plan" explicitly (e.g. "I have my PMP in 6 weeks and don't know where to start", "help me study for the bar", "I need to prep for the AZ-900"). Also use when someone wants to revise or adjust an existing study plan because their timeline changed, they fell behind, or their confidence in a topic shifted.
---

# Exam Prep Learning Plan Builder

## Compatibility

If Code Interpreter is available, populate `assets/plan-app-template.html` with the plan JSON and return it as a downloadable `.html` file. If Code Interpreter isn't available, present the plan as formatted chat text instead.

## Step 1: Gather the inputs

Before building anything, get these four things (plus preferred study time if they want calendar events). If the person hasn't given them, ask (use a lightweight elicitation tool if one is available, otherwise just ask directly in plain language):

1. **Exam date** — this sets the total runway and whether the plan needs to be in triage mode (see below).
2. **Syllabus or topic list** — the domains or chapters the exam covers. If the person doesn't have an official breakdown, help them reconstruct one from the exam's public objectives (search if you have the ability to) or ask them to list what they remember the exam covering.
3. **Weekly study time available** — realistic hours per week, not aspirational ones. If they give a number that seems very high for someone with a job or a life, gently sanity-check it rather than just taking it at face value.
4. **Self-rated confidence per topic** — ask them to rate each topic Low / Medium / High. Don't skip this step even if the person seems eager to get straight to a schedule. This is the single input that makes the plan personalized instead of generic, and it's worth the extra thirty seconds it takes them to answer.

If the person gives you a big pasted syllabus, don't ask them to rate every single sub-bullet. Group it into a sane number of topics (roughly 6-15) and have them rate at that level.

5. **Preferred study time** (optional) — a rough time of day works fine, "evenings around 7" or "lunch breaks." This only matters for the `.ics` file (see Step 4), since calendar events need an actual time, not just a date. If the person doesn't give one, default to a reasonable early-evening block (e.g. 7:00-8:00 PM) and say plainly in the plan that the times are placeholders they should adjust to fit their real schedule.

> **Note for Copilot Studio makers:** a dropdown per topic (Adaptive Card `Input.ChoiceSet`, `style: compact`, choices Low/Medium/High) is a nicer input experience than free text, but it can only render if it's wired into an actual Adaptive Card node on the topic canvas at design time, generative instructions alone can't trigger a card to render, the platform will just print the JSON as text. If you want to build that yourself, duplicate one `Input.ChoiceSet` per topic on an Adaptive Card node and route its output into this skill's flow. Otherwise, plain text works everywhere without any extra setup, and is what this skill uses by default.

## Step 2: Decide the structure

**Calculate available study sessions.** Take the weeks until the exam times the weekly hours, and convert that into a realistic number of study sessions (a session is usually 45-90 minutes; don't plan 4-hour blocks, nobody does those consistently).

**Weight topics by confidence, not just by size.** A Low-confidence topic should get roughly double the session count of a High-confidence topic covering similar material. Don't make this rigid math, use judgment, but the weighting should be visibly reflected in the plan. If someone is a 5/5 on a topic, it still deserves at least one pass, just a short one, since exams still test things people think they already know.

**Build in spaced repetition.** This is the part most study plans skip and it's the part that actually matters. Every topic should appear at least twice on the calendar, not back to back. A good pattern: first pass on the topic, then a shorter revisit 4-7 days later, then a final light touch in the last week before the exam. If the timeline is too short for this pattern on every topic, prioritize spacing for the Low-confidence topics first since those are the ones that decay fastest without reinforcement.

**Schedule practice tests at checkpoints, not just at the end.** Put at least one practice test or self-check roughly at the halfway point, so the person finds out where they actually stand while there's still time to react to it, and at least one more in the final week. A practice test that only happens two days before the exam is a diagnosis with no time to treat it.

**Triage mode.** If the exam is close (a rough guide: fewer than 10 total study sessions available), don't try to force full coverage and spaced repetition onto everything. Instead: rank topics by confidence, cut or reduce the High-confidence ones to a single light review, and spend the bulk of remaining sessions on Low-confidence topics with at least one repeat pass each if at all possible. Say plainly in the plan that this is a compressed/triage plan and what got deprioritized and why, so the person understands the tradeoff rather than being surprised by it.

## Step 3: Build the plan data

Rather than hand-writing HTML or Python for each session, this skill ships a single-file app template (`assets/plan-app-template.html`) that already contains the timeline graphic, day-by-day view with a calendar picker, domain breakdown, an in-browser `.ics` download, and a notes/confidence scratchpad, all driven off one JSON object. Your job is to build that JSON object correctly, not to write markup.

Build a JSON object matching this schema:

```json
{
  "examName": "string",
  "examDate": "YYYY-MM-DD",
  "startDate": "YYYY-MM-DD",
  "totalSessions": 0,
  "weeklyHours": 0,
  "preferredTime": "HH:MM",
  "planNote": "2-4 plain sentences on how confidence shaped the schedule, where the practice tests fall, and whether this is a full or triage plan",
  "isTriage": false,
  "topics": [
    { "id": "slug", "name": "Display name", "confidence": "low|medium|high", "domain": "Domain or category name" }
  ],
  "sessions": [
    {
      "date": "YYYY-MM-DD",
      "topicId": "slug matching a topics[].id",
      "type": "first-pass|revisit|checkpoint|final-review",
      "title": "Short title, e.g. the topic name",
      "description": "Plain, calendar-ready description: what to study and why now, no markdown syntax",
      "durationMinutes": 60
    }
  ]
}
```

A few things that matter for the data to render correctly:

- `topics[].id` and `sessions[].topicId` must match exactly, the domain breakdown and confidence chips key off this.
- `topics[].domain` is what groups sessions in the "By Domain" tab. Use the same domain names consistently, and keep the count reasonable (roughly 3-8 domains), not one domain per topic.
- `sessions[].description` follows the same rule as before: plain sentences, no markdown, no "see above", since this text goes straight into both the day card and the `.ics` event description.
- Give checkpoint sessions a longer `durationMinutes` (90-120) than regular sessions (45-90).
- Apply the confidence weighting and spaced repetition pattern from Step 2 through the actual `sessions` array: a Low-confidence topic should have more entries than a High-confidence one, and each topic should generally appear at least twice, not back to back.

## Step 4: Populate the template and output the file

Using Code Interpreter:

1. Read `assets/plan-app-template.html`.
2. Serialize the JSON object from Step 3, then escape it for safe embedding: replace every `</` with `<\/` in the serialized string. This matters because the JSON gets embedded inside a literal `<script>` tag, if any topic name, title, or description happens to contain the literal characters `</script`, the browser's HTML parser will close that tag early before your JSON is even parsed, breaking the page (or worse, opening a second injection path upstream of the DOM-building code). The escape is safe: `\/` is a valid JSON escape for `/`, so it round-trips through `JSON.parse` correctly.
   ```python
   import json
   json_str = json.dumps(plan_data).replace("</", "<\\/")
   ```
3. Replace the placeholder token `{{PLAN_DATA_JSON}}` (inside the `<script type="application/json" id="plan-data">` tag) with the escaped string from step 2.
4. Save and return the completed file as a downloadable `.html`, named after the exam (e.g. `az-900-study-plan.html`).

Do this through Code Interpreter so it comes back as an actual file with a download link, not as raw markup printed into the chat, printing `<html>` as plain generative text won't render, the platform just shows the literal tags, same issue as trying to force an Adaptive Card to appear from text alone. If Code Interpreter isn't enabled on the agent, fall back to presenting the plan as clearly formatted chat text (day by day, grouped by week) instead of the app.

The app is self-contained: the "Download .ics" button inside it generates the calendar file client-side from the same JSON, so there's nothing extra to build or keep in sync, one file is the whole deliverable.

Tell the person plainly what they're getting: an app they can open in any browser, with a timeline overview, the full day-by-day schedule, a calendar picker to jump to a date, a breakdown of time by domain, a button to download the `.ics` for their calendar app, and a notes tab where they can log how a topic is going and copy a formatted update back into the chat if they want the plan adjusted.

## A few things to keep in mind

- Don't schedule study on every single day by default. Ask about or assume at least one rest day a week unless the person says they want daily sessions. Burnout kills consistency more than under-scheduling does.
- If someone comes back later and says they fell behind or their confidence on a topic changed (including updates copied from the app's notes tab), don't rebuild from scratch, adjust the remaining plan the same way you built it: re-weight by current confidence, re-check whether spaced repetition still fits in the remaining time, and flag if triage mode is now needed when it wasn't before. Regenerate the JSON data and re-populate the template so the app reflects the update, don't hand-edit the rendered HTML directly.
- If the person is prepping for something with no fixed public syllabus (an internal work exam, a niche cert), rely on what they tell you about the format and don't invent topics or objectives you don't have evidence for.
