# Design notes — Campaign Deck Builder

A reference for anyone editing the template or the fill script.

## Slides & placeholders

| Slide | Purpose | Placeholders |
| --- | --- | --- |
| 1 — Cover / hero | Brand + campaign reveal | `{{BRAND_NAME}}`, `{{CAMPAIGN_NAME}}`, `{{TAGLINE}}` |
| 2 — The Big Idea | The concept + three message cards | `{{BIG_IDEA}}`, `{{AUDIENCE}}`, `{{MESSAGE_1}}`, `{{MESSAGE_2}}`, `{{MESSAGE_3}}` |
| 3 — Activation / CTA | Channels + call to action | `{{CHANNELS}}`, `{{CTA}}`, `{{CLOSING}}` |

## How the fill works

- Every `{{TOKEN}}` is authored in **its own run**, so `build_campaign.py`
  swaps the text without disturbing neighbouring formatting (e.g. the two-tone
  "For **{{AUDIENCE}}**" line on slide 2).
- `messages` may be a JSON list **or** discrete `message_1` / `message_2` /
  `message_3` keys. Only the first three are used.
- Any omitted field falls back to a tasteful default in `build_campaign.py`
  (`DEFAULTS`), so a partial answers file still yields a complete deck.

## Accent theming

- Shapes whose name starts with **`accent`** are recolored to `accent_hex`
  (the dominant hero/bar/badge/background on each slide).
- Shapes named **`deco…`** (the violet + sunny-yellow pops) are intentionally
  **left fixed** so the deck stays vibrant and charming for any brand color.
- `accent_hex` accepts `#RRGGBB`, `RRGGBB`, or shorthand `#RGB`. Invalid or
  missing values keep the template's default hot-pink accent.

## Regenerating the template

The template is produced by `generate_template.py` (kept with the project
sources, **not** shipped in the skill bundle):

    python generate_template.py assets/campaign-template.pptx

Requires `python-pptx`. The canvas is 16:9 (13.333in × 7.5in).
