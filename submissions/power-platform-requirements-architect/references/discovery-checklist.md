# Discovery coverage checklist

Coverage guidance, not an interview script. Reciting this at a user is the fastest way to lose them. Use it to check what you still don't know, then ask about the consequential gaps.

Each domain notes **why it matters downstream** — if a domain has no downstream consequence for this particular solution, mark it `NOT-APPLICABLE` and move on.

## Contents
1. [Business context and scope](#1-business-context-and-scope)
2. [Actors, access, and volumes](#2-actors-access-and-volumes)
3. [Journeys and process states](#3-journeys-and-process-states)
4. [Functional behavior](#4-functional-behavior)
5. [Business rules and enforcement](#5-business-rules-and-enforcement)
6. [Data](#6-data)
7. [Integrations](#7-integrations)
8. [Automation](#8-automation)
9. [App surface, screens, and states](#9-app-surface-screens-and-states)
10. [Devices, responsiveness, offline](#10-devices-responsiveness-offline)
11. [Accessibility](#11-accessibility)
12. [Nonfunctional](#12-nonfunctional)
13. [Governance, licensing, compliance](#13-governance-licensing-compliance)
14. [ALM and operations](#14-alm-and-operations)
15. [Acceptance and prioritization](#15-acceptance-and-prioritization)

---

## 1. Business context and scope
- Problem or opportunity; what it costs today
- Current process, tools, and workarounds (the Excel file is always worth asking about)
- Target outcome and measurable success indicators with a baseline
- In scope / future scope / explicitly out of scope
- Deadline and what drives it (audit, season, contract, reorg)
- Stakeholders, and specifically **who decides** when requirements conflict

*Downstream:* scope errors produce the wrong solution; missing measures make it impossible to tell whether it worked.

## 2. Actors, access, and volumes
- User groups, approximate counts, and Entra groups that already represent them
- Internal / external / partner / anonymous
- Role differences in capability, not just in title
- Row-level access: who sees whose records, and on what dimension (own, team, store, region, all)
- Field-level sensitivity
- Approval authority and delegation when the approver is absent
- Admin, support, and read-only-observer roles
- Service accounts and system identities

*Downstream:* drives security roles, business units, teams, sharing, app sharing, licensing count, and the data platform choice.

## 3. Journeys and process states
For each significant journey: trigger, actors, steps, decision points, data touched, validations, exception paths, notifications, and completion outcome.

Then the **status model** as a whole:
- The full list of statuses and who may move a record between them
- Which transitions are irreversible
- What happens to a record that stalls
- Whether history of transitions must be reconstructable later

*Downstream:* status models become choice columns, business rules, flow trigger conditions, and role privileges. A vague status model produces a solution nobody can explain.

## 4. Functional behavior
- Create / read / update / delete, and per role
- Search, filter, sort — on which fields (this is the delegation question in disguise)
- Lists, galleries, views, dashboards, charts, KPIs
- Bulk actions and imports
- Attachments, photos, documents: types, sizes, expected counts per record
- Camera, barcode/QR, GPS, signature
- Comments, notes, activity history
- Draft / submit / withdraw / reopen semantics
- Duplicate prevention
- Export, print, PDF generation, sharing links
- Notifications: channel, recipient, trigger, and whether they're required or nice-to-have

*Downstream:* screens, columns, flows, and capacity estimates.

## 5. Business rules and enforcement
- Validation rules and their error messages
- Required-vs-optional per field, per status (fields are often only required at submission)
- Calculations, rollups, scoring, aggregation
- Conditional visibility and conditional requirement
- Uniqueness and referential rules
- Deadlines, escalation thresholds, working-day arithmetic, time zones
- Role-specific behavior differences
- What happens on the exception path for each rule

For each rule, capture **where it must be enforced** — app-only feedback vs server-side guarantee. See `architecture-decisions.md` AD-C.

*Downstream:* business rules, plug-ins, flow conditions, Power Fx, and column configuration.

## 6. Data
- Entities and their real-world meaning
- Primary identifier: human-readable number, autonumber format, or natural key
- Key fields per entity, with type, requirement level, and constraints
- Choice sets and their **actual option values** (not "a status field")
- Relationships, cardinality, and what should happen on parent delete
- Reference/master data and its owning system
- Alternate keys where external systems will upsert
- Row volumes now, growth per year, retention and archival
- Read/write frequency and peak patterns
- Sensitivity classification, personal data, retention obligations
- Existing data to migrate: source, volume, quality, mapping, cutover, rollback
- Audit requirements: which tables and columns, and for how long

*Downstream:* the entire data layer. This is where under-specification hurts most, because builders will guess types and requirement levels and be wrong in ways that are annoying to fix after data exists.

## 7. Integrations
- Systems involved, direction, and which side is authoritative
- Trigger: event-driven, scheduled, or on-demand
- Protocol and connector type (standard / premium / custom / API)
- Authentication: delegated user vs service principal vs API key, and who owns the credential
- Volume, payload size, and expected latency
- Throttling and service-protection limits
- Failure contract: retries, dead-lettering, alerting, replay
- Whether the integration already exists and can be reused

*Downstream:* connectors, connection references, DLP exposure, licensing, and the biggest source of production incidents.

## 8. Automation
- What must happen without a human
- Trigger for each automation, including trigger conditions that prevent loops
- Sequencing and dependency between automations
- Approvals: approver determination, timeout, escalation, reassignment, and record of decision
- Scheduled work: window, catch-up behavior after a failure, idempotency
- Expected run volume (drives licensing and throttling)
- Error handling and who is notified
- Long-running or high-volume patterns that need batching

*Downstream:* flow specs. See `automation-spec.md`.

## 9. App surface, screens, and states
- Which app type, and why (AD-B)
- Minimum screen inventory derived from the confirmed journeys — not invented
- Per screen: purpose, primary content, primary action, secondary actions, navigation in/out, role variants
- Empty, loading, error, offline, no-permission, and success states for each
- Brand and visual direction, or explicit delegation of visual choices to the coding agent
- Required components: forms, galleries, tables, tabs, dialogs, charts, dashboards
- Navigation pattern

*Downstream:* screen work items in the YAML. If the user has no visual opinion, record the delegation explicitly so the coding agent is allowed to decide.

## 10. Devices, responsiveness, offline
- Target devices and orientations, with a primary
- Browser vs Power Apps Mobile vs Teams vs embedded
- Which regions stack, collapse, hide, or become drawers at small widths
- Touch vs mouse/keyboard expectations
- Offline: required or not; which data must be cached; conflict and reconnect behavior; photos taken offline

*Downstream:* layout strategy, and a genuine architecture constraint — offline requirements narrow the platform choice sharply.

## 11. Accessibility
- Organizational standard (often WCAG 2.2 AA) and whether it's contractually binding
- Keyboard operability and logical focus order
- Screen reader support and accessible labels
- Contrast and text sizing
- Alternative text for meaningful images
- Whether an accessibility review is a release gate

## 12. Nonfunctional
- Performance targets, expressed observably ("list loads under 3s with 500 rows on 4G")
- Concurrency and peak load
- Availability expectations and acceptable degraded modes
- Data retention and archival
- Localization: languages, time zones, date and number formats, working calendars
- Telemetry and monitoring
- Support model: who gets the ticket, and what their access is

## 13. Governance, licensing, compliance
- Licensing implications of the design, per user group
- Consumption-based costs (AI Builder, Copilot Studio credits, capacity add-ons)
- Dataverse database / file / log capacity against the volume estimates
- DLP policy: are the required connectors permitted in the target environment
- Internal approval gates: environment requests, connector exceptions, maker program tiers, security review, data protection review
- Data classification, personal data handling, and any legal basis or agreement requirements
- Audit and traceability obligations

*Downstream:* `GOV-` items, most of which are human gates that must appear early in the build order because they have lead times.

## 14. ALM and operations
- Environment strategy and which environment this lands in
- Solution and publisher prefix
- Managed vs unmanaged downstream
- Deployment mechanism and who may run it
- Source control
- Environment variables and connection references needed
- Rollback plan
- Ownership after go-live, and the maker capability of that owner
- Documentation and handover expectations

## 15. Acceptance and prioritization
- MoSCoW or equivalent per requirement
- MVP boundary and what is deliberately deferred
- Acceptance criteria for at least every must-have journey
- UAT participants and process
- Definition of done for the whole solution (not just "it works on my machine")
- Explicit assumptions the user is knowingly accepting
