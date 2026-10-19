---
name: study-flashcards
description: >-
  Use this skill whenever the user provides source material (notes, slides, a document, a PDF,
  pasted text, or a web page) and asks to "create a guide based on this", make a study guide,
  make flashcards, turn it into a quiz, "quiz me on this", or otherwise study from that material.
  Produces source-grounded flashcards and a practice quiz, defaulting to an interactive HTML
  study app for "guide" requests unless the user asks for Word, PDF, printable, or plain text.
  Do NOT use for essay grading, open-ended tutoring, multi-week course design, or trivia
  quizzes with no source material.
---

## Overview
Reads whatever study material the user provides — notes, a slide deck, a textbook chapter, a PDF,
pasted text, or a referenced web page — and produces study aids grounded strictly in that source:
a stack of flashcards (front/back) and a practice quiz with a separate answer key. Guide and study
guide requests default to the bundled interactive HTML app. Nothing in the output goes beyond what
the source material actually says.

## When to Use
- The user uploads or references notes, slides, or a document and asks for flashcards, a quiz, or
  a study guide.
- The user says "create a guide based on this" or otherwise uses "guide" for source-grounded
  learning material.
- The user names an exam, certification, or class and wants practice material built from specific
  material they provide.
- The user asks to "quiz me on [topic]" right after sharing or pointing to a document.

## When NOT to Use
- Full essay grading, open-ended Socratic tutoring, or free-form Q&A dialogue — use a general
  writing or tutoring skill instead.
- Building a complete curriculum, syllabus, or multi-week lesson plan — that's course design, not
  single-session study-aid generation.
- The user wants general knowledge quizzed with no source material of their own — this skill
  exists specifically to test recall of THEIR material, not trivia.

## Core Instructions

### Step 1: Locate the Source Material
- If the user attached or uploaded a file, read it directly — PDF, Word doc, slide deck, plain
  text, or pasted notes all count as source material.
- If the user points to a web page and you cannot open it in this environment, ask them to paste
  the text or attach the page as a file instead.
- If nothing is attached or pasted, ask the user to provide their notes or attach the file. Do
  not substitute general knowledge for material the user hasn't actually given you.
- If more than one file is available or the topic scope is unclear, confirm which material and
  which section/range to build from before generating anything.

### Step 2: Extract Concepts
- Break the material into atomic facts: terms, definitions, formulas, dates, cause/effect
  relationships, steps in a process.
- One idea per flashcard — never bundle two facts into a single card.
- Group extracted concepts by the section or heading structure already present in the source.
- Keep a source pointer for each concept (page, slide number, or heading) so every card and quiz
  answer can be traced back to where it came from.

### Step 3: Build the Flashcards
- Format: **Front** (a question, term, or prompt) → **Back** (a concise answer — ideally one
  sentence or phrase, not a paragraph).
- Prefer recall-testing phrasing ("What is…", "Why does…", "Define…", "What happens when…") over
  yes/no phrasing, which is easy to guess.
- Order cards so foundational concepts appear before concepts that depend on them.
- Scale card count to the actual material — roughly 10-30 cards for a chapter or lecture's worth
  of content. Do not pad with filler cards just to hit a number.

### Step 4: Build the Quiz
- Mix formats: multiple-choice (four options, one correct answer), true/false, and 2-3
  short-answer questions.
- Every question and every multiple-choice distractor must be grounded in the source material —
  never invent a fact, date, name, or number that isn't actually in it.
- Vary difficulty: include a few straightforward recall questions and a few that require
  connecting two concepts from the material.
- Do not place answers next to questions — the quiz should be usable as a real practice test.

### Step 5: Choose the Delivery Format
- If the request says "guide" or "study guide", deliver the interactive HTML app by default.
- If the user explicitly requests Word, PDF, printable, markdown, plain text, or an in-chat
  response, honor that format instead.
