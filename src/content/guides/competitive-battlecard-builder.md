# Competitive Battlecard Builder

Builds an interactive comparison app from what you know about your product and one or more other items, either a sales battlecard advocating for your product against named competitors, or a genuinely neutral comparison with no side taken. Exports to PowerPoint on request.

## Why this skill exists

Most "battlecard" generators quietly assume the answer is always "we win." That's not credible, and it doesn't survive contact with a sharp prospect who's done their own research. This skill treats every claim as either confirmed by the person or found on the web and explicitly unverified, and it won't ship a claim as settled fact until a human has actually looked at it.

It also refuses to pretend neutral comparisons and sales battlecards are the same shape of problem wearing different colors. A battlecard is inherently pairwise, us versus each competitor. A neutral comparison has no "us," every item is a peer, laid out as a real matrix. The skill builds genuinely different data and renders genuinely different UI depending on which one you asked for, down to never using the word "competitor" anywhere in neutral mode.

## What makes this different from just asking an agent to "compare X and Y"

- **Two real modes, not one mode with relabeled fields.** Battlecard mode is pairwise; neutral mode is a true N-way matrix with every item as a peer column.
- **Verified vs. unverified, tracked per claim.** Anything sourced from the web sits behind an explicit human review step before it's treated as trustworthy, and stays visibly flagged in the output if it isn't confirmed.
- **Honest by design.** Battlecard mode expects real vulnerabilities, not just wins. Neutral mode allows "even" as a legitimate answer instead of forcing a winner on every row.
- **A compact scorecard, not a duplicate table.** The summary at the top is aggregate counts, not another copy of the detailed comparison sitting right below it.
- **Filterable, searchable, and copyable.** Filter by item or category, search across every dimension, and copy any row as a ready-to-use talking point.
- **Branding-aware.** Give it a PowerPoint template or just your brand colors, and both the HTML app and the PowerPoint export pick them up, without ever letting a brand palette blur the win/loss or leader signal past the point of being readable.

## Requirements

Both the HTML app and the PowerPoint export require Code Interpreter enabled on the Copilot Studio agent. Without it, the skill falls back to presenting the comparison as formatted chat text.

## Author

Michael Heath ([Get Automating](https://getautomating.com))
