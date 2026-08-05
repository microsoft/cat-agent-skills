# Decompose the specification for a coding agent

Use this reference after requirements and architecture are stable. Work items are part of the canonical YAML, not separate documents.

## Work-item contract

Each `WI-` item must be independently understandable from the YAML and contain:

| Field | Required meaning |
|---|---|
| `id` | Stable `WI-###` identifier |
| `title` | Concrete outcome, not a vague activity |
| `status` | `not_started`, `blocked`, `in_progress`, `done` or `waived` |
| `surface` | `solution`, `envvar`, `connection`, `dataverse`, `security`, `data`, `flow`, `canvas`, `model`, `code`, `pages`, `agent`, `integration`, `test`, `deployment` or `manual` |
| `owner` | `coding_agent` or `human` |
| `depends_on` | Earlier `WI-` ids that must be complete |
| `implements` | `FR-` and `BR-` ids delivered by the item |
| `spec_refs` | Exact `TBL-`, `FLW-`, `APP-`, `SCR-`, `SEC-`, `INT-`, `CR-`, `EV-` or related ids affected |
| `acceptance` | Observable checks proving the item works |
| `human_gate` | `true` when authority, consent or judgement is required |
| `notes` | Constraints, infrastructure justification or execution boundary |

Use `owner: human` for actions a coding agent cannot or must not perform, such as licence purchase, DLP changes, consent, Entra membership, production approval, business sign-off and destructive migration approval.

Do not hide a human prerequisite in notes. Create an explicit work item or governance gate and make dependent coding-agent items depend on it.

## Traceability

Every `must` requirement must be covered by at least one work item through `implements` or `covered_by`. Every work item must either implement a requirement/business rule or be justified as infrastructure.

Use `spec_refs` to point the coding agent to the exact specification entries it must implement. Do not duplicate full definitions in notes.

Examples:

```yaml
- id: WI-007
  title: "Create Inspection and Finding schema"
  status: not_started
  surface: dataverse
  owner: coding_agent
  depends_on: [WI-001]
  implements: [FR-004, BR-002]
  spec_refs: [TBL-001, TBL-002, CHO-001, REL-001]
  acceptance:
    - "Every specified column exists with the required type and requirement level"
    - "Deleting an Inspection follows the confirmed REL-001 behaviour"
  human_gate: false
  notes: "Create only inside the solution named by the ready build contract."
```

## Dependency-safe build order

Use phases appropriate to the solution, normally:

1. solution and publisher foundation;
2. environment variables and connection references;
3. tables, columns, choices, relationships and keys;
4. security roles and ownership configuration;
5. reference data and approved migration preparation;
6. cloud flows, business rules and integrations;
7. apps, pages and Copilot Studio agents;
8. end-to-end testing, sharing and rollout gates.

Hard constraints:

- no item may depend on an item in a later phase;
- every work item appears exactly once in `build_order`;
- data-source items precede consumers;
- connection and environment-variable items precede flows that reference them;
- security configuration precedes realistic acceptance testing;
- human gates appear early enough to avoid blocking a later phase unexpectedly.

If a dependency cycle exists, the specification is not ready. Redesign the work items instead of choosing an arbitrary start point.

## Coding-agent start rule

Set `handoff.first_work_item` to the first executable item only when `build_contract.status` is `ready`. Otherwise use `null` and list every blocker in `handoff.blocking_ids`.

The coding agent receives the complete YAML once. It works one item at a time, verifies acceptance, and stops when:

- a dependency is incomplete;
- a human gate is reached;
- a required deployment input is unresolved;
- the platform contradicts the specification;
- implementation would exceed `build_contract.authority`;
- business behaviour is ambiguous.

On stop, it must report the work item id, expected state, observed state and decision required. It must not continue into dependent work.
