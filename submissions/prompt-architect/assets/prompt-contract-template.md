# Prompt Contract

## Purpose

**Task:**

**Audience / consumer:**

**Source of truth:**

**Success looks like:**

## Production prompt

```text
[Ready-to-use prompt]
```

## Variables

| Variable | Purpose | Required? | Expected shape | Missing-value behavior |
| --- | --- | --- | --- | --- |
| `{{variable}}` |  | Yes/No |  |  |

## Output contract

- Required content:
- Required structure:
- Length/detail constraints:
- Allowed labels/values, if any:
- Evidence/citation behavior:
- Content that must not be added:

## Failure behavior

| Condition | Expected behavior |
| --- | --- |
| Required input missing |  |
| Input ambiguous |  |
| Inputs conflict |  |
| Evidence insufficient |  |
| Request outside task scope |  |

## Prompt-level smoke tests

### Test 1 — Happy path

**Input:**

**Expected behavior:**

**Must not:**

### Test 2 — Missing input

**Input:**

**Expected behavior:**

**Must not:**

### Test 3 — Edge or ambiguous case

**Input:**

**Expected behavior:**

**Must not:**

### Test 4 — Regression / adversarial case

**Input:**

**Expected behavior:**

**Must not:**

## Change note

**Changed:**

**Why:**

**Behavior intentionally preserved:**

## Architecture dependencies

List only dependencies that the prompt cannot enforce by itself, such as required knowledge, tool permissions, workflow validation, approval gates, or authentication.
