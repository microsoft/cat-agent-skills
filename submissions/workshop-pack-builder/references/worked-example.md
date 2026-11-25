# Worked example: Contoso journey mapping workshop

A short end-to-end run on a fictional, public topic. Contoso Outdoor Gear is fictional; every number is
illustrative.

## The request

"Build a 90-minute virtual workshop from this guide for 16 support and store team leads who have never
done journey mapping. Use breakout rooms."

Source: `assets/example/contoso-journey-mapping-guide.md` (a fictional internal guide).

## 1. Source map

```bash
python scripts/build_source_map.py assets/example/contoso-journey-mapping-guide.md \
  --json-out working/source_map.json --md-out working/source_map.md
```

Result: one source (S1), eight sections (`S1.sec1` to `S1.sec8`). Numbers to cite exactly: the 2025 pilot,
11 pain points, 18 percent fewer contacts over eight weeks.

## 2. Intake

Already answered by the request: audience, level, size, length, format, tool. Asked once: "Do you have a
PowerPoint template? Do you want a pre-read, survey and follow-up email draft?" Answer: no template; yes
to all three.

## 3. Objectives

- O1 Explain the difference between a journey map and a process diagram (S1.sec2).
- O2 Map one customer journey across the five stages (S1.sec3, S1.sec4).
- O3 Identify pain points and moments that matter using evidence (S1.sec5, S1.sec6).
- O4 Commit to one improvement with a named owner and a check date (S1.sec8).

## 4. Modules and timing

```bash
python scripts/timing.py plan --total 90 "Welcome=8" "What a journey map is=14" "Map one journey=28" \
  "Break=5!" "Pain points=18" "Commit=9"
```

Result: 10, 15, 30, 5, 20, 10. Total 90.

## 5. Exercises

- Map the online returns journey (guided mapping; 20 minutes in a 30-minute
  module).
- Circle the pain points (pattern: hunt; 15 minutes in a 20-minute module), using the cited illustrative
  pilot finding about entering an order number twice. Other unsupported steps stay open questions.
- Three discussions: chat waterfall, compare two illustrative snippets shown on the discussion slide,
  commitment round in chat. The facilitator guide repeats the snippets if screen sharing fails.

The workbook supplies exercise sheets 1 and 2 with a "Your work" area. The first map can be recorded
there if the whiteboard fails. The closing commitment uses chat and the annotated map, not a third
exercise sheet. No separate evidence cards, example map or meeting poll is needed.

Each has an objective, timebox, steps, materials, expected output, debrief questions, fallback and
sources.

## 6. Gaps recorded

- The guide does not say how long a session should take; the length comes from the intake.
- The guide supplies no detailed evidence for every journey step; unsupported steps remain open questions.

## 7. Build and check

```bash
python scripts/build_deck.py assets/example/workshop.example.json --out working/pack/deck.pptx \
  --source-map working/source_map.json
python scripts/build_docs.py assets/example/workshop.example.json --out-dir working/pack \
  --source-map working/source_map.json --html
python scripts/check_pack.py assets/example/workshop.example.json --source-map working/source_map.json \
  --pack-dir working/pack --deck working/pack/deck.pptx
python scripts/deck_preview.py working/pack/deck.pptx --out-dir working/preview
```

Expected output: 22 slides and 8 supporting files. Run the quality gate, then review the contact sheets
slide by slide before calling the pack ready.
