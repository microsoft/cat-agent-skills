# Host Profiles, Templates, and Contracts

Read this reference when selecting a host profile, choosing a template, or producing mappings and wiring guidance.

## Capability boundary

This package targets Copilot Studio agents on the standard harness only. The
skill may be invoked from a skills-capable GitHub Copilot harness, but that
harness does not support Adaptive Cards or topic nodes. The generated package
cannot render or be tested in that same GitHub Copilot harness agent.

This package builds and reviews maker artifacts. It does not attach cards to runtime messages and does not edit Copilot Studio topics. Configure and test the artifacts in a standard-harness agent and its intended published channels.

Copilot Studio supports Adaptive Cards 1.6 and earlier, but target hosts differ:

| Profile | Maximum version | Scope | Bounded policy |
|---|---:|---|---|
| `portable-1.5` | 1.5 | Teams, Omnichannel live chat, Web Chat, and test chat | Default and recommended |
| `teams-1.5` | 1.5 | Microsoft Teams | Test Teams separately |
| `omnichannel-1.5` | 1.5 | Omnichannel live chat widget | Test live chat separately |
| `web-chat-1.6` | 1.6 | Bot Framework Web Chat | `Action.Execute` remains unsupported |
| `test-chat-1.6` | 1.6 | Copilot Studio test chat | Test-only evidence, not deployment evidence |

Every profile has a **minimum schema version of 1.5**, because this package
requires the first body element to use `TextBlock` with `style: "heading"`.
Versions 1.3 and 1.4 are unsupported by this bounded policy, regardless of host
support. The maximum versions in the table still apply.

The linter supports a deliberately conservative subset:

### Elements

* `TextBlock`
* `FactSet`
* `Container`
* `ColumnSet`
* `Column`
* `ActionSet`
* `Input.Text`
* `Input.Number`
* `Input.Date`
* `Input.Time`
* `Input.Toggle`
* `Input.ChoiceSet`

### Actions

* `Action.Submit`
* `Action.OpenUrl` with HTTPS, no URL userinfo, and a valid port when specified

This subset is not the full Adaptive Cards schema. A type outside it can be valid Adaptive Cards JSON and still fail this linter because it is outside the package's portability and safety policy.

## Template catalog

| Template | Node mode | Use | Primary outputs |
|---|---|---|---|
| `welcome-starter-prompts.json` | Interactive | Start a conversation with three stable intents | `actionSubmitId`, `intent` |
| `information-summary.json` | Informational | Present a concise record or decision summary | None |
| `data-collection-form.json` | Interactive | Collect text, category, and due date | `requestTitle`, `requestCategory`, `requestedDate`, `requestDetails` |
| `confirmation.json` | Interactive | Confirm or go back before a consequential step | `confirmDetails`, action identity |
| `approval-decision.json` | Interactive | Approve, reject, or request changes; comment is optional for approval and downstream-required for rejection or changes | `reviewComment`, action identity |
| `choice-disambiguation.json` | Interactive | Resolve one ambiguous request from a controlled list | `selectedOption`, action identity |
| `status-progress.json` | Informational | Show current state, owner, and next step | None |
| `escalation-handoff.json` | Interactive | Capture a safe handoff summary and urgency | `handoffSummary`, `urgency`, action identity |

Use the smallest card that supports the interaction. A card should not become a miniature application.

## Card package contract

Return this directory shape when file output is appropriate:

```text
adaptive-card-package/
  card.json
  card.powerfx             optional, dynamic cards only
  sample-data.json         optional, data-driven cards only
  mapping.md
  wiring.md
  validation.json
  accessibility.md
  fallback.txt
```

`card.json` is always present. For a dynamic card it is a static representative that can be linted and used to inspect structure.

## Input mapping contract

```yaml
inputs:
  - id: requestTitle
    card_type: Input.Text
    output_type: String
    copilot_output: requestTitle
    downstream_variable: Topic.requestTitle
    required: true
    sample: Replace a damaged item
    validation:
      client: isRequired and maxLength
      downstream: trim, length, policy, authorization
```

Input IDs are the stable contract. Changing an ID is a breaking change to downstream mappings.

For every input type, `isRequired` must be boolean whenever present, including
when its supplied value is `null`; invalid values report `INPUT.REQUIRED_TYPE`.
Only `true` requires a useful `errorMessage`. Omission retains optional behavior.
`isVisible` is supported on all six input types: omission and `true` keep the
input visible; `false` reports only `ACCESS.HIDDEN_INPUT`. Non-boolean values,
including `null`, report `ELEMENT.BOOLEAN_TYPE`, not an unsupported-property error.

Suggested Copilot Studio output types:

| Input type | Typical output type |
|---|---|
| `Input.Text` | String |
| `Input.ChoiceSet` | String, or a documented delimited string for multiselect |
| `Input.Number` | Number |
| `Input.Date` | String or Date after explicit conversion |
| `Input.Time` | String or Time after explicit conversion |
| `Input.Toggle` | String or Boolean after explicit conversion and schema review |

Copilot Studio creates output variables based on card inputs. Makers must inspect the generated output schema and correct types where needed.

## Action mapping contract

Every submit action includes:

```yaml
action:
  title: Approve
  data:
    cardId: approval_decision_v1
    actionId: approve
    actionSubmitId: approval_decision_v1_approve
    intent: approval.approve
    riskLevel: consequential
  downstream_branch:
    condition: cardId equals approval_decision_v1 AND actionSubmitId equals approval_decision_v1_approve
    expected_identity_source: trusted state for the currently awaited card/version
    authorization_check: required
    stale_submission_check: required
    duplicate_submission_check: required
    business_rule_check: required
```

`actionSubmitId` identifies one button on one card version. `actionId` is a short stable branch key. `intent` gives a readable machine contract.

When submit `data` is missing or is not an object, report `SUBMIT.DATA` plus one
`SUBMIT.CONTRACT` finding for each missing field: `cardId`, `actionId`,
`actionSubmitId`, `intent`, and `riskLevel`. The linter checks the fields against
an empty object without modifying the supplied payload or inventing input
collisions.

Never branch on `actionId` alone. Before selecting a branch or invoking any work,
match both `cardId` and `actionSubmitId` exactly against the currently awaited
card/version recorded in trusted conversation state. Versioned template IDs
such as `approval_decision_v1` express package identity, not schema version.
Reject missing, unknown, cross-card, expired, or consumed identities; do not
fall back to the short action key. Validate any additional action fields against
the same expected contract. Client-supplied identity is not authorization.

For retries or repeated cards with the same static template, issue fresh submit
identities or enforce a separate downstream instance/freshness check. Track the
active instance and consume it once; matching static IDs alone is not replay
protection.

