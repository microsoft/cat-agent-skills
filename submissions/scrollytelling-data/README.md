# scrollytelling-data

You can say to the Agent **"Run the Demo"** to start the demo, or upload your own data.

- **Run the Demo** — builds a full story from the bundled sample workbook (`assets/Basketball_Demo_Data.xlsx`, a multi-sheet basketball players + teams dataset).
- **Upload your own data** — drop in a `.xlsx`, `.csv`, `.json`, or a PDF with tables and the Agent builds the story from that instead.

## What you get

A single self-contained `.html` file that opens in any browser with zero setup and tells your data's story as you scroll:

- Narrative chapters generated from your data
- Interactive charts — map, bar, scatter, line, pie/donut
- Stat cards that count up, animated reveals, a progress bar, and chapter markers

## How it works

The Agent walks through five phases — inspect the data, find the story, crunch the numbers, build the page, and deliver the file — narrating friendly progress along the way. You don't need to configure anything; just ask for a data story (or say "Run the Demo") and open the resulting file.

Under the hood it loads your data into **SQLite** and runs the group-bys, sorts, totals, and other aggregations there — so the numbers in your story are computed with a real query engine and come back accurate.

## Files

- `SKILL.md` — the full workflow the Agent follows
- `assets/Basketball_Demo_Data.xlsx` — the bundled demo dataset
- `scripts/build_story.py` — reference implementation of the page generator
- `references/` — chart patterns and demo-mode notes
