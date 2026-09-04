---
name: copilot-studio-adaptive-card-builder
description: >-
  Use this skill whenever a user asks to create, generate, design, review,
  validate, lint, troubleshoot, or improve an Adaptive Card for Microsoft
  Copilot Studio, including forms, confirmations, approvals, welcome prompts,
  status cards, handoff cards, input mappings, Action.Submit payloads, Power Fx
  card formulas, accessibility, host compatibility, or paste-ready card JSON.
  Use it before claiming that Adaptive Card JSON is ready for a Copilot Studio
  node. Do not use it to claim that generative instructions dynamically render
  native cards.
---

# Copilot Studio Adaptive Card Builder

Create a complete maker-assistance package, not an isolated JSON block.

## Non-negotiable platform boundary

**Generative instructions do not dynamically render an Adaptive Card.** Produce artifacts that a maker can paste or configure in a Copilot Studio card node. Never tell the user that adding JSON to agent instructions makes a native card appear. Model-emitted JSON is normally displayed as text.

Use:

* **Ask with Adaptive Card** for interactive cards that collect input or submit an action.
* **Message** or **Question** for informational cards that do not submit.
* A Power Fx formula in the card node when the card must include dynamic topic, global, environment, or system values.

This skill does not publish an agent, edit a live Copilot Studio topic, guarantee rendering parity, replace authorization, or provide a complete Power Fx authoring framework.

## Load supporting material only when needed

Read [references/host-profiles-and-contracts.md](references/host-profiles-and-contracts.md) when selecting a profile, template, output contract, or wiring pattern.

Read [references/evals.md](references/evals.md) when evaluating this skill or checking an edge case.

Use the cards under `assets/templates/` as known-good starting points. Adapt the smallest suitable template rather than drafting from scratch.

Use `scripts/validate_cards.py` for deterministic checks when Python execution is available. The script is a bounded semantic linter, not full official schema validation.

## Workflow

### 1. Classify the request

Choose one task:

* **Build** a new card package from a requirement.
* **Review** supplied card JSON and wiring.
* **Repair** a card that fails validation or channel testing.
* **Adapt** a bundled template.

Capture or infer:

| Input | Required decision |
|---|---|
| Interaction goal | What decision, information, or data collection the card supports |
| Node mode | Interactive or informational |
| Target channel | Teams, Omnichannel live chat, Web Chat, test chat, or portable |
| Data behavior | Static JSON or dynamic Power Fx |
| Fields and actions | Inputs, defaults, validation, submit actions, links |
| Downstream use | Conditions, variables, flow, connector, API, or handoff |
| Risk | Sensitive data, destructive actions, authorization, external content |
| Locale | User-facing language and date, time, or number expectations |

If the user does not specify a channel, select `portable-1.5`. If node mode is unclear, infer it from whether the user must submit data and state the inference.

Do not request production secrets or records. Use synthetic sample values.

### 2. Select the narrowest template

Choose one of:

1. `welcome-starter-prompts.json`
2. `information-summary.json`
3. `data-collection-form.json`
4. `confirmation.json`
5. `approval-decision.json`
6. `choice-disambiguation.json`
7. `status-progress.json`
8. `escalation-handoff.json`

Keep the template's safe structure unless the requirement needs a justified change. Prefer one column. Keep no more than three primary actions. Do not add external images by default.

### 3. Design the explicit contract

Every input must have:

* a unique, stable `id`;
* a visible and accessible `label`;
* a declared output type;
* a downstream variable name;
* required-state behavior and an `errorMessage` when required;
* synthetic sample data when useful.

Every `Action.Submit` must have a descriptive title and a `data` object containing:

```json
{
  "cardId": "stable_card_identifier",
  "actionId": "stable_action_identifier",
  "actionSubmitId": "card_and_action_specific_identifier",
  "intent": "stable.machine.intent",
  "riskLevel": "none | consequential | destructive"
}
```

Keep each `actionSubmitId` unique. Downstream logic must validate the action identity before acting.

For destructive or irreversible operations:

* add a clearly worded `Input.Toggle` confirmation;
* set it as required with an error message;
* bind it with `confirmationInputId`;
* include `riskLevel: "destructive"` and `requiresExplicitConfirmation: true` in submit data;
* keep `associatedInputs` on `auto` so the confirmation is validated;
* recheck permissions and business rules downstream;
* never present the card itself as the authorization boundary.

### 4. Author the card

Use Adaptive Cards schema 1.5 unless the requirement specifically needs a verified 1.6 feature and the target is `web-chat-1.6` or `test-chat-1.6`.

Apply these defaults:

