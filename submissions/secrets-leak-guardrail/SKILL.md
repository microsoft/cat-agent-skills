---
name: secrets-leak-guardrail
description: >-
  Use this skill before sharing, sending, committing, or displaying any code,
  config, log output, or exported file the agent generated or was asked to
  paste, to catch API keys, tokens, passwords, and private keys before they
  leave the conversation.
---

## Instructions

1. This applies whenever the agent is about to: write code containing real
   configuration, paste log or console output, export a file, post to an
   external destination (chat, email, a ticket, a repository), or answer a
   question by quoting real environment variables or connection strings.

2. Run the bundled scanner when a Python environment is available:

   ```bash
   python scripts/scan_secrets.py <file-or-directory>
   ```

   It also reads stdin (`... | python scripts/scan_secrets.py -`) for pasted
   text that isn't in a file yet. Without Python available, read the content
   directly and check it against the patterns in the **What counts as a
   secret** section below.

3. The scanner flags two kinds of finding:
   - **High confidence**: matched a known credential format (AWS keys,
     GitHub/GitLab/Slack tokens, PEM private keys, JWTs, bearer tokens,
     `password=`-style connection strings).
   - **Medium confidence**: a `SECRET`/`TOKEN`/`PASSWORD`-named variable
     assigned a high-entropy value that didn't match a known format. Judge
     these yourself; entropy is a heuristic, not proof.

4. For every finding, before sharing the content: stop and tell the user
   exactly what was found and where (file/line, redacted so the actual value
   isn't repeated back). Ask whether it's a real, live credential to strip, or
   a test/example value that's fine to leave. Don't assume either way.

5. If the user confirms it's real, redact or remove it and explain what
   replaced it (an environment-variable reference, a placeholder, removal
   entirely) rather than silently deleting the line.

6. Never treat a finding as resolved just because it was mentioned once.
   Re-scan after edits before the content actually goes out.

## What counts as a secret

Cloud provider keys (AWS `AKIA…`/`ASIA…`, Google `AIza…`), platform tokens
(GitHub `ghp_…`, GitLab `glpat-…`, Slack `xox…`), API keys matching common
vendor formats, PEM-format private keys, JWTs, bearer tokens, and
`password=`/`pwd=` values inside connection strings. Anything else that reads
as a live, working credential even if its format isn't on this list. The
scanner's list is a floor, not a ceiling.

## Guardrails

- Never repeat a found secret back in full, even to describe it. Always
  redact the middle of the value.
- Never silently strip or silently allow a finding through. Every finding gets
  surfaced to the user before the content ships, no exceptions.
- Don't flag obvious documentation placeholders (`your_api_key_here`,
  `sk-EXAMPLE...`, `changeme`) as if they were real, but if genuinely
  uncertain whether something is a placeholder, ask rather than assume either
  way.
- This is a leak check, not a secrets-management setup. Don't turn a "found a
  key in this file" moment into an unsolicited lecture on secret rotation
  unless asked.

## Tone

Direct and calm: what was found, where, what it looks like, what to do next.
