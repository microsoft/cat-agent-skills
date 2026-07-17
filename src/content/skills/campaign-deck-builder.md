---
name: Campaign Deck Builder
description: "Turn a short interview into a charming, vibrant 3-slide marketing-campaign deck by filling a bundled PowerPoint template."
agentDescription: "Use this skill whenever the user wants to create a marketing-campaign presentation, pitch deck, or launch deck for a brand. Ask the campaign questions, then run the bundled script to fill the template into a finished .pptx."
platforms: [Copilot Studio]
tags: [marketing, presentations, powerpoint, automation, scripts]
author: Adi Leibowitz
authorUrl: "https://microsoft.github.io/mcscatblog/"
authorGithub: adilei
version: 1.0.0
createdAt: 2026-07-09
updatedAt: 2026-07-09
featured: true
bundle: bundles/campaign-deck-builder.zip
---
Turn a short interview into a charming, vibrant, highly visual **3-slide
new-marketing-campaign deck** by filling a bundled PowerPoint template with a
bundled Python script.

## Step 1 — Interview the user
Ask for these (accept short answers; anything they skip gets a tasteful
default). Ask them in a single, friendly batch:

1. **Brand name**
2. **Campaign name** (the headline of the launch)
3. **Tagline** — one line that makes people lean in
4. **Target audience** — who it's for
5. **The big idea** — the single concept the campaign turns on (one sentence)
6. **Three key messages / benefits** (exactly three)
7. **Channels / activation** — where it runs (e.g. TikTok, out-of-home, retail)
8. **Call to action** — the ask
9. **Closing line** — the sign-off
10. **Brand accent color** (optional, `#RRGGBB`) — themes the whole deck

## Step 2 — Write the answers file
Save the answers as JSON. All keys are optional; `messages` is a list of three.

```json
{
  "brand_name": "Vela",
  "campaign_name": "Taste the Quiet",
  "tagline": "Botanical sparkling water for your loudest days.",
  "audience": "calm-seeking millennials",
  "big_idea": "A moment of quiet in every can.",
  "messages": ["Zero sugar, all serenity", "Adaptogens that work", "Guilt-free fizz"],
  "channels": "TikTok  ·  Out-of-home  ·  Sampling",
  "cta": "Pop the quiet.",
  "closing": "Vela — find your fizz.",
  "accent_hex": "#00A6A6"
}
```

See `assets/answers.example.json` for a complete example.

## Step 3 — Build the deck
Run the bundled script to produce the finished presentation:

```bash
python scripts/build_campaign.py answers.json campaign-deck.pptx
```

It fills `assets/campaign-template.pptx` — replacing every `{{PLACEHOLDER}}`
while preserving the design, rendering the three key messages as visual cards,
and recoloring the deck to the brand accent color when one is given. Missing
answers fall back to sensible defaults, so it always produces a complete
3-slide deck. Hand the resulting `campaign-deck.pptx` back to the user.

## Bundled files
The attached `.zip` includes:
- `scripts/build_campaign.py` — fills the template from a JSON answers file.
  Run it as `python scripts/build_campaign.py <answers.json> [output.pptx]`.
- `assets/campaign-template.pptx` — the 3-slide, highly visual template with
  `{{PLACEHOLDER}}` tokens.
- `assets/answers.example.json` — a complete sample brand you can copy and edit.
- `references/design-notes.md` — the slide/placeholder map and theming notes.

Requires `python-pptx` (`pip install python-pptx`).

## Tone
Bold, upbeat, and brand-forward. The deck should feel like a launch, not a memo.
Keep copy punchy — headlines over paragraphs.
