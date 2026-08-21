# Copilot Adoption Analysis — framework logic

The reference the build script and the agent follow when turning the four MAC
(Microsoft admin center) Copilot activity exports into a populated dashboard.
Source: *Copilot Adoption Analysis — A suggested analytical approach & reporting
framework* (S. Borovina, July 2026). Thresholds below are the framework's
defaults and are tunable per org.

## The four reports (join key = user)

Three are per-user tables joined on the user column; the fourth is per-agent.

| # | Report (`--flag`) | Grain | Key columns the framework uses | Signature to recognise it |
|---|---|---|---|---|
| 1 | **Copilot usage** (`--usage`) | one licensed user per row | **Report Period**; **Report Refresh Date**; user key; prompts submitted; active days; overall last activity; per-app last-activity for Teams, Word, Excel, PowerPoint, Outlook, OneNote, Loop, M365 Copilot app, Edge | per-app Copilot columns incl. **Loop / OneNote**, plus prompts + active-days |
| 2 | **Agents — per user** (`--agents-user`) | one licensed user per row | user key; number of agents used; agent responses received; last activity | has **agents-used** / **agent-responses** columns |
| 3 | **Agents — per agent** (`--agents-agent`) | one agent per row | agent name; creator type; active users (licensed / unlicensed); responses sent; last activity | has an **agent-name** column + **active-users** / **creator** |
| 4 | **Copilot Chat** (`--chat`) | one user per row, **includes unlicensed** | user key; prompts submitted; active days; last activity; per-surface last-activity incl. **web chat** | has a **web-chat** surface column; the only report with unlicensed users |

The strategic hinge: Copilot Chat reaches users with no paid license. Active Chat
users who are **not** already active in licensed in-app Copilot are the
conversion pipeline (Pillar E).

## Reporting window (read from the data, never assumed)

MAC exports record the window they were generated for in a **Report Period**
column — the admin center default is **28 days** (the picker also offers 7, 30
and 90). The window drives the dashboard badge and footer ("*N*-day window") and
the per-app activity recency test, so it is resolved from the export itself:

1. An explicit `--period` flag, if the user asked for a specific window (a
   mismatch with the data is reported as a warning).
2. The **Report Period** column of the Copilot usage export.
3. The **Report Period** column of the Copilot Chat export.
4. Failing all of those, the **28-day MAC default**, with a warning.

Values may be plain (`28`) or worded (`Last 28 days`); the first integer in the
range 1–365 is taken, and the most common value wins if rows disagree. A window
outside 7/28/30/90, mixed values within one report, or two reports disagreeing
each raise a warning so the export can be checked.

The **report date** resolves the same way: `--report-date`, else the export's
**Report Refresh Date**, else today (flagged as an assumption).

## The five pillars (thresholds; tuned to the detected window)

**Pillar A — Adoption segmentation** (from Copilot usage). Each licensed user is
placed in exactly one segment using a waterfall (first match wins), where
`apps` = number of per-app columns with recent activity:

1. **Never activated** — no prompts, no active days, no activity at all.
2. **Dormant / at-risk** — had activity, but last activity **≥ 28 days** ago.
3. **Champion / power user** — active days **≥ 12** AND (prompts **≥ 60** OR apps **≥ 4**).
4. **Habitual** — active days **≥ 5** (i.e. 5–11 and not a Champion).
5. **Casual / occasional** — any remaining user with 1–4 active days.

**Pillar B — Surface breadth** (from Copilot usage). For each app, share of
licensed users with recent activity in that app = users-active-in-app ÷ assigned.
Dashboard shows the **top 10** surfaces, each carrying its user count for the
hover tooltip. Multi-surface (≥ 3 apps) users get the most value; low-share apps
(including any that come back at 0%) are the targeted-enablement candidates.

**Pillar C — Agent adoption** (from Agents per-user). Feeds the KPI only: agent
adoption rate = users with ≥ 1 agent ÷ licensed users. (Full sub-segments —
Power user ≥ 3 agents & ≥ 50 responses, Regular 1–2 & ≥ 20, Explorer 1–2 & < 20,
Non-adopter 0 — are documented for future depth but not rendered.)

**Pillar D — Agent usage share** (from Agents per-agent). For each agent,
active-user share = that agent's active users ÷ the distinct agent-active user
base (users with ≥ 1 agent, from Pillar C). Users may use several agents, so
shares need not sum to 100. Dashboard shows the **top 10** agents, each carrying
its user count for the hover tooltip.

**Pillar E — Conversion pipeline** (from Copilot Chat). Rank unlicensed,
Chat-active users by intent (Chat prompts × active days × recency), first match
wins:

- **Hot** — prompts **≥ 30** AND active days **≥ 8** AND recent (last activity ≤ 7 days).
- **Warm** — prompts **≥ 10** AND active days **≥ 3** (and not Hot).
- **Cool** — prompts **≥ 1** AND active days **≥ 1** (and not Warm/Hot).

Funnel = *Unlicensed active* (any Chat-active unlicensed user) → *Warm+*
(Hot + Warm) → *Hot*.

## KPI scorecard (the four dashboard tiles)