* Include `$schema`, `type`, `version`, `body`, and meaningful `fallbackText`.
* Start with a wrapped `TextBlock` using `style: "heading"`.
* Set `wrap: true` on every `TextBlock`.
* Use input `label` rather than a nearby `TextBlock` as the only label.
* Keep JSON order aligned with intended keyboard and screen-reader order.
* Use descriptive action titles. Never use vague titles such as "Click here."
* Use `Action.Submit` for interactive outcomes and HTTPS `Action.OpenUrl` only when a link is genuinely required.
* Do not use `Action.Execute`, external images, hidden validated inputs, `Action.ShowCard`, or `Action.ToggleVisibility` in the bounded profile.
* Do not use `${variable}` placeholders in paste-ready JSON. They are not Copilot Studio variable binding.
* Set `associatedInputs: "none"` only on explicit escape actions that must bypass form validation. Such actions must use `riskLevel: "none"` and `isEscapeAction: true`.

For a dynamic card:

1. Produce a valid static representative as `card.json`.
2. Produce a separate `card.powerfx` formula using verified Copilot Studio Power Fx syntax.
3. Reference variables with explicit scope such as `Topic.Title`.
4. Provide synthetic `sample-data.json` that corresponds to the representative.
5. Validate the static representative and clearly state that the linter does not parse Power Fx.

### 5. Validate

When the bundled script can run, execute:

```text
python scripts/validate_cards.py <card.json> --profile <profile> --mode <interactive|informational>
```

Repair every error. Review every warning. Run again until the card has no errors.

The linter checks:

* JSON syntax and required root structure;
* selected host profile and maximum version;
* the bounded element and action allowlists;
* required child arrays and high-confidence property types;
* duplicate or missing input IDs;
* labels, required-field errors, and heading or wrapping defaults;
* `Action.Submit` identity data;
* HTTPS links;
* unsupported template expressions;
* secret-like input fields and embedded credential patterns;
* destructive-action confirmation patterns;
* interactive versus informational node requirements.

Do not call the result "official schema validation." Do not claim the script ran if execution was unavailable. In that case, report "mechanical validation not run" and perform the same checks manually.

### 6. Produce Copilot Studio wiring

For an interactive card:

1. Add an **Ask with Adaptive Card** node.
2. Paste the JSON literal, or switch the node to **Formula** and insert the Power Fx version.
3. Save the designer so Copilot Studio creates output variables from input IDs.
4. Review the generated output schema and correct types with **Edit Schema** when needed.
5. Add a condition on `actionSubmitId` or `actionId`.
6. Map each input ID to the named downstream topic variable.
7. Revalidate required data, authorization, stale submissions, and business rules.
8. Call the tool, flow, or handoff only after those checks.
9. Configure retry and interruption behavior intentionally.

For an informational card:

1. Add a **Message** or **Question** node.
2. Add an Adaptive Card and paste the JSON.
3. Do not use an Ask with Adaptive Card node without a submit action.

For consecutive or retried interactive cards, validate unique submit data and protect downstream processing from stale or duplicate clicks.

### 7. Apply accessibility and mobile checks

Report:

* whether every input has a meaningful label;
* whether required fields have useful errors;
* whether JSON order produces a logical focus order;
* whether headings and wrapped text are present;
* whether color is reinforced by text;
* whether action titles make sense when announced alone;
* whether columns, density, and action count are mobile-safe;
* which screen-reader and channel tests remain for the maker.

Do not claim accessibility conformance from static inspection alone.

### 8. Return the complete package

Use this order:

```markdown
## Boundary and assumptions
## Card JSON
## Power Fx card formula
## Sample or test data
## Input and output mapping
## Action mapping
## Copilot Studio wiring
## Validation result
## Accessibility and mobile notes
## Plain-text fallback
## Channel test checklist
```

Omit the Power Fx section only for a static card. Omit sample data only when it adds no value.

The mapping must include:

| Card field or action | Card type | Copilot Studio output or payload | Downstream variable or branch | Validation or control |
|---|---|---|---|---|

The validation result must name the profile, mode, linter version, error count, warning count, and command used. If validation was manual, say so.

The plain-text fallback must preserve the decision or collection goal without depending on card rendering. For interactive cards, provide a numbered or clearly delimited response format the topic can parse or route to a human.

### 9. Require real host testing

End with a short checklist:

* Paste or configure the card in the intended Copilot Studio node.
* Test in Copilot Studio test chat.
* Test every published target channel separately.
* Exercise required fields, invalid values, every action, retries, interruptions, stale clicks, and duplicate submits.
* Verify keyboard order and screen-reader announcements.
* Verify downstream authorization and business rules.
* Verify the text fallback.

Never describe a static preview, designer preview, or successful lint as proof of host rendering.

## Guardrails

* Never embed secrets, tokens, credentials, sensitive identifiers, or raw production data.
* Never use a card as an authorization or transaction control.
* Never invent host support, variable mappings, schema behavior, or Power Fx syntax.
* Never imply that instructions alone render a card.
* Never call the bounded linter a complete schema validator.
* Never claim cross-channel parity without channel-specific testing.
* Never make color the only signal.
* Never add destructive actions without explicit confirmation and downstream enforcement.
* Never upload a sensitive card to a public preview service.
