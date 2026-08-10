---
name: competitive-battlecard-builder
description: >-
  Build an interactive sales battlecard comparing your product or company
  against one or more named competitors: their likely pitch, where you win,
  where you're genuinely vulnerable, and objection-handling scripts. Use this
  skill whenever someone asks for a battlecard, competitive positioning, "how
  do we beat [competitor]", objection handling against a named competitor, or
  a sales enablement comparison asset. Also use when someone wants to add a
  competitor to an existing battlecard, update it with new intel, or
  rescope/filter an existing one down to specific competitors or categories.
---

# Competitive Battlecard Builder

## Compatibility

The interactive app output and the PowerPoint export both require Code Interpreter available to the agent. Without it, present the battlecard as formatted chat text instead.

When writing Python for Code Interpreter, avoid building scripts through shell heredocs or string concatenation that has to escape the battlecard data inline, especially once brand colors, hex codes, or parenthesized function calls like `RGBColor(...)` are involved, unbalanced quotes or parens in the data will break the heredoc before your code ever runs. Write the JSON data to its own file (`json.dump`) and have the script `json.load` it, or write the whole script as a single Python file directly rather than assembling it through shell quoting.

## Step 1: Gather the inputs

1. **Which kind of comparison this is** — ask first, before anything else: is this a sales battlecard advocating for one specific product against competitors, or a neutral, unbiased comparison with no side taken? This determines the entire shape of what you build next, not just the wording:
   - **Battlecard**: one product is "ours," the rest are competitors, compared pairwise (us vs. each one). Objection handling applies (Step 3's `objections` array), since that's inherently a sales concept, what a prospect pushes back with and how to respond.
   - **Neutral comparison**: there is no "ours." Every item is a peer, laid out as one shared matrix, all items as columns, one set of dimensions as rows, no anchor item privileged over the others. Never use the word "competitor" anywhere in this mode, not in what you say to the person, not in the data. Skip objection handling entirely, there's no seller position to defend. Gather comparably balanced detail on every item.
2. **The items being compared** — for a battlecard: your product/company (name and a one-line positioning statement) plus one or more competitors. For a neutral comparison: two or more named items, genuinely peers, no ordering implication.
3. **What the person already knows** — pitch, strengths, weaknesses for each item, and (battlecard only) objections prospects commonly raise. This is the primary source of truth. Ask for it directly rather than assuming you already know the landscape.
4. **Permission to supplement with web research** (optional) — ask whether they'd like you to search for additional public information (pricing pages, marketing claims, review sites) to round out gaps. If they decline, work only from what they gave you.

Optionally ask for **category tags** (e.g. Pricing, Security, Integration, Support, Ecosystem) if they want the comparison filterable by category as well as by item. If they don't have a preference, pick 3-5 sensible categories based on the content itself.

5. **Output format** — ask directly: an interactive HTML app (filterable, searchable, with a live scorecard tally, opens in any browser), or a PowerPoint deck (easy to present or drop into an existing deck)? Build only the one they ask for. Don't generate both by default, and don't guess, this is a real fork in what Step 4 does next.
6. **Branding** — ask whether they have a PowerPoint branding template or brand guidelines (colors, fonts, logo) this should follow. If yes, ask for either the actual `.pptx` template file, or at minimum the core details: primary/secondary colors (hex if they have them), font names, and a logo if relevant. If no, say plainly that you'll use a clean, generic default, and move on, this isn't worth belaboring if they don't have one.

## Step 2: The credibility rule (read this before writing anything)

A battlecard a sales rep can't trust is worse than no battlecard, it gets someone caught flat-footed in front of a customer. Every single claim in this skill's output carries a `source` (`"user"` or `"web"`) and a `verified` flag:

- Anything the person told you directly → `source: "user"`, `verified: true`.
- Anything you found through web research → `source: "web"`, `verified: false` until the person explicitly confirms it.

**Never invent a competitor claim.** If you don't have it from the person or a real search result, leave it out rather than filling the gap with something plausible-sounding.

Before generating the final deliverable, if there are any `web`-sourced claims, show the person exactly what you found, don't summarize or paraphrase it away. For each one, list which competitor it's about, which section it would go in (pitch, win, vulnerability, or objection), and the claim text itself, close to verbatim from the source. End with something low-friction like "Let me know if anything's off and I'll fix it before it goes into the [html app / deck]." A person should be able to skim the list and immediately spot anything wrong, not have to reconstruct what you actually found from a vague summary.

Only after that review does a claim get treated as trustworthy in the shipped battlecard. Claims that remain unconfirmed (the person didn't respond to that specific one, or explicitly said "not sure") should either be dropped or clearly marked `unverified` in the output, never silently presented as settled fact. If they flag something as wrong, correct or remove it and don't carry it into Step 3 as-is.

## Step 3: Build the data model

The two modes need genuinely different data shapes, not just different labels on the same one. Battlecard mode is inherently pairwise, "us" versus each competitor, one at a time. Neutral mode is not: there's no anchor item, every item being compared is a peer, so the data model is a real matrix, one shared set of dimensions with a value for every item, not a series of us-vs-X comparisons.

### If `mode` is `"battlecard"`

```json
{
  "mode": "battlecard",
  "us": { "name": "string", "tagline": "string" },
  "categories": ["Pricing", "Security", "..."],
  "competitors": [
    {
      "id": "slug",
      "name": "Display name",
      "theirPitch": { "text": "string", "source": "user|web", "verified": true },
      "comparison": [
        {
          "category": "one of categories[]",
          "dimension": "Short label for what's being compared, e.g. 'Recording capture method'",
          "us": { "text": "Our position on this dimension", "source": "user|web", "verified": true },
          "them": { "text": "Their position on this dimension", "source": "user|web", "verified": true },
          "edge": "us|them|even"
        }
      ],
      "objections": [
        { "objection": "What the prospect says", "response": "How to handle it", "source": "user|web", "verified": true }
      ]
    }
  ]
}
```

### If `mode` is `"neutral"`

```json
{
  "mode": "neutral",
  "items": [
    { "id": "slug", "name": "Display name", "positioning": { "text": "string", "source": "user|web", "verified": true } }
  ],
  "categories": ["Pricing", "Security", "..."],
  "matrix": [
    {
      "category": "one of categories[]",
      "dimension": "Short label for what's being compared",
      "values": {
        "item-id-1": { "text": "That item's position on this dimension", "source": "user|web", "verified": true },
        "item-id-2": { "text": "That item's position on this dimension", "source": "user|web", "verified": true }
      },
      "best": "item-id-of-whichever-item-leads-this-dimension, or null if genuinely even"
    }
  ]
}
```

`items` needs at least two entries, `values` on every `matrix` row should have an entry for every item in `items` (missing ones render as blank/unverified rather than breaking anything, but that means incomplete data, go back and fill the gap). Never use the word "competitor" anywhere in neutral-mode language, in what you say to the person or in the data itself, there isn't one, that's the whole point of this mode.

### Applies to both modes

- **Set `mode` from what they told you in Step 1.** This isn't cosmetic, it changes both the data shape above and how the app renders and labels everything.
- **Be honest about who leads a dimension** (`edge` in battlecard mode, `best` in neutral mode). Not every dimension has to favor the same side, and "even" / `null` is a legitimate, credible answer, not a cop-out. A card where every single row favors the same item reads as marketing, not something anyone can trust.
- **`category` must match one of the top-level `categories[]` values exactly**, the filtering keys off this.
- **Order `comparison`/`matrix` rows grouped by category**, all rows for one category together before moving to the next. The app inserts a category header whenever the category changes from the row before it, not once per unique category, so an interleaved order (Pricing, Security, Pricing) produces a duplicate "Pricing" header instead of one clean group.
- Keep every `text`/`response` field a plain sentence a rep could say out loud, not a bullet fragment.
- `id` values must be unique, stable slugs (used for filtering and DOM references, not shown to the user).
- Aim for real coverage: if the person only gave you two comparison points, ask for a few more before calling it done. A one-row "comparison" isn't a battlecard.

## Step 4a: If they chose HTML

Using Code Interpreter:

1. Read `assets/battlecard-app-template.html`.
2. **If the person gave you brand colors**, update the CSS custom properties near the top of the `<style>` block (`--blue`, `--green`, `--red`, `--amber`, and their `-light` companions) to match. In battlecard mode, `--green`/`--red` drive the win/loss highlighting, keep those two visually distinct from each other regardless of the brand palette, the highlighting only works if someone can tell the colors apart at a glance. In neutral mode the matrix only ever uses `--blue` for its single neutral highlight, there's no red/green to worry about there. If they gave you a logo, you can add it next to the title, but don't restructure the layout to accommodate it. If they didn't give you branding, leave the defaults as-is, don't invent a color scheme.
3. Serialize the JSON from Step 3 and escape it for safe embedding: replace every `</` with `<\/` before inserting it. This prevents an item name or claim containing the literal text `</script` from prematurely closing the embedded `<script>` tag.
   ```python
   import json
   json_str = json.dumps(battlecard_data).replace("</", "<\\/")
   ```
4. Replace the placeholder token `{{BATTLECARD_DATA_JSON}}` in the template with the escaped string.
5. Save and return the completed file as a downloadable `.html`, named after what's being compared (e.g. `battlecard-vs-competitor-name.html` for battlecard mode, `comparison-item-a-vs-item-b.html` for neutral mode).

Do this through Code Interpreter so it comes back as an actual file with a download link, printing raw HTML into the chat as text won't render it, the platform will just show the literal markup. If Code Interpreter isn't available, present the same content as formatted chat text instead: battlecard mode grouped by competitor with us/them pairs per dimension plus objection handling; neutral mode as a single table with one row per dimension and one column per item.

If the person later wants a PowerPoint version too, that's a separate follow-up ask, go to Step 4b at that point using the same underlying data.

## Step 4b: If they chose PowerPoint

**If the person gave you a `.pptx` branding template**, open it as the base presentation (`Presentation("their_template.pptx")` in `python-pptx`) and add your slides using their existing slide masters and layouts, so the deck inherits their fonts, colors, and placeholder positions rather than starting from a blank default. Only fall back to building a plain default presentation if they didn't provide one.

**If they only gave you colors/fonts (no template file)**, apply those to a default layout: use their font for headings and body text, and use their primary/secondary colors for the title slide and the "who has the edge" table highlighting, keeping the win/loss colors visually distinct from each other regardless of the palette.

**A `python-pptx` gotcha worth knowing before you hit it**: `RGBColor` is a tuple subclass, it has no `.red`/`.green`/`.blue` attributes, indexing into it (`color[0]`, `color[1]`, `color[2]`) works but attribute access throws. If you need a lighter tint of a brand color for cell shading (the same idea as the HTML app's `-light` color variants), do the math on plain integers before constructing the `RGBColor`, not after:
```python
def lighten(hex_color, amount=0.85):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return RGBColor(r, g, b)
```

**If they gave you neither**, use a clean, professional default, don't invent a brand identity, just keep it legible and uncluttered.

**Don't ship a bare `python-pptx` table dump.** Left unstyled, `python-pptx` tables render with PowerPoint's default banded-blue table style, small unstyled text, and no visual hierarchy, that reads as an obvious AI-generated afterthought, not something a rep would actually present from. Override the defaults explicitly:

- **Header row**: solid fill (brand primary color, or a dark navy/slate if no branding was given), white or light text, bold, 12-13pt.
- **Body cells**: at least 12pt, don't leave `python-pptx`'s tiny default size.
- **Category-group rows** need their own distinct fill (a light tint of the brand color, or a neutral gray), not plain text at the same visual weight as the data rows below them, otherwise they don't read as section breaks at all.
- **The title slide needs actual visual weight**: a large bold title (32pt+) and a filled background shape or color block behind it, not plain black text centered on a blank white slide.
- **Never use a thin accent stripe or colored bar as the only decoration** (a header/footer bar spanning the slide, a vertical sidebar stripe, a single-edge border on a box), that's a hallmark of low-effort AI-generated slides. If a card or section needs visual separation, use a filled shape or a solid background tint instead, not a thin line.
- Keep consistent margins (0.5"+ from every slide edge) and consistent spacing between elements, don't let gaps vary randomly from slide to slide.
- Check cell text length against column width before finalizing. If text would wrap past 3-4 lines in a cell, that's a sign to split the competitor across two slides (see the density note below), not to keep shrinking the font until it's unreadable.

If your sandbox can render the deck to an image before finalizing (for example, converting to PDF and rasterizing a page), do a quick visual pass for text overflow, overlap, or low-contrast text against its background before calling it done. If that's not available in your environment, apply the sizing and wrapping guidance above defensively, since you won't get a check on the actual output.

Structure it depends on which mode you're in, since the data shapes are genuinely different (see Step 3):

**In `"battlecard"` mode**: a title slide (your name vs the competitor(s)), then for each competitor, a comparison table with three columns (Dimension / Us / Them), one row per `comparison` entry, the `edge` winner's cell given a background fill, green tint for `"us"`, red tint for `"them"`, matching the HTML app's convention. Follow each competitor's table with a short objection-handling section (still text, that one doesn't fit a table format).

**In `"neutral"` mode**: a title slide, then one single matrix table, not a table per item. Columns are Dimension plus one column per entry in `items[]`, in the same order every time. Rows come from `matrix[]`, one row per dimension, and the `best` item's cell (if any) gets a single neutral accent fill, never red/green, since that would imply a bias that isn't there. If `best` is `null` for a row, no cell gets highlighted. There's no objection-handling section in this mode, there's no `objections` data to draw from.

In either mode, group rows by category if there are more than 5-6 comparison points, so it doesn't read as a wall of rows. If the matrix or a competitor's table has enough entries that one table would be unreadably dense (this gets tighter fast in neutral mode as `items[]` grows, a 5-column matrix eats width quickly), split by category across multiple slides rather than shrinking text to fit or cramming columns narrower than they can hold their content.

**Carry the verification status into the deck.** Any cell built from a claim with `verified: false` needs a visible marker in the cell text itself (append "(unverified)"), whether that's a `us`/`them` cell in battlecard mode or an item's cell in the neutral matrix. Don't drop the distinction just because it's no longer in an app with a badge, someone presenting from a printed or shared deck needs the same warning the HTML app gives them.

If the person later asks for a rescoped version ("just give me a deck for these two" or "only the pricing category"), regenerate a fresh `.pptx` from the same underlying data filtered to their request rather than trying to edit the existing file.

If the person later wants the HTML version too, that's a separate follow-up ask, go to Step 4a at that point using the same underlying data.

## A few things to keep in mind

- If someone wants to add an item (a competitor in battlecard mode, another peer in neutral mode) or update intel on an existing comparison, don't rebuild from scratch, extend the existing JSON data and regenerate whichever output format(s) they're using. Run any new claims through the Step 2 verification gate the same as the first time.
- If the person names an item you have no information about and declines web research, say so plainly and ask them to supply at least the basics (their positioning, and a couple of real comparison points) rather than fabricating a plausible-sounding profile.
- If they hand you branding partway through an existing session, regenerate the output with it applied rather than trying to patch colors into an already-delivered file.
- Keep tone factual throughout. In battlecard mode, this is a tool someone reads on a call, not a marketing piece. In neutral mode, this doubles: no marketing tone, and no accidental advocacy for whichever item happened to get gathered first.
