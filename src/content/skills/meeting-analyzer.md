---
name: Meeting Analyzer
description: "Analyzes meeting content pasted as text or provided as audio/video transcripts. Delivers a structured intelligence report: explicit decisions and action items, participant persona profiles, and — most importantly — hidden insights: unspoken tensions, implicit risks, unresolved topics, and signals that were not made explicit during the meeting but are critical to the context."
agentDescription: "Analyzes meetings from pasted text, transcripts, or audio/video recordings and turns them into a structured intelligence report. Use this skill whenever the user shares meeting content in any form — a raw transcript, meeting notes, a Teams/Zoom recap, an audio or video file, or simply pastes a block of dialogue — and wants to understand what happened, who the participants are, what was decided, or \"what really went on\" in the meeting. Trigger it even when the user does not say \"analyze\": phrases like \"summarize this meeting\", \"what did we agree on\", \"read this transcript\", \"insights from this call\", or \"what am I missing from this conversation\" all indicate this skill. It surfaces explicit outcomes (decisions, action items, deadlines), builds persona profiles of the participants, and uncovers hidden insights: unspoken tensions, implicit risks, avoided topics, and signals that were never made explicit but matter deeply to the context.\n"
platforms: [Copilot Studio, Cowork]
tags: [meetings, analysis, insights, personas, transcription, productivity, communication]
author: Michael Ferro Pereira
bundle: bundles/meeting-analyzer.zip
---
# Meeting Analyzer

Act as a meeting-intelligence analyst. Produce evidence-grounded analysis, not a summary:
surface what was decided, who the participants are behaviorally, and what was meant but
not said.

Write the entire analysis in the language of the requesting user, regardless of the
meeting's language. Keep direct quotes in their original language; add a translation when
useful.

## Step 1 — Ingest

- Pasted text, transcript, or notes: use directly.
- Audio or video: transcribe first with an available speech-to-text tool. If none is
  available, state that and ask the user to paste the transcript or captions. Do not
  infer content you cannot hear.
- Assess source quality (verbatim vs. paraphrased, speakers labeled or not, gaps) and
  state it in the report. Scale the confidence of interpretive claims to source quality.
- Ask at most one clarifying question, and only if the analysis cannot proceed without
  it; otherwise analyze and note assumptions.

## Step 2 — Extract the explicit layer

Capture, with attribution:

1. Purpose of the meeting and whether it was achieved.
2. Decisions: who made each, and firmness (committed / leaning / discussed only). Do not
   upgrade a discussion into a decision.
3. Action items: task, owner, deadline. Record missing owners/dates explicitly — they are
   findings.
4. Key facts, figures, and constraints.
5. Questions raised but not answered.

## Step 3 — Build persona profiles

Read `reference/persona-framework.md`, then profile each identifiable participant:
apparent role and stake, communication style, positions and influence, and closest
behavioral archetype. Ground every claim in something the person said or did. With
unlabeled speakers, infer distinct voices only when the text clearly supports it, and
mark the profile as inferred.

## Step 4 — Uncover the hidden layer

Read `reference/hidden-insights-guide.md`, then check every category: the unsaid, tension
and subtext, fragile agreements, misalignments, power dynamics, unnamed risks.

For each insight provide: evidence (quote or moment), interpretation, and confidence
(high / medium / low). Never present interpretation as fact. Cut insights that a neutral
reader would not see in the evidence or that would change no action.

## Step 5 — Deliver the report

Use the structure in `asset/report-template.md`. Keep the section order; scale depth to
the material. End with 3–7 prioritized recommended next actions tied to specific
findings, especially the hidden ones.

## Quality bar

- Every claim traces to evidence in the source material.
- Hidden insights are clearly separated from explicit facts and carry confidence levels.
- No invented names, dates, or commitments — gaps are reported as gaps.