No input ID may equal a top-level `data` key on a submit action that collects
inputs. This applies to every key, not just the five required contract fields.
The comparison is exact and case-sensitive; nested data keys are not flattened.
Microsoft Learn documents the [input/data merge and `associatedInputs` behavior](https://learn.microsoft.com/en-us/adaptive-cards/schema-explorer/action-submit).
The [Microsoft JavaScript renderer](https://github.com/microsoft/AdaptiveCards/blob/8b62e1d5700192578050a4fe255658811e67ce43/source/nodejs/adaptivecards/src/card-elements.ts#L6019-L6034)
copies action data first, then assigns input values by ID, overwriting collisions.
An explicit escape action with `associatedInputs: "none"` collects no inputs,
so this collision check does not apply to that action. Collision-free data is
still untrusted and must be checked downstream.

`riskLevel` is required and must be `none`, `consequential`, or `destructive`. A destructive action also requires `confirmationInputId`, `requiresExplicitConfirmation: true`, and a matching initially-off required confirmation toggle with distinct on and off values. Escape actions can use `associatedInputs: "none"` when they must bypass incomplete form validation, but they must declare `riskLevel: "none"` and `isEscapeAction: true`. Consequential and destructive actions cannot bypass associated inputs.

**Rule: a submit action must declare destructive risk whenever its title or
any string value anywhere in its data contains a listed destructive operation,
treating identifier separators and camel case like spaces, with no exceptions.**

The list is `delete`, `remove`, `revoke`, `terminate`, `destroy`, `erase`, `purge`,
`wipe`, `factory reset`, `deprovision`, `format device`, and `drop database`.
Scanning includes custom keys' string values and strings nested in objects or
arrays, but not the property names themselves. Each string is checked separately;
unrelated values are not joined into a phrase. Existing case-insensitive substring
matches are preserved, so inflections such as "deleted" still trigger the gate.
`drop_database`, `factory-reset`, `factoryReset`, and `format-device` also trigger
it. This is deliberately conservative: even "do not delete" in payload prose
requires `riskLevel: "destructive"` and the existing confirmation safeguards.
There is no exception list or card-supplied bypass. A clean result still cannot
prove that the downstream operation is reversible; classify its actual effect.

Confirmation is bound by the exact toggle ID, not a naming convention. For
example, `acknowledgeDeletion` is valid when `confirmationInputId` names it and
the toggle satisfies all confirmation requirements.

The [published Input.Toggle schema](https://github.com/microsoft/AdaptiveCards/blob/8b62e1d5700192578050a4fe255658811e67ce43/schemas/src/elements/inputs/Input.Toggle.json#L11-L24)
declares `value`'s default as the literal string `"false"`, independently of
`valueOff`. The confirmation check applies that default, then requires the
effective value to equal `valueOff` and differ from `valueOn`. An on value reports
`SAFETY.PRECHECKED_CONFIRMATION`; any other non-off/ambiguous initial value reports
`SAFETY.CONFIRMATION_INITIAL_VALUE`. Set `value` explicitly to `valueOff` when
authoring a confirmation, especially with custom on/off values. For example,
`valueOn: "false"` and `valueOff: "true"` require `value: "true"`.

This is a schema-based safety policy, not proof of host rendering. The
[JavaScript renderer's optional value property](https://github.com/microsoft/AdaptiveCards/blob/8b62e1d5700192578050a4fe255658811e67ce43/source/nodejs/adaptivecards/src/card-elements.ts#L4050-L4075)
does not declare the schema's default, and its
[checked-state test](https://github.com/microsoft/AdaptiveCards/blob/8b62e1d5700192578050a4fe255658811e67ce43/source/nodejs/adaptivecards/src/card-elements.ts#L4134-L4138)
compares the parsed value with `valueOn`. Do not assume identical omitted-value
behavior across hosts; explicitly set the off value and verify the target host.

### Conditional downstream input validation

Adaptive Card native validation applies to the card submission, not selectively
to individual submit actions. Do not set `reviewComment` as card-required in the
approval template, because that would also block Approve.

After matching the submitted `cardId` and `actionSubmitId` against the trusted
expected identity for the currently awaited card/version:

* **Approve:** `reviewComment` can be blank.
* **Reject:** trim `reviewComment`; if blank, reprompt and do not record or invoke the decision.
* **Request changes:** trim `reviewComment`; if blank, reprompt and do not record or invoke the decision.

Treat action data as untrusted input. Configure these branch rules in the topic
or downstream service rather than trusting a client-provided requirement flag.

Do not put authorization claims, secrets, or trusted server state into action data. Users and clients can submit payloads independently of the intended visual flow.

## Dynamic card contract

Use Power Fx only when the card needs values from the conversation or another node.

Produce:

1. A static representative JSON card with synthetic values.
2. A Power Fx formula derived from that structure.
3. A variable table naming every reference and scope.
4. Sample values for testing.
5. A statement that the linter validates only the static JSON.

Example variable table:

| Display purpose | Power Fx reference | Type | Sample |
|---|---|---|---|
| Request title | `Topic.RequestTitle` | String | Replace a damaged item |
| Due date | `Topic.RequestedDateText` | String | 2026-09-18 |

Do not use `${Topic.RequestTitle}` inside JSON. That is a template expression, not a Copilot Studio JSON binding contract.

## Plain-text fallback contract

An informational fallback preserves all decision-relevant facts:

```text
Request REQ-1042
Status: Waiting for review
Owner: Service desk
Next step: A reviewer will respond by 18 September 2026.
```

An interactive fallback preserves a parseable choice:

```text
Reply with one option:
1. Approve
2. Reject
3. Request changes

Include a comment after the number if needed.
```

Do not pretend `fallbackText` creates a full alternate form. It is a graceful rendering fallback. Topic-level plain-text handling must be designed separately when the interaction is business-critical.

## Security and privacy checks

Reject or redesign a card that:

* asks for a password, secret, token, API key, private key, or credential;
* embeds raw production records without minimization;
* puts trusted state or authorization assertions in action data;
* invokes an irreversible operation without confirmation;
* uses an external image without a documented need, trusted host, and privacy review;
* includes an HTTP rather than HTTPS link;
* treats a hidden field as tamper-proof.

Inspect input IDs and all visible input prompts: labels, placeholders, error
messages, and toggle titles. The linter splits camelCase/acronyms and separators,
then detects a secret term as a contiguous token sequence **anywhere** in each
candidate. No prompt words are stripped. "Enter API token to continue",
"Password confirmation", and "secret token input" are rejected without requiring
their surrounding wording to be listed. Collapsed spellings of known terms,
such as `apikey` and `secrettoken`, are also recognized as whole tokens.

This is token matching, not arbitrary substring matching: `keyword`, `keywords`,
`tokenizer`, and `secretary` stay whole words. Bare `key` and `access` are not
secret terms, so `keyFindings` and `accessLevel` need no exception.

**Rule: flag every secret term in an input ID or prompt, even when it describes
metadata; only the non-credential phrase `secret santa name` is exempt.**

There are no metadata-suffix exemptions: `secretTokenLabel` and
`privateKeyLabel` both fail; `accessTokenStatus` and `tokenUsage` both fail;
`passwordPolicy`, `passwordHelp`, `passwordPolicyUrl`, and `signingKeyStatus`
all fail. `secretTokenStatus`, `tokenCount`, `credentialType`, and
`connectionStringFormat` also fail. These are intentional conservative flags,
not assertions that every such field contains a credential. Prefer an approved
authentication/configuration surface for credential-related information; for
genuinely non-secret metadata, describe the actual non-secret value without a
secret term. Never rename a credential input merely to obtain PASS.

`secret santa name` is the sole explicit benign phrase because "Secret Santa"
names a gift-exchange activity, not authentication material. Its exception
covers only that phrase's token span, never a whole input or prompt:
"Secret Santa name and password" still fails. `secretTokenizer` has a separate
`secret` token and therefore fails, unlike the single word `tokenizer`.
`secretQuestion` and `secretQuestionAnswer` are intentionally flagged because
authentication challenge material is not confidently benign; exempting the
question phrase would also hide a request for its answer.

To request a policy change, provide synthetic field/prompt examples and the
non-secret output contract to the skill maintainer. Do not add ad hoc metadata
exceptions. A new non-credential phrase exception must add an
explicit entry to `BENIGN_INPUT_PHRASES`, document its meaning here, and include
both allowed examples and tests that nearby secret requests remain rejected.
There is no card-supplied bypass or context-word allow-list.

Non-input/action-data key scanning is unchanged: remove all non-alphanumeric
characters, lowercase, and compare exactly against the secret vocabulary.
Input exceptions never weaken that scan or the embedded-credential patterns.
This bounded policy does not understand every language or prove a card contains
no sensitive content; review the complete card and enforce controls downstream.

Cards are untrusted presentation and input surfaces. Enforce permissions, validation, idempotency, and business rules downstream.

## Accessibility and mobile checklist

* Use `label` on every input.
* Use `isRequired` and a useful `errorMessage` for required inputs.
* Put elements in the intended keyboard order.
* Start with a `TextBlock` using `style: "heading"`.
* Set `wrap: true` on all `TextBlock` elements.
* Keep instructions next to the relevant fields in JSON order.
* Use descriptive action titles.
* Reinforce color with text.
* Avoid hidden validated inputs.
* Prefer one column and short labels.
* Keep primary actions to three or fewer.
* Test with keyboard navigation and a screen reader in every target channel.

## Validation result contract

Text PASS/FAIL and passed-card counts, JSON `results[].ok`, and the process exit
code use the same policy: errors fail; warnings also fail with
`--warnings-as-errors`. Warning diagnostics remain in the warnings list.

Version components are limited to nine decimal digits before integer conversion,
independently of the Python runtime's integer-string limit; oversized components
report `ROOT.VERSION`. URL-parser failures report `OPENURL.HTTPS`, and regex
syntax, repetition-overflow, or parser-recursion failures report `INPUT.REGEX`.
These rejected values must produce diagnostics in text and JSON output, not an
uncaught traceback. Compiling a card-supplied regex does not prove safe runtime
matching in the target host; the linter does not execute that regex.

`OPENURL.HTTPS` also rejects URL userinfo (username-only, username/password, or
empty userinfo before `@`) and invalid or out-of-range ports. HTTPS does not
make embedded credentials safe. A path containing `@` is not userinfo. Hostname
trust and live network access are separate checks; the linter does not open URLs.

`JSON.DEPTH` rejects more than **64 nested object/array levels**, counting the
root object or array as level one. The limit includes all data, not just visual
containers. An iterative, string-aware preflight checks JSON text before parsing;
an iterative object preflight checks direct in-memory cards before any recursive
sensitive-data or element scan. Brackets inside strings do not count. Specific
`RecursionError` guards also return `JSON.DEPTH` if a runtime reaches its recursion
capacity during parsing or card inspection. Simplify the nesting rather than
raising the runtime limit. Over-limit malformed text or a non-object root is
rejected by the depth gate before syntax/root-type diagnostics.

```yaml
validation:
  validator: copilot-studio-adaptive-card-linter
  validator_version: 1.0.0
  scope: bounded semantic lint, not official schema validation
  profile: portable-1.5
  mode: interactive
  working_directory: skill root
  command: python scripts/validate_cards.py card.json --profile portable-1.5 --mode interactive
  errors: 0
  warnings: 0
  host_rendering_tested: false
  remaining_tests:
    - Copilot Studio test chat
    - Microsoft Teams desktop
    - Microsoft Teams mobile
    - Keyboard and screen reader
```

## Official sources

* [Adaptive Cards overview in Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/adaptive-cards-overview)
* [Ask with Adaptive Cards](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-ask-with-adaptive-card)
* [Send a message](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-send-message)
* [Power Fx expressions](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-power-fx)
* [Accessibility tips for Adaptive Cards](https://learn.microsoft.com/en-us/microsoft-copilot-studio/adaptive-card-accessibility-tips)
* [Adaptive Cards input validation](https://learn.microsoft.com/en-us/adaptive-cards/authoring-cards/input-validation)
* [Adaptive Cards schema](https://adaptivecards.io/schemas/adaptive-card.json)
