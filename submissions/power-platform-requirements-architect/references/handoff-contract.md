# Coding-agent handoff contract

The canonical result of this skill is one self-contained YAML document with the root key `POWER_PLATFORM_SOLUTION_SPEC_V1`. The coding agent must not need the requirements conversation, separate packet files or additional explanations to understand the approved baseline.

Use `assets/solution-spec.template.yaml` as the field structure. Delete sections that genuinely do not apply. Never leave unexplored areas as empty scaffolding; record relevant gaps in `open_items`.

## Contents

- [Status model](#status-model)
- [Final response](#final-response)
- [Coding-agent contract](#coding-agent-contract)
- [Identifier conventions](#identifier-conventions)
- [Omission and placeholder rules](#omission-and-placeholder-rules)
- [Revision rules](#revision-rules)

## Status model

Requirements completion and execution readiness are independent.

| Field | Meaning |
|---|---|
| `meta.status: draft` | Discovery is incomplete. Do not hand off for implementation. |
| `meta.status: in_review` | A complete candidate is being reviewed. |
| `meta.status: approved` | Critical requirements and architecture decisions are resolved and the requester approved the baseline. |
| `build_contract.status: draft` | The coding agent must not execute. It may inspect the specification and report blockers. |
| `build_contract.status: ready` | The coding agent may execute in dependency order within the stated authority. |

An approved specification can remain blocked for implementation. Common reasons are missing environment name, publisher prefix, connection identity, DLP decision, licence approval or consent.

Derive the visible coding-agent readiness as follows:

- `READY`: `meta.status` is `approved`, `build_contract.status` is `ready`, `handoff.blocking_ids` is empty and the first work item is not human-gated.
- `BLOCKED`: the requirements baseline is approved but one or more execution prerequisites remain.
- `NOT APPROVED`: `meta.status` is `draft` or `in_review`.

Never use `READY WITH ASSUMPTIONS`. A value needed to execute is either confirmed or blocking.

When `meta.status` is `approved`, complete `meta.approval` with the approver, role, date and a short statement identifying what was approved. Record the manual check result in `handoff.manual_self_check`; this evidence belongs inside the YAML because the coding agent does not see the conversation.

## Final response

After explicit approval, emit exactly this shape:

```text
Requirements engineering complete
Requirements status: APPROVED
Coding-agent readiness: READY | BLOCKED
Revision: <number>
Blocking ids: none | DEP-001, GOV-002, ...
Manual self-check: passed | passed with listed noncritical assumptions
```

Then emit one complete YAML block:

````text
```yaml
POWER_PLATFORM_SOLUTION_SPEC_V1:
  ...complete specification...
```
````

Do not emit separate build packets, phase documents, diffs or abbreviated YAML. Do not put information required for implementation only in prose outside the YAML.

Never truncate the YAML or silently omit sections to fit a response. Prefer a native `.yaml` or plain-text attachment when the host can create one without altering the artifact. If neither a complete inline block nor a complete attachment is possible, report delivery as blocked; an incomplete document is not a handoff. Keep the YAML compatible with safe parsers: no anchors (`&name`), aliases (`*name`), merge keys (`<<`) or custom tags.

When readiness is `BLOCKED`, the YAML remains useful. The coding agent can review it, but `build_contract` must instruct it not to create or modify anything until all `handoff.blocking_ids` are resolved and a new approved revision sets the contract to `ready`.

## Coding-agent contract

Include `build_contract` for every coding-agent handoff. It must define:

- `status`: `draft` or `ready`;
- `audience`: the intended coding agent;
- `target`: environment, solution unique name and scope boundary;
- `authority.may`: actions explicitly permitted;
- `authority.may_not`: tenant, production, destructive and out-of-scope actions prohibited;
- `stop_and_report_when`: conditions that require the agent to stop;
- `on_stop`: the exact information to report;
- `verification`: acceptance criteria must be checked after each work item.

The coding agent must treat these rules as part of the requirements, not as suggestions. `handoff.instructions` must also state that it must:

1. treat the YAML as the source of truth;
2. execute only a `ready` contract;
3. follow `build_order` and `depends_on`;
4. not invent missing business logic or tenant values;
5. stop at human gates and contradictions;
6. verify each work item's acceptance criteria;
7. report platform deviations against stable ids.

All implementation units remain inside `work_items`. Each `WI-` item needs:

- `surface`;
- `owner`: `coding_agent` or `human`;
- `depends_on`;
- `implements` for `FR-`/`BR-` traceability;
- `spec_refs` for the exact objects it creates or changes;
- `acceptance`;
- `human_gate`;
- `notes` when the item is infrastructure or carries a constraint.

## Identifier conventions

Use stable, zero-padded ids. Never reuse or renumber them after a revision.

| Prefix | Meaning | Prefix | Meaning |
|---|---|---|---|
| `GOAL-` | Success measure | `FR-` | Functional requirement |
| `OOS-` | Out of scope | `BR-` | Business rule |
| `ACT-` | Actor or persona | `AD-` | Architecture decision |
| `JRN-` | User journey | `TBL-` | Table or data entity |
| `COL-` | Referenced column | `CHO-` | Choice or option set |
| `REL-` | Relationship | `SEC-` | Security role or rule |
| `INT-` | Integration | `FLW-` | Automation |
| `APP-` | Application | `SCR-` | Screen, page or view |
| `AGT-` | Copilot Studio agent | `CR-` | Connection reference |
| `EV-` | Environment variable | `NFR-` | Nonfunctional requirement |
| `ACC-` | Accessibility requirement | `GOV-` | Governance or approval gate |
| `MIG-` | Migration item | `CON-` | Constraint |
| `RSK-` | Risk | `DEP-` | Tenant-owned deployment input |
| `UX-` | Delegated UX decision | `WI-` | Work item |
| `OI-` | Open requirement or decision |  |  |

Every referenced id must be declared. Reference fields must contain the correct id type. For example, `depends_on` contains only `WI-` ids and `implements` contains only requirement or business-rule ids.

An entry in `open_items` uses its own unique `OI-` id. When it concerns an existing deployment input, governance gate, risk or requirement, add `ref: DEP-006` (or the applicable id). Never assign the referenced object's id to the open item itself.

## Omission and placeholder rules

- Omit a whole section only when it does not apply.
- Put a relevant but unresolved business or architecture question in `open_items`.
- Put a tenant-owned build value in `deployment_inputs` with `value: SET_AT_BUILD`, a supplier and its usage location.
- Never put credentials, tokens or secrets in the document. Refer to a secret-backed environment variable or deployment-time configuration.
- Every `{prefix}` or `SET_AT_BUILD` value must map to a `DEP-` id.
- A required `SET_AT_BUILD` value must appear in `handoff.blocking_ids` and keeps `build_contract.status` at `draft`.
- Every unresolved deployment input appears in `handoff.blocking_ids`, even when it would block only a later work item. A `ready` contract means the full approved build plan can execute until it reaches an intentional human gate.
- Do not ask a business requester to confirm tenant facts they do not own. Assign the deployment input to the correct platform, security or governance owner.

## Revision rules

The YAML is always emitted in full. When a material change occurs:

1. keep all existing ids stable;
2. update every affected reference and acceptance criterion;
3. increment `meta.revision`;
4. append a concise entry to `meta.change_log`;
5. obtain approval when scope, behaviour, architecture, security, cost or authority changed;
6. emit the complete replacement YAML.

The coding agent reports deviations using ids, for example: `WI-014 blocked because CR-002 cannot use the specified authentication model`. The requirements engineer then revises the canonical artifact instead of allowing the coding agent to improvise.
