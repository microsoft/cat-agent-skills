# Meeting Analyzer

A skill that turns raw meeting content into a structured intelligence report: explicit
outcomes (decisions, action items, deadlines), persona profiles of the participants, and
hidden insights — unspoken tensions, fragile agreements, implicit risks, and signals that
were never made explicit during the meeting but matter deeply to the context.

**Author:** Michael Ferro Pereira · **Platforms:** Copilot Studio, Cowork

## What it does

Summarizing is not the goal — anything can summarize. This skill reads between the lines:
it detects what participants meant but did not say, which decisions are fragile, where
misalignment is hiding, and what will cause problems two weeks from now if nobody acts on
it. Every hidden insight is delivered as evidence → interpretation → confidence level, so
interpretation is never presented as fact.

The report ends with prioritized recommended next actions tied to the findings, and is
always written in the language of the user who requested the analysis (quotes stay in the
meeting's original language).

## Supported inputs

- **Pasted text** — transcripts, meeting notes, or chat exports. Transcripts with speaker
  labels enable full persona analysis; unlabeled text still supports everything else.
- **Audio / video** — the recording is transcribed first, using whatever speech-to-text
  capability is available in the runtime environment.

**Tip:** if no transcription capability is available where the skill runs, paste the
auto-generated captions/transcript from your meeting platform instead — Microsoft Teams
(*Recap → Transcript*), Zoom (*Audio transcript* in the recording), and Google Meet
(*Transcript* attached to the calendar event) all produce one automatically when
recording/transcription is enabled.

## Example prompts

- "Analyze this meeting transcript and tell me what I'm missing." (paste transcript)
- "Summarize this call and profile the participants." (attach audio)
- "What did we actually agree on here, and how solid are those agreements?"

## What you get

1. **Executive summary** — the headline in 3–5 sentences.
2. **Explicit outcomes** — decisions (with firmness rating), action items (owner/deadline,
   with gaps flagged), key facts, open questions.
3. **Participant personas** — role, stake, communication style, influence, and behavioral
   archetype, each grounded in what the person actually said or did.
4. **Hidden insights** — the differentiating layer: avoided topics, tension and subtext,
   fragile agreements, misalignments, power dynamics, unnamed risks.
5. **Recommended next actions** — 3–7 prioritized moves based on the findings.

## Folder structure

```
meeting-analyzer/
├── metadata.json                      # Catalog metadata
├── SKILL.md                           # Agent-facing runtime instructions
├── README.md                          # This file (human-facing documentation)
├── references/
│   ├── persona-framework.md           # Persona dimensions + behavioral archetypes
│   └── hidden-insights-guide.md       # Technique catalog for the hidden layer
└── assets/
    └── report-template.md             # Output structure for the final report
```

## Notes

- The skill analyzes only the content provided; it does not fetch recordings from
  external platforms on its own.
- Hidden insights are evidence-based interpretations and should be validated with the
  meeting participants before acting on sensitive conclusions.