- For a non-interactive text package, present flashcards first, then quiz questions with no answers
  inline, then a separate answer key with a source reference for each answer.
- If the source material is thin or incomplete for something the user specifically asked about,
  say so explicitly instead of filling the gap with invented content.

### Step 6: Interactive HTML Delivery
- Use the bundled template at `assets/flashcard-quiz-app.html` when the user asks for a guide,
  study guide, interactive or digital experience, web app, or in-browser study/practice.
- Copy the template, then replace the `STUDY_DATA` object (clearly marked between
  `STUDY DATA` / `END STUDY DATA` comments near the top of the `<script>` block) with the actual
  generated flashcards and quiz — keep the exact same shape: `{ title, flashcards[], quiz[] }`,
  where each flashcard is `{id, front, back, topic, source}` and each quiz item is
  `{id, type: "mc"|"tf"|"short", question, options?, answer, source}`.
  Give each flashcard a short, stable `id` (e.g. `c1`, `c2`) — the app uses it as the
  spaced-repetition storage key, so keep ids stable if the user asks you to regenerate or expand
  the same deck later.
- Short-answer (`short`) items are self-checked in the app: the learner sees the expected
  `answer` after submitting and marks themselves right or wrong. Write a concise model answer.
- Treat every generated string as untrusted text, because it comes from the user's source
  material. Serialize `STUDY_DATA` as JSON (e.g. `JSON.stringify`), then make it safe for an
  inline `<script>` by replacing every `<` with `\u003c`, and U+2028 / U+2029 with `\u2028` /
  `\u2029`. Never hand-write values into the script, and never let a literal `</script>` or
  `<!--` appear inside the data block.
- Keep the app logic below the `END STUDY DATA` marker unchanged when populating a guide. The
  bundled template already includes sandbox-safe progress storage; do not replace it with direct,
  unguarded `localStorage` access.
- Deliver the filled-in file as a single, self-contained HTML file — it needs no server, no
  internet connection, and no build step; opening it in a browser is enough.
- Before delivering, check that the replaced `STUDY_DATA` block is valid JavaScript, contains no
  raw `<` characters, matches the shape above, and that every quiz `answer` is valid for its type (an option index for `mc`,
  `true`/`false` for `tf`, text for `short`).
- If your environment offers an HTML preview or browser tool, also open the file in a sandboxed
  preview (without `allow-same-origin`) and confirm card flipping, Skip/Shuffle,
  Again/Good/Easy, quiz submission, and score display work without a storage error. If no
  preview is available, skip this step — do not fail the task — and tell the user to open the
  file in any browser to try it.
- Deliver the file using whatever file-output method your platform provides (a saved file,
  attachment, or download). If the platform cannot return files, paste the full populated HTML
  in a single code block and tell the user to save it with a `.html` extension.

## Output
- **Flashcards** — numbered list or table, grouped by topic, strict Front/Back format.
- **Quiz** — numbered questions, mixed format, no inline answers.
- **Answer key** — separate section at the end; each answer cites its source location.
- **Interactive guide (default for "guide" requests)** — a single populated HTML file from
  `assets/flashcard-quiz-app.html`, with flip-card flashcards, spaced-repetition scheduling,
  a self-graded quiz, and a small progress dashboard.
- Length scales with the source: a two-page handout should yield far fewer cards than a
  40-page chapter — never inflate to hit a target count.

## Guardrails
- Never fabricate facts, numbers, names, or claims that aren't in the source material — flag
  gaps instead of guessing.
- Keep quiz answers separate from questions so the output works as a real practice test.
- If the source material conflicts with general/common knowledge, follow the source (it's what
  the user will likely be tested on) but note the discrepancy rather than silently overriding it.
- Every flashcard must test one specific, checkable fact — no vague or filler cards ("basic
  concepts," "general overview").
- If asked to quiz on material with no attached source, ask for the material rather than
  generating trivia from general knowledge.
