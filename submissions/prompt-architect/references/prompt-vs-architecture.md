# Prompt problem or architecture problem?

Use this guide before adding more instructions to a prompt. Many “prompt problems” are actually missing context, tooling, data, permissions, or deterministic controls.

## Decision guide

| Symptom | Likely prompt issue | Likely architecture issue | Better first move |
| --- | --- | --- | --- |
| Output format drifts | Output contract is vague or contradictory | Downstream parser requires strict validation | Clarify the contract; add deterministic schema validation when failure matters |
| Model invents facts | Prompt does not define source of truth or uncertainty behavior | Required knowledge is missing, stale, inaccessible, or not retrieved | Fix retrieval/data first; then require grounded behavior |
| Wrong action/tool is used | Tool-selection instructions are ambiguous | Tool is missing, too broad, incorrectly described, or permissions are wrong | Fix tool surface/descriptions/permissions before adding prompt prose |
| User must confirm before an action, but action fires | Confirmation rule is absent or unclear | Orchestration allows bypassing confirmation | Enforce the confirmation in workflow/orchestration |
| Agent reveals restricted information | Prompt lacks scope language | Authorization/data access is too broad | Fix permissions and data boundaries; prompt wording is not an access control |
| Prompt injection succeeds | External content is not clearly treated as data | Runtime has no isolation, allowlist, confirmation, or tool controls | Add architecture controls; use prompt boundaries as defense-in-depth only |
| Same task fails because required field is missing | Missing-input behavior is undefined | Upstream system is not supplying a required field | Define missing-input behavior and fix the upstream contract |
| Output varies across runs | Success criteria are under-specified | Task is inherently generative or model/settings vary | Define observable success; use deterministic logic only for deterministic requirements |
| Prompt is huge and brittle | Duplicated/conflicting rules and examples | Business logic is being encoded in prose | Move deterministic rules to code/workflow/reference data |
| Citations are requested but absent | Citation requirement is unclear | Runtime cannot return citations/source metadata | Fix retrieval/runtime first or remove impossible citation requirement |

## Architecture-first rules

Do not rely on prompt wording alone for:

- authentication or authorization;
- access control or row/document filtering;
- secrets handling;
- transaction limits;
- required approval gates;
- deterministic calculations or validation where errors are consequential;
- durable state or idempotency;
- audit logging;
- guaranteed citation generation when the runtime does not expose source metadata.

## Prompt-first rules

Prompt changes are appropriate when the failure comes from:

- unclear task framing;
- ambiguous terminology;
- missing source-of-truth instruction when the source is available;
- unclear output shape;
- undefined missing/ambiguous-input behavior;
- contradictory constraints;
- poor examples;
- hard-coded values that should be variables;
- unnecessary verbosity that hides the actual rules.

## Mixed failures

Some issues require both layers. Example:

> The model must ask for confirmation before sending an email.

Use the prompt to make the user experience clear and predictable, but use orchestration/tool logic to prevent the send action until confirmation is actually recorded.

When both layers matter, say which requirement belongs in the prompt and which must be enforced elsewhere.