| KPI | Formula | Framework target |
|---|---|---|
| **License activation** | active licensed users ÷ licenses assigned | ≥ 80% |
| **Habitual-user rate** | users active on ≥ 5 days ÷ licensed users | ≥ 40% |
| **Agent adoption** | users with ≥ 1 agent ÷ licensed users | ≥ 30% |
| **Conversion-ready leads** | count of Hot + Warm unlicensed Chat leads | grow the pipeline |

"Assigned licenses" = every row in the Copilot usage export (each row is an
assigned licensed user). "Active" = a user who is not in the *Never activated*
segment.

## Dashboard data contract (what the script injects)

The template exposes one JavaScript object between `@DASHBOARD_DATA:BEGIN` and
`@DASHBOARD_DATA:END`. The script replaces that block (and the template header
comment, title, and footer note) so the output carries only real data:

```
company      string   customer / org name
logo         string   inline "data:image/…;base64,…" URI, or "" for the default mark
reportDate   string   ISO "YYYY-MM-DD" (--report-date, else Report Refresh Date, else today)
periodDays   number   MAC window read from the Report Period column: 7 | 28 | 30 | 90
                      (--period overrides; 28 assumed only if the column is absent)
sources      { usage, agentsUser, agentsAgent, chat } booleans — false → related panel shows "pending"
kpis         { activation:float, activationSub:"1,240 of 1,500", habitual:int, agentAdoption:int, conversion:int }
segments[]   { name, value, count }  five rows Champion→Never; value = % share
                                     (sum = 100), count = users (shown on hover)
surfaces[]   { name, pct, users }    top-10 apps by % of users active
agentShare[] { name, pct, users }    top-10 agents by active-user share
funnel[]     { name, value }  Unlicensed active, Warm+, Hot (counts)
```

If a report is not supplied, its `sources` flag is set `false`; the template dims
and marks the related panel as pending, and the footer lists the missing source.

## Recommended next steps (the framework's Action plays)

Below the charts the dashboard renders enablement plays from the framework's
action matrix. A card appears **only when a measured value trips its threshold**,
so the list stays short and every item cites the number that triggered it. This
is evaluated in the template from `DASHBOARD_DATA` (`buildRecos()` / `RECO_T`),
so the section stays correct if the data object is edited.

**Group 1 - triggered by your KPI values.** Shown only when a measured value
trips its scorecard threshold; each card cites the number that triggered it.

| Trigger (measured) | Threshold | Play |
|---|---|---|
| Low activation **or** many never-activated | activation < 80% or Never >= 10% | Onboarding campaign, first-prompt nudges, reclaim & reassign idle licences |
| Low depth | habitual < 40% | Role-based use cases, champions programme, lunch-and-learns |
| Narrow surface breadth | multi-surface < 50% | App-specific enablement, one dark surface at a time |
| Low agent adoption | agent adoption < 30% | Publish role-relevant agents, showcase high-value ones, target power users |
| Strong Chat pipeline (upside) | Hot + Warm > 0 | Business case for expansion, pilot-convert Hot leads, measure uplift |

**Group 2 - ongoing recommendations.** NOT threshold-driven: these rank the
surfaces and agents to point steady-state effort, so they are labelled
separately and shown **even when every KPI passes**.

| Focus | Selection | Play |
|---|---|---|
| Training focus | top 3 surfaces / agents by share | Deepen where adoption already exists; advanced role-specific sessions |
| Awareness focus | surfaces < 25%, agents < 10% | Promote the quiet surfaces one at a time; retire-or-relaunch the agent tail |

Every threshold above comes from the framework scorecard. **Dormancy is
deliberately not a trigger** - the framework treats it as a trend requiring two
reporting periods, and this dashboard is a single-period view, so flagging it
from one export would overstate what the data supports. The Dormant *segment*
still appears in the Pillar A donut, where "last activity >= 28 days ago" is
computable from a single export.

When no Group 1 card is triggered the section leads with *"You're doing great -
keep it up!"*; if reports were missing, that banner says so rather than implying
the untested pillars passed. Group 2 is shown regardless.

## Dashboard interactivity

Everything is pure CSS/SVG — no libraries, no scripts beyond the inline one.

- **Definitions:** all four KPI tiles *and* all four panels carry an `i` button
  (hover or keyboard focus) showing the metric's definition, how it is
  calculated, and the framework target. Panel definitions live in `PANEL_DEFS`
  in the template and mirror the pillar rules above; pending panels keep their
  button so a missing source is still self-explanatory.
- **Hover values:** the donut arcs, the donut legend rows, and every bar in
  Top surfaces and Agent usage share show `name: share · N users` on hover, so
  the underlying head-count is always one mouse-over away from the percentage.
  The count comes from the `count` / `users` field; if a payload omits it the
  tooltip degrades to the share alone.

## Column resolution

Header names vary between tenants and export versions, so the script matches
columns by normalised keyword (lower-cased, punctuation/space-stripped), not by
exact string. When a needed column cannot be matched it stops and lists the
available headers so the agent can supply a `--col-map` JSON override, e.g.:

```json
{
  "usage":  { "user": "UPN", "prompts": "Total prompts", "active_days": "Active days" },
  "chat":   { "user": "UPN", "prompts": "Chat prompts", "active_days": "Active days" }
}
```

Never fabricate a metric a column cannot support — map the column or leave the
related source out and let the panel render as pending.
