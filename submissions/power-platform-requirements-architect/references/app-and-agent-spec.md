# Specifying apps and agents

Screens come from confirmed journeys, not from imagination. If a screen doesn't appear in a journey, ask why it exists before specifying it.

## Contents
- [Screen inventory](#screen-inventory)
- [Per-screen spec](#per-screen-spec)
- [States](#states)
- [Delegation in the app layer](#delegation-in-the-app-layer)
- [Canvas apps](#canvas-apps)
- [Model-driven apps](#model-driven-apps)
- [Code apps](#code-apps)
- [Power Pages](#power-pages)
- [Offline](#offline)
- [Visual direction](#visual-direction)
- [Accessibility](#accessibility)
- [Copilot Studio agents](#copilot-studio-agents)

---

## Screen inventory

Derive it: walk each journey and list the distinct views a user needs. Then check role variants — an Area Manager viewing the same list with a wider row scope is usually the same screen with a different filter, not a second screen. Say which it is, because "same screen, different scope" and "two screens" are different amounts of work.

Keep the inventory minimal for the MVP and list deferred screens in `future_scope`. Screen count is the main driver of app build effort.

## Per-screen spec

For each `SCR-`:

- **Purpose** in one sentence — what the user accomplishes here
- **Actors** who see it
- **Primary content**: which data, filtered how, sorted how
- **Primary action**: the one thing this screen exists for
- **Secondary actions**
- **Navigation** in and out
- **Role variants**
- **States** (below)
- **Validation shown here**, and which `BR-` rules apply
- **Delegation note** where the data set is large

## States

Every data-bound screen needs its states specified, because builders default to only the happy path and users spend a surprising amount of time in the others.

Prefer a mapping keyed by the canonical kind, with the description in whatever language the spec is written in:

```yaml
states:
  loading: "Show a skeleton, then load the data"
  empty: "No reports yet; link to the Report tab"
  error: "Loading failed; show a Retry button"
  success: "Show the report list with status indicators"
```

A plain list works too, but only the mapping can be checked for completeness — matching keywords against prose fails as soon as the spec is written in German, which is normal and encouraged. The kinds:

- **loading** — and whether it's a skeleton, spinner, or cached-then-refresh
- **empty** — with the distinction between "no data yet" and "no results for this filter", which need different messages and different actions
- **error** — what the user sees and what they can do
- **offline** — if offline is in scope: what's available, what's marked pending, how sync status is shown
- **no permission** — what a user sees when their role scope excludes the record
- **success** — confirmation and where they land next

## Delegation in the app layer

For every gallery, table, or list bound to a data source that can exceed the record limit, state the filter and sort and whether they delegate on the chosen platform. Where they don't, name the mitigation in the spec: a delegable rewrite, a pre-filtered server-side view, a search-first pattern, or an accepted cap the business has agreed to.

This is worth the words because the failure is invisible in testing — everything works on 200 rows and silently truncates in production.

## Canvas apps

Practical constraints to reflect in the spec and the work items:

- Record whether the intended coding capability requires a **live Power Apps Studio session**, an existing app shell or another maker-side prerequisite. Do not assume it.
- Make every unavailable or authority-bound data-source/consent step an explicit prerequisite work item with `owner: human` and `human_gate: true`.
- Specify the **theme and component approach**: a shared header/footer component and a consistent theme make later edits tractable; per-screen hand-styling doesn't.
- Specify **navigation pattern** (tab bar, hamburger, wizard) once, at app level.
- Each screen spec must be complete enough that the coding agent does not infer behaviour from another screen.
- Note **form factor**: phone portrait and tablet landscape are different layouts; name the primary.

## Model-driven apps

Specify: site map areas/groups/subareas, which tables appear, and per table which **views** (name, columns, filter, sort, default) and which **forms** (main, quick create, quick view, and section layout). Then business process flows if used, charts, and dashboards.

Model-driven apps are configuration over layout: precision about views and forms is where the value is, and users judge them on whether the right columns are in the right default view.

## Code apps

Specify: framework and stack expectations, which connectors/data sources, component inventory, routing, state management approach, auth context, and how it's deployed. Note the maintainability consequence — a code app needs someone who can run a build.

## Power Pages

Specify: pages, authentication (external identity provider, invitation, self-registration), **table permissions and web roles** (the security model is separate from Dataverse roles and is where most Pages incidents originate), forms and lists, and anything anonymous users may reach. Anonymous access needs a deliberate decision recorded as an `AD-`, plus a security review as a `GOV-` gate.

## Offline

If offline is in scope, specify: which tables and which subset of rows are cached, how much data that is per user, what a user may create or edit offline, conflict resolution when two people edited the same record, how sync status is surfaced, and what happens to photos taken offline. "It should work offline" is not a specification; "own-store open inspections plus store master, create and edit allowed, last-write-wins with a conflict warning" is.

## Visual direction

Capture only what affects the build:

- brand constraints: primary colour, logo, typography if mandated
- light/dark preference
- density and character (dense data tool vs spacious guided form)
- required component patterns: cards, tables, tabs, dialogs, charts
- references the user likes or dislikes

If the user has no opinion, record the delegation explicitly (`UX-nnn: coding agent may choose ...`) so the coding agent knows it has permission to decide rather than stalling or inventing something it was not authorised to invent.

## Accessibility

State the standard (often WCAG 2.2 AA) and whether it's a release gate. At minimum specify: keyboard operability with visible focus, accessible labels on all interactive controls, logical tab and reading order, contrast requirements, text sizing/zoom behavior, and alt text on meaningful images. For canvas apps, note that accessible labels and tab order are properties a builder must set deliberately — they don't happen by default.

## Copilot Studio agents

For each `AGT-`:

- **Purpose and boundary**: what it answers or does, and explicitly what it must not do. Read-only vs able to write is an architecture decision with an audit consequence.
- **Knowledge sources**: which SharePoint sites, files, Dataverse tables, or public sites; and whether the underlying permissions are trimmed per user.
- **Tools and actions**: connectors, flows invoked as actions, MCP tools. Each one inherits the same connection-reference and DLP considerations as a flow.
- **Topics or instruction design**: the intents it handles, and the escalation path to a human.
- **Channels**: Teams, web, embedded — each has its own auth and publishing story.
- **Authentication**: Entra user-delegated vs no auth. Delegated is what keeps a user from reading data they otherwise couldn't.
- **Consumption expectation**: agent responses consume Copilot Studio credits (or the tenant's messages/capacity model). Forecast expected sessions per month so the cost is a known number rather than a surprise, and record it as a `GOV-` item where the user isn't the budget holder.
- **Guardrails and testing**: response constraints, PII limits, and a set of test utterances including out-of-scope ones.
- **Publishing and governance**: who may share it, with whom, and which internal approval that requires.

Agents look cheap to specify and aren't: the knowledge permission model and the consumption forecast are the two things that turn into problems later.
