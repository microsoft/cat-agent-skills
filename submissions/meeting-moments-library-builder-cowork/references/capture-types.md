# What do you want to capture? (ask this FIRST)

The machinery in this skill is **type-agnostic**. It scans meetings you choose, verifies a
moment in the transcript, deep-links to that moment, stores it in your list, and serves it
through an agent and (optionally) a website. Nothing about that pipeline is specific to
"how-tos" — that is just the most common preset.

So **before** creating storage or writing config, ask the user what kind of moments this
library should capture. Getting this right up front shapes the criteria, the title format,
the categories, the agent persona, and the website copy. Retrofitting it later means
re-scanning and re-titling everything.

## Ask it like this

Offer the presets below as concrete choices, plus "something else". Keep it to one
question — do not interrogate the user. Example framing:

> "Before we build it: what kind of moments do you want to capture from your meetings?"

Then confirm the derived vocabulary in one line before proceeding, e.g.
*"So: a **Decision Log** — each entry is a decision, titled 'Decision: <what was decided>'.
Sound right?"*

If the user already said what they want ("a how-to library", "I want to capture customer
objections"), **skip the question** and just confirm the derived vocabulary.

## Presets

Each preset fills `capture` in `library-config.json`. All of them still obey the core
rules: a real recording link, a verified transcript timestamp, and a short clip.

### 1. How-to library *(default)*
Reusable demos and walkthroughs.
- `itemNoun`: how-to · `titleFormat`: `How to <do the specific task>`
- **Include:** step-by-step demos, build/config walkthroughs, troubleshooting with a clear
  resolution, reusable patterns, templates, prompts, agent techniques.
- **Exclude:** status updates, roadmap talk, strategy/brainstorming with no repeatable steps.
- **Quality bar:** someone can watch it and immediately repeat the task.
- **Categories:** by tooling or capability area.

### 2. Decision log
Why a call was made, straight from the room.
- `itemNoun`: decision · `titleFormat`: `Decision: <what was decided>`
- **Include:** a decision being made, the options weighed, the rationale, who owns it, and
  any explicit trade-off or reversal criteria.
- **Exclude:** open questions with no resolution, informal opinions, decisions already
  documented in writing elsewhere.
- **Quality bar:** someone joining later understands *why*, not just *what*.
- **Categories:** by workstream, product area, or decision type.

### 3. Customer voice
What customers actually said, unfiltered.
- `itemNoun`: customer insight · `titleFormat`: `<Customer/segment>: <the insight>`
- **Include:** direct customer quotes, pain points, objections, feature requests,
  competitive mentions, reactions to a demo.
- **Exclude:** internal speculation about customers, anything under NDA or otherwise
  restricted, and anything the customer asked not to be recorded.
- **Quality bar:** it's the customer's own words, with enough context to be actionable.
- **Categories:** by theme, product area, or segment.
- ⚠️ **Extra care:** confirm sharing is permitted before capturing external-customer
  content, and respect the skill's default of excluding external-customer meetings.

### 4. Demo highlights
The moments worth showing again.
- `itemNoun`: demo moment · `titleFormat`: `<Product/feature>: <what it shows>`
- **Include:** a feature working end to end, a striking before/after, a wow moment, a crisp
  explanation of value.
- **Exclude:** broken or caveated demos, anything under embargo, long unedited walkthroughs.
- **Quality bar:** it stands alone in a customer or exec conversation.
- **Categories:** by product or feature area.

### 5. Lessons learned
What went wrong, and what you'd do differently.
- `itemNoun`: lesson · `titleFormat`: `Lesson: <what we learned>`
- **Include:** retro insights, post-incident findings, a specific misstep with its fix, a
  process change and why.
- **Exclude:** blame, individual performance discussion, anything identifying a person
  negatively.
- **Quality bar:** a team hitting the same situation would act differently after watching.
- **Categories:** by phase, workstream, or theme.

### 6. Onboarding moments
The context new joiners always ask for.
- `itemNoun`: onboarding clip · `titleFormat`: `<Topic>: <what a new joiner learns>`
- **Include:** how a system or team works, who owns what, the origin of a convention,
  walkthroughs of core tools and process.
- **Exclude:** anything version-specific enough to go stale within a quarter, confidential
  material a new joiner wouldn't have access to.
- **Quality bar:** it answers a question new joiners genuinely repeat.
- **Categories:** by system, team, or onboarding week.

### 7. Something else (custom)
If none fit, build the vocabulary with the user. You need:
- **`itemNoun` / `itemNounPlural`** — what one entry is called.
- **`titleFormat`** — a consistent title shape.
- **`criteria.definition`** — one sentence on what qualifies.
- **`criteria.include` / `criteria.exclude`** — concrete examples of each.
- **`criteria.qualityBar`** — how a viewer should be better off after watching.
- **`categories`** — the buckets that make sense for this content.

Do not invent these silently — draft them, show the user, and adjust.

## Where it lands in config

```json
"capture": {
  "type": "how-to",
  "itemNoun": "how-to",
  "itemNounPlural": "how-tos",
  "fallbackCategory": "Other How-Tos",
  "criteria": {
    "definition": "...",
    "include": ["..."],
    "exclude": ["..."],
    "requiredEvidence": ["recording link", "verified transcript timestamp", "presenter",
                         "one-line outcome", "duration under maxClipMinutes"],
    "titleFormat": "How to <do the specific task>",
    "audience": "...",
    "qualityBar": "..."
  }
}
```

`capture.criteria` is what the weekly scan filters on, what the agent applies when someone
submits an entry, and what you use to reject a candidate. `itemNounPlural` and
`fallbackCategory` drive the website and agent wording so nothing says "how-to" in a
decision log.

## Mixing types

Prefer **one type per library** — the criteria stay sharp and the agent's persona stays
coherent. If a team genuinely wants two (say how-tos *and* decisions), either run two
libraries over the same meetings, or use a single library with categories per type and
widen `criteria` to cover both. Say which trade-off you're making rather than blurring it.
