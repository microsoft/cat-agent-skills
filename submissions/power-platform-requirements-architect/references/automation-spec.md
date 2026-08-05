# Specifying automation

A flow spec is buildable when a builder can construct it without asking "and what if that fails?". Failure behavior, trigger precision, and identity are the three things most often missing, and all three cause production incidents rather than build-time errors.

## Contents
- [Per-automation spec](#per-automation-spec)
- [Triggers](#triggers)
- [Identity and run-as](#identity-and-run-as)
- [Connection references and environment variables](#connection-references-and-environment-variables)
- [Error handling](#error-handling)
- [Idempotency](#idempotency)
- [Concurrency, volume, throttling](#concurrency-volume-throttling)
- [Approvals](#approvals)
- [Child flows and shared logic](#child-flows-and-shared-logic)
- [Non-flow automation](#non-flow-automation)
- [Test cases](#test-cases)

---

## Per-automation spec

Each `FLW-` entry needs:

1. **Name** following the convention `<Solution area> - <Verb phrase>` (`Inspection - Escalate critical finding`). Names are the only navigation aid in a solution with 30 flows.
2. **Kind and type**: cloud flow (automated / instant / scheduled), child flow, desktop flow, plug-in, business rule, custom API.
3. **Solution-aware**: yes, for anything that must be promoted. Non-solution flows cannot be deployed properly and cannot use connection references.
4. **Trigger** with its precise condition.
5. **Run-as identity.**
6. **Inputs** and their types, for instant and child flows.
7. **Steps** in business terms — enough to construct, not pseudo-JSON.
8. **Error handling** behavior.
9. **Idempotency** rule.
10. **Concurrency** setting and expected volume.
11. **Connection references** and **environment variables** used.
12. **Implements**: the `FR-`/`BR-` ids it satisfies.
13. **Test cases**, including at least one failure case.

Write steps at the level of "Get the store's Area Manager from TBL-002; if empty, use the regional fallback from EV-003" — decisions and data resolution explicit, connector minutiae left to the builder.

## Triggers

Precision here prevents both missed runs and infinite loops.

- **Automated (Dataverse)**: table, scope (user / business unit / organization), which change type (create / update / delete), and **which columns** trigger it. Firing on any update is the classic cause of loops and throttling; naming the filtering columns fixes it.
- **Trigger conditions**: state them as a business rule ("only when Status changes to Submitted and the previous status was Draft"). Also state explicitly whether the flow should skip its own writes — a flow that updates the table it triggers on needs either a column filter or a marker to avoid re-entry.
- **Instant / app-invoked**: what invokes it, what inputs it receives, whether the app waits for a response, and what the app does if the call fails.
- **Scheduled**: interval, time, **time zone by name**, and what happens if a run is missed. "Daily at 05:00" without a time zone is a bug in every country that observes DST.
- **HTTP request**: auth model, expected payload schema, and the response contract.
- **Webhook / event**: source system, event, and whether ordering or duplicates are possible.

## Identity and run-as

Say who the flow runs as, and why:

- **Service account** — the default answer for scheduled and system automation. Survives people leaving. Needs a licensed account and a named owner.
- **Invoking user** — appropriate when the action must be attributed to that user or must respect their row access.
- **Service principal / application user** — for integrations; no interactive licence, no leaver risk, but auditing shows the app rather than a person.

Also record **flow ownership** (co-owners, ideally a team not an individual) and which security role the run-as identity needs on the tables it touches. A flow that fails at 03:00 because its service account lacks Append To is a specification failure, not a build failure.

## Connection references and environment variables

For anything that will be promoted:

- Every connector use becomes a **connection reference** (`CR-`), with connector, tier, auth model, consenting identity, and whether consent is a human gate (it almost always is).
- Every environment-specific value becomes an **environment variable** (`EV-`): site URLs, list names, group ids, mailboxes, API base URLs, thresholds someone will want to change without editing the flow, feature toggles.
- Secrets go in an Azure Key Vault-backed environment variable, never in a flow, never in a spec file. If the spec would otherwise contain a credential, write `SET_AT_DEPLOY` and name the owner.

State per environment which values differ. This section is what makes the difference between a solution that promotes cleanly and one that needs hand-editing in production.

## Error handling

Specify a pattern, not a hope. For each flow:

- **Pattern**: a Try/Catch/Finally scope arrangement is the standard. A generic catch that inspects `result()` of the try scope avoids maintaining a per-action error list, which is what makes error handling survive later edits.
- **Retry**: default exponential is fine for transient faults; say where it isn't (non-idempotent external calls need retry disabled or an idempotency key).
- **On final failure**: who or what finds out. A Teams post, a record in an error table, an email to a monitored mailbox — but never nothing. "The maker sees it in run history" is not monitoring.
- **Partial failure in loops**: continue and collect, or stop at first error? For a 900-store batch, stopping at the first error is usually wrong; collecting failures and reporting them at the end is usually right. Say which.
- **Dead-lettering and replay**: for integrations, where does a failed message go and how is it replayed.
- **Business-visible failure**: if a user was waiting on this, what do they see?

## Idempotency

Any flow that can be retried, resubmitted, or run twice needs a rule for what "already done" means. Without it, retries create duplicate records and duplicate emails, and someone eventually discovers it via a customer.

State the mechanism: an alternate key upsert, a check-before-create, a processed flag with a timestamp, or a deduplication key derived from the source event. For scheduled catch-up work, also state how the flow knows what it already covered.

## Concurrency, volume, throttling

- **Concurrency control**: on or off, and the degree. Off means Power Automate may run many instances in parallel — good for throughput, dangerous when the flow assigns sequential numbers or mutates shared state.
- **Loop concurrency**: parallel degree for Apply-to-each. Parallel is faster and breaks anything order-dependent.
- **Expected run volume** per day/month: drives licensing (per-flow vs per-user), throttling risk, and Dataverse service protection limits.
- **Batching** for high-volume writes, with the batch size.
- **Long-running work**: if a run could exceed platform limits, say how it's split — pagination, chunked scheduling, or a queue.

## Approvals

Approvals are where under-specification is most visible to end users. Cover:

- How the approver is determined (a lookup, a manager hierarchy, a group, a fixed list) and the fallback when it resolves to nobody
- Single vs multiple approvers; all-must-approve vs first-response
- **Timeout behavior** — after how long, and then what: escalate, auto-approve, auto-reject, or notify a human. "Nothing" leaves the process stalled forever
- Reassignment and delegation while someone is away
- Whether comments are mandatory on rejection
- Where the decision, decider, timestamp, and comment are stored for audit
- Whether the record is locked during approval, and what a user sees if they open it

## Child flows and shared logic

Use a child flow when the same logic is needed in three or more places, or when a unit deserves its own error boundary. Specify inputs, outputs, and the fact that it must live in the same solution as its callers. Note that a failing child flow surfaces as a failure in the parent — say which layer is responsible for reporting.

## Non-flow automation

- **Business rules**: scope (entity vs form), conditions, actions. Entity-scoped for anything that must hold beyond the form.
- **Plug-ins**: message, stage (pre-validation / pre-operation / post-operation), synchronous or async, and the transactional expectation. Only propose these when a `CON-` capability constraint allows a developer to maintain them.
- **Custom API / process action**: signature, inputs, outputs, and who calls it.
- **Desktop flows (RPA)**: target application, machine or machine group, credentials and their owner, attended vs unattended, and the fragility mitigation. RPA needs an owner more than anything else on this list.
- **Power Fx in the app**: fine for immediate UX feedback; note explicitly that it is not enforcement.

## Test cases

At least two per automation, and at least one that fails:

- the happy path with an expected outcome,
- the exception path from the journey (missing approver, offline, malformed payload),
- an idempotency check ("run twice, assert one record"),
- for scheduled flows, a catch-up check after a simulated missed run.

These become the acceptance checks on the work item, which is what lets a build agent verify its own output instead of declaring success on a green run.
