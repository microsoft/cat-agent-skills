# Manual self-check before handoff

Work this checklist against the complete YAML before requesting approval. This skill has no executable validator. Report the result honestly and fix critical defects before handoff.

## Structure and status

- [ ] `meta`, `solution`, `business`, `work_items`, `build_order`, `deployment_inputs`, `open_items` and `handoff` are present and coherent.
- [ ] Sections that do not apply are omitted; relevant unexplored areas are visible in `open_items`.
- [ ] `meta.status: approved` is used only after user approval and with no unresolved critical requirement or architecture question.
- [ ] An approved specification records approver, role, date and approval statement in `meta.approval`.
- [ ] `build_contract` exists for the coding agent and its `status` matches actual execution readiness.
- [ ] `handoff.blocking_ids` contains every unresolved prerequisite and no resolved one.
- [ ] `handoff.first_work_item` is set only when the contract is ready.
- [ ] `handoff.manual_self_check` records this checklist's outcome and any findings.
- [ ] YAML uses no anchors, aliases, merge keys or custom tags; repeated structures are explicit.

## Identifiers and references

- [ ] Every id follows its uppercase, zero-padded convention (`FR-001`, not `FR1`).
- [ ] No id appears twice.
- [ ] Open items use unique `OI-` ids; an open item referring to an existing object uses `ref` instead of reusing that object's id.
- [ ] Every referenced id is declared.
- [ ] Reference fields contain the correct id type: `depends_on` uses `WI-`, `implements` uses `FR-`/`BR-`, and work-item phase lists use `WI-`.
- [ ] Existing ids remained stable after revisions.

## Requirements coverage

- [ ] Every `must` requirement has observable acceptance criteria.
- [ ] Every `must` requirement is implemented by at least one work item.
- [ ] Every work item either implements a requirement/business rule or is justified as infrastructure.
- [ ] Every material business rule contains a condition, consequence and enforcement location.
- [ ] Vague quality words were converted into measurable `NFR-` or acceptance criteria.
- [ ] Scope and out-of-scope boundaries do not contradict work items.

## Journeys and exceptions

- [ ] Every critical journey has actor, trigger, main path, decisions, exception paths and outcome.
- [ ] Approval timeouts, absences, retries, duplicate submissions and final-failure handling are defined where relevant.
- [ ] Operational ownership is named: somebody detects and resolves failed processes and bad data.

## Data and security

- [ ] Every table has ownership, primary name, volume/growth and retention assumptions.
- [ ] Every column has type, requirement level and applicable constraints.
- [ ] Every lookup names its target and every choice includes actual option values.
- [ ] Every relationship states its cardinality and delete/cascade behaviour.
- [ ] Choice and status fields contain every referenced label and numeric value.
- [ ] Currency thresholds define permitted currencies or an authoritative conversion rule, and calculations define rounding/tolerance.
- [ ] Idempotency keys reference fields that exist and have defined update semantics.
- [ ] Working-day rules name the calendar source and required fields; conditional delete rules name an enforceable mechanism.
- [ ] Row, team/business-unit and field-level access rules are explicit.
- [ ] Security roles and sharing targets implement those rules.
- [ ] Schema names use the confirmed publisher prefix or a blocker-backed placeholder.

## Automation and integrations

- [ ] Every automation has trigger, trigger conditions, steps, run-as identity, error handling and tests.
- [ ] Scheduled or retryable processing defines idempotency.
- [ ] Integrations define direction, system of record, connector/API, authentication, data mapping, timeout/retry and failure ownership.
- [ ] Connection references exist for every connector used by solution-aware flows.
- [ ] Environment-specific values use environment variables.
- [ ] No credentials, tokens or secret values appear in the YAML.

## Work items and sequencing

- [ ] Every work item has surface, owner, dependencies, spec references, acceptance criteria and human-gate flag.
- [ ] Every work item appears exactly once in `build_order`.
- [ ] No dependency cycle exists and no item depends on a later phase.
- [ ] Solution and configuration precede schema; schema precedes flows/apps; security precedes realistic acceptance tests.
- [ ] Human prerequisites appear before coding-agent work that needs them.

## Deployment and authority

- [ ] Every `{prefix}`, `SET_AT_BUILD` or equivalent placeholder has a `DEP-` entry with supplier and usage.
- [ ] Required unresolved `DEP-` and `GOV-` entries are listed in `handoff.blocking_ids`.
- [ ] Every unresolved deployment input is listed in `handoff.blocking_ids`, including inputs needed only by later work items.
- [ ] A `ready` contract has no unresolved required deployment input.
- [ ] A `ready` contract names a non-production first target.
- [ ] `authority.may`, `authority.may_not`, stop conditions and verification rules are explicit.
- [ ] Production deployment, consent, DLP, licence, Entra and destructive data actions remain human-gated unless explicit authority is documented.

## Approval result

State one of these outcomes before emitting the YAML:

- `passed`: no critical defects; requirements and coding-agent contract are both ready;
- `passed, build blocked`: requirements are approved, but listed deployment/governance prerequisites block execution;
- `not passed`: critical requirements or architecture gaps remain; do not mark the specification approved.

Finally, verify that the complete YAML can be delivered without truncation. A missing closing fence, omitted tail section or channel-limited partial response is `not passed` regardless of content quality.
