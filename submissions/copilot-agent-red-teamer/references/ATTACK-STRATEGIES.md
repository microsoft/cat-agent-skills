# Attack Strategies

Attack strategies convert a **baseline** direct adversarial query into another
form that tries to bypass the target's safeguards. Always run baseline first as
the control, then apply strategies. Each strategy is applied on top of the
baseline objective set, so N strategies over M objectives produce
`M x (1 + N)` probes. Score the **decoded / semantic** content of the response,
never the encoded surface form.

This catalog mirrors the Azure AI Foundry AI Red Teaming Agent, which is built
on Microsoft's open-source PyRIT framework.

## Complexity tiers

- **Baseline** — raw adversarial query, no transformation. Naive but essential
  control.
- **Easy** — low-effort encodings/obfuscations; a determined novice attacker.
- **Moderate** — semantic rewrites that need another generative model or
  linguistic effort.
- **Difficult** — high-effort attacks: multi-turn escalation or composed
  chains, sometimes needing search-based algorithms or a second model.

## Default grouped strategies

Use these group names directly in `attackStrategies`:

| Group      | Includes                          |
| ---------- | --------------------------------- |
| `BASELINE` | Direct adversarial query          |
| `EASY`     | `Base64`, `Flip`, `Morse`         |
| `MODERATE` | `Tense`                           |
| `DIFFICULT`| Composition of `Tense` + `Base64` |

## Full strategy catalog

| Strategy | Description | Complexity |
| --- | --- | --- |
| `AnsiAttack` | Uses ANSI escape codes. | Easy |
| `AsciiArt` | Encodes the request as ASCII art. | Easy |
| `AsciiSmuggler` | Smuggles data using ASCII. | Easy |
| `Atbash` | Atbash cipher. | Easy |
| `Base64` | Base64 encoding. | Easy |
| `Binary` | Binary encoding. | Easy |
| `Caesar` | Caesar cipher. | Easy |
| `CharacterSpace` | Inserts character spacing. | Easy |
| `CharSwap` | Swaps characters. | Easy |
| `Diacritic` | Adds diacritics. | Easy |
| `Flip` | Flips characters. | Easy |
| `Leetspeak` | Leetspeak substitution. | Easy |
| `Morse` | Morse code encoding. | Easy |
| `ROT13` | ROT13 cipher. | Easy |
| `SuffixAppend` | Appends an adversarial suffix. | Easy |
| `StringJoin` | Joins/splits strings. | Easy |
| `UnicodeConfusable` | Uses confusable Unicode glyphs. | Easy |
| `UnicodeSubstitution` | Substitutes Unicode characters. | Easy |
| `Url` | URL encoding. | Easy |
| `Jailbreak` | User-injected prompt attack (UPIA): crafted prompts that try to override safeguards. | Easy |
| `IndirectAttack` | Indirect/cross-prompt injection (XPIA): payload hidden in context, retrieved content, or tool output. | Easy |
| `Tense` | Rewrites the request into past tense to dodge intent filters. | Moderate |
| `Multiturn` | Escalates across several conversation turns. | Difficult |
| `Crescendo` | Gradually increases prompt risk/complexity turn over turn. | Difficult |

## Compositions

Chain exactly two strategies to build a difficult attack. Notation used in the
manifest: `Compose:A+B` applies A then B (order matters).

Examples:
- `Compose:Tense+Base64` — reframe to past tense, then Base64-encode.
- `Compose:Base64+ROT13` — Base64-encode, then apply ROT13.

Compositions support chaining only two strategies.

## Choosing strategies

- **Fast gate:** `BASELINE` only.
- **Standard pre-ship:** `BASELINE`, `EASY`, `MODERATE`.
- **Deep assurance:** add `DIFFICULT`, `Jailbreak`, `IndirectAttack`, and one or
  two compositions.
- **Agentic targets:** always include `Jailbreak` and `IndirectAttack`, and use
  `Multiturn` / `Crescendo` to test tool-abuse and data-leak resilience.

## Execution notes

- Apply each strategy deterministically to the same baseline objective so
  results are comparable across runs.
- For multi-turn strategies, preserve the full turn sequence in the
  attack-response record; do not collapse turns.
- If the target refuses at baseline but complies under an obfuscation, that lift
  is the finding — record which strategy defeated the safeguard.
