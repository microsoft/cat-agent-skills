# Architecture decisions

Requirements tell you what the business needs. These decisions determine whether the thing you build survives contact with 900 users, a promotion to production, and next year's change request.

Work them as a set, record each as an `AD-` entry, and get user confirmation. An unconfirmed decision is an assumption — put it in `open_items`, not in `architecture_decisions`.

Platform capabilities, licensing, limits and preview status change. Treat the guidance below as decision prompts, not timeless product facts. Verify material claims against current Microsoft Learn or an authoritative tenant source and record the date and URLs in `meta.capability_snapshot` before an approved recommendation depends on them.

## Contents
- [AD-A Data platform](#ad-a--data-platform)
- [AD-B App surface](#ad-b--app-surface)
- [AD-C Automation pattern](#ad-c--automation-pattern)
- [AD-D Security and access model](#ad-d--security-and-access-model)
- [AD-E Integration pattern](#ad-e--integration-pattern)
- [AD-F Environment and ALM strategy](#ad-f--environment-and-alm-strategy)
- [AD-G Licensing, DLP, capacity](#ad-g--licensing-dlp-capacity)
- [AD-H Ownership and maintainability](#ad-h--ownership-and-maintainability)
- [Common failure patterns](#common-failure-patterns)

---

## AD-A — Data platform

The decision with the highest blast radius. Retrofitting it means rebuilding everything above it.

| Option | Fits when | Breaks when |
|---|---|---|
| **Dataverse** | Relational model, row/field-level security, audit needed, offline mobile, solution-aware ALM, alternate keys for upsert, high volume with server-side query | Budget can't carry premium licensing; only a flat list is needed |
| **SharePoint lists** | Small, document-centric, list-shaped data; standard licensing; team-owned | Row-level security beyond item-level, >few thousand rows with complex filters (list view threshold + delegation), relational integrity, reliable concurrency |
| **Azure SQL** | Existing SQL estate, heavy reporting, external write paths, DBA ownership | You need Dataverse-native features (security roles, audit, offline, business rules); premium connector still required |
| **Fabric / Lakehouse** | Analytics and large historical data; read-mostly | Transactional app backend |
| **Existing system of record** (via integration) | The data already has an owner and must stay there | You need to write and the owning system offers no safe write path |
| **Dataverse for Teams** | Small team-scoped app, low volume | Growth beyond the environment's limits; needs standalone licenses later anyway |

Force these into the open before deciding:

- **Row counts today and per year.** "A few thousand" and "400k/year" are different platforms.
- **The queries users actually need.** Filter, sort, search, aggregate — on which columns? This is where delegation risk lives.
- **Who may see which rows and which fields.** If the answer is anything beyond "everyone sees everything", SharePoint gets expensive fast.
- **Is anything the system of record for another system?** That implies keys, idempotency, and audit.
- **Can the intended coding agent and its connected tools actually create it?** See [buildability](#buildability-as-a-decision-criterion). An unsupported surface becomes a human work item or requires a different implementation path.

Mixed models are legitimate — Dataverse for transactional data, SharePoint for document storage, existing SQL read-only via virtual table. Say so explicitly rather than letting it happen by accident.

## Buildability as a decision criterion

Ask early whether the coding agent must perform the whole build or whether human maker steps are acceptable. Do not rely on a static capability table: connected tools, preview status and supported operations change. Record the verified capability snapshot in `meta.capability_snapshot` and route unsupported or authority-bound actions to explicit human work items.

For every relevant surface, establish:

- whether the coding agent can create, update, test and publish it;
- which connected capability is expected to do so;
- which prerequisites require a live maker session, consent or pre-existing resource;
- which operations remain human for policy or authority reasons;
- what fallback applies when the capability is unavailable.

Buildability is one architecture criterion, not a licence to choose a more expensive platform for implementation convenience. Put automation benefit, manual effort, recurring licence cost and maintainability in the same `AD-` entry so the decision owner can make the trade-off consciously.

## AD-B — App surface

Multiple surfaces in one solution is normal for complex builds; a field app plus a back-office app is a common and correct answer.

| Option | Fits when | Watch out for |
|---|---|---|
| **Canvas app** | Task-focused, phone/tablet, pixel control, offline, guided flow | Screen sprawl; delegation; maintainability once formulas grow; needs a real component/theme discipline |
| **Model-driven app** | Process-heavy, many tables, views/forms/charts, role-driven, low custom UI need | Only on Dataverse; less layout freedom; users expect the shell |
| **Code app (React + Vite)** | Complex interaction, component reuse, dev team owns it, needs libraries | Requires a developer skill set to maintain; citizen makers cannot |
| **Power Pages** | External / unauthenticated / partner users | External identity, licensing, and security review are their own project |
| **Teams-embedded** | Work happens in Teams; lightweight | Still the same app underneath — decide the app type first |
| **No app** | Flow-only automation, or the interaction is a conversation | Someone still needs a way to see state and fix errors |
| **Copilot Studio agent** | Q&A, lookup, guided intake in chat | Not a substitute for a form-heavy or offline workflow; credit consumption is a real cost line |

Decide from the *user's context*, not from what's fashionable: a store manager standing in an aisle on a phone with patchy signal rules out most options immediately.

## AD-C — Automation pattern

| Option | Fits when | Costs |
|---|---|---|
| **Cloud flow (automated)** | React to a data change; async is acceptable | Latency (seconds+); not transactional with the originating write |
| **Cloud flow (instant/button)** | User-triggered action from app or Teams | Runs as the invoking user's connection unless designed otherwise |
| **Cloud flow (scheduled)** | Batch, reminders, syncs | Needs idempotency and a catch-up story after failures |
| **Child flow** | Shared logic reused across flows | Must be in the same solution; adds an error-handling boundary to design |
| **Dataverse business rule** | Simple field-level validation/defaults, needed in forms | Limited logic; form-scoped variants don't cover API writes |
| **Power Fx in the app** | Immediate UX feedback | Not enforcement — bypassed by any non-app write path |
| **Dataverse plug-in (C#)** | True synchronous enforcement, transactional, pre/post-operation | Needs a developer, ALM discipline, and a place to run tests. Check `CON-` capability constraints first |
| **Custom API / custom process action** | A reusable server-side operation callable from app, flow, and integration | Developer effort |
| **Desktop flow (RPA)** | Legacy system with no API | Fragile; needs a machine, credentials, and an owner |

The question that decides most of this: **must the rule hold when someone writes through the API or an import, not just through the app?** If yes, it belongs server-side (plug-in, flow on the data event, or a real constraint), not in Power Fx.

Second question: **synchronous or eventual?** "The number must be assigned before the user sees the record" is synchronous. "The manager gets notified" is eventual. Mixing these up produces race conditions that only appear under load.

## AD-D — Security and access model

Spell this out even when the user says "everyone can see everything" — write it down as a decision so it isn't discovered later to be false.

Cover:

- **Row ownership**: user/team-owned vs organization-owned per table. Organization-owned removes per-row access control entirely; that's a decision, not a default.
- **Business units**: needed when access maps to org structure (region, store, country). Cheap now, painful to introduce later.
- **Security roles**: one role per persona, privileges per table at the narrowest workable scope (None / User / Business Unit / Parent-Child BU / Organization). Deleting is rarely the right privilege for business data — prefer a status change.
- **Teams**: Entra group teams keep membership in Entra where identity governance already lives, rather than a manually maintained list.
- **Column-level security** for genuinely sensitive fields (salary, medical, disciplinary notes). It applies platform-wide, so decide it once.
- **Sharing**: who shares what, triggered by whom. Automated sharing in a flow is a common and legitimate pattern; unbounded sharing is a governance problem.
- **App sharing**: which Entra groups get the app, at what permission. Sharing to "everyone" is a finding in most audits.
- **Flow ownership and run-as**: flows owned by an individual break when that person leaves. Prefer a service account or a solution-aware flow with connection references, and name the owner.

## AD-E — Integration pattern

| Option | Fits when | Watch |
|---|---|---|
| **Standard connector** | The service is covered and standard tier suffices | Check DLP grouping |
| **Premium connector** | SQL, HTTP, Salesforce, SAP etc. | Licensing for every user of the flow/app |
| **Custom connector** | REST API you own or a documented third party | Needs DLP classification and a governance approval in most tenants |
| **Azure Function / Logic App** | Transformation, secrets, high throughput, complex retry | Another service to own, monitor, and pay for |
| **Virtual tables** | Read (and sometimes write) external data as if it were Dataverse | Provider capabilities and performance vary a lot |
| **Dataflow** | Scheduled bulk ingest | Not near-real-time |
| **Webhook / Service Bus** | Push from Dataverse to external, with buffering | Needs consumer ownership |

Always record: direction, auth model (**delegated user vs service principal** — this changes permissions, auditing, and what breaks when someone leaves), throughput, throttling behaviour, and the **failure contract**. What happens on failure is a requirement, not an implementation detail: retry how many times, then what, and who finds out.

## AD-F — Environment and ALM strategy

Decide even for "small" solutions that will reach production:

- **Environments**: dev / test / prod, or dev / prod. Personal/default environment is not a home for a production solution.
- **Solution + publisher prefix**: one publisher per org or per team, consistently. The prefix ends up in every schema name forever.
- **Managed vs unmanaged**: unmanaged in dev, managed downstream is the standard. Unmanaged in production means nobody can cleanly upgrade or remove it.
- **Deployment**: Power Platform pipelines, `pac solution import`, or Azure DevOps/GitHub. Manual export/import is acceptable only with a named owner and a documented process.
- **Source control**: unpacked solution in git or not. For L-tier, yes.
- **Environment variables and connection references** for everything environment-specific. This is what makes the above possible; without them promotion means hand-editing flows in production.
- **Rollback**: what happens if the import breaks prod.

## AD-G — Licensing, DLP, capacity

These are the decisions that kill projects after they're built, so surface them during requirements. Record each as a `GOV-` item with an owner and status.

- **Premium dependency**: record which app, flow, connector or Dataverse capability creates the premium requirement and which population invokes it. Do not reduce this to "premium means every user": automated/scheduled flows, instant or app-invoked flows, process licences, and in-app use rights can produce different licence populations. Treat the tenant's current licensing position as a `DEP-` input unless verified by an authorised owner.
- **Power Automate licensing**: record the flow type, invoking identity and intended licence path (user, process, or applicable app-context rights). Have the platform owner confirm it; licensing rules change and the requester usually cannot approve the spend.
- **AI consumption**: Copilot Studio credits, AI Builder credits, and any MCP calls charged outside Copilot Studio are consumption-based. Forecast expected sessions or calls and verify the current charging model before approval.
- **Dataverse capacity**: database, file, and log capacity against the row volumes and attachment sizes in `data.volumes`. Attachments are usually the surprise.
- **DLP policies**: will the connectors in this design actually be allowed in the target environment? Custom and HTTP connectors are commonly blocked by default. This is a hard gate — find out early.
- **Tenant and program governance**: many orgs gate maker access, connector use, or environment creation behind an internal program or approval. If the user operates under such a program, capture its gates as `GOV-` items and `CON-` constraints so the build order reflects the real waiting time.
- **Data classification and residency**: does the data type impose restrictions on where it can live or which connectors may touch it?

## AD-H — Ownership and maintainability

Who owns this in twelve months, and can they change it? A plug-in-heavy design handed to a citizen-maker team is a design defect no matter how elegant it is. Capture the maker capability as a `CON-` constraint and let it genuinely constrain AD-C and AD-B.

Also decide: naming conventions, whether components/templates are shared across the org, how errors get monitored and by whom, and where documentation lives.

---

## Common failure patterns

Recognizing these during requirements is much cheaper than discovering them at build time.

- **The SharePoint list that needed to be Dataverse.** Discovered when the first "only the store manager may see their own rows" requirement lands, or at 5,000 rows.
- **Business rules only in the app.** Any import, API call, or second app silently violates them.
- **Hardcoded environment values.** Site URLs and group GUIDs baked into flows; the solution imports but points at dev.
- **Flows owned by a person.** Works until they change teams.
- **Delegation ignored.** Works with 200 test rows, silently truncates at 500 in production. Non-delegable filters/sorts must be caught in the spec, not in UAT.
- **No idempotency on scheduled or upsert flows.** A retry creates duplicates.
- **Approval with no timeout.** The approver is on holiday; the process stops forever with no visible owner.
- **Attachments in Dataverse notes with no volume estimate.** Capacity bill arrives later.
- **Premium licensing discovered after build.** The design was fine; the funding wasn't.
- **DLP discovered after build.** The connector was never going to be allowed.
- **No error surface.** Flows fail silently for weeks because nothing routes failures to a human who cares.
