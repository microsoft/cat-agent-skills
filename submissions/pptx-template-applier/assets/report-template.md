# Chat report template

Short, in Markdown. Start from the output of `summarize_run.py` and add the visual check line. Keep the
whole reply under about 30 lines; link the deck rather than describing it.

```
Converted: <n> source slides into <n> slides on <template> | file: <output file>

| # | Source slide | Template layout | Why |
|---|---|---|---|
| 1 | <title> | <layout> | <exact match / fell back to ... / user override> |
...

Fixes made: <count>
- <one line per fix: text shrunk, table or chart rebuilt, pictures fitted, colors mapped, splits>

Warnings:
- <slide N: item not carried over / overflow left / lint WARN> or "none"

Visual QA: lint <n> FAIL, <n> WARN | rendered <n> slides on <n> contact sheet(s)
What I saw: <one or two lines from your look at every sheet, for example "all slides clean; slide 9 body
text is smaller (22 pt) to fit">

Please check: <fonts on a machine with the brand fonts, chart number formats, picture crops, the slides
named above, speaker notes>
```

Fallback mode replaces the first line with:

```
Restyled (fallback, the template has no usable layouts): <n> slides | file: <output file>
Brand colors: accent1 <hex>, accent2 <hex>, ... | fonts: <heading> / <body>
```

When rendering was not available, the Visual QA line reads:
"Lint only: I could not render the slides here. Please open the deck and check each slide."
