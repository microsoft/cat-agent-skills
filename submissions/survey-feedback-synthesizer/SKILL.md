---
name: survey-feedback-synthesizer
description: >-
  Use this skill whenever a user has open-text survey responses, customer
  feedback, NPS comments, or event feedback and wants it turned into themes,
  sentiment, and a prioritized action list, grounded only in what
  respondents actually wrote.
---

Turn open-text feedback into clear themes and a prioritized list, without
inventing sentiment or a theme the responses don't actually support.

## Instructions

1. Get the raw responses. Work from the actual text, not a summary of it, so
   nothing gets lost in an intermediate paraphrase before analysis starts.

2. Group responses into themes based on what they actually say, not a
   pre-decided category list. Let the themes emerge from the data; don't
   force responses into categories that don't fit well just to keep the
   structure tidy.

3. For each theme, report:
   - How many responses touched on it (a rough count or proportion, not a
     false-precision exact percentage if the sample is small).
   - The general sentiment within it (positive, negative, mixed), based on
     what respondents actually wrote, not assumed from the theme's topic.
   - One or two representative quotes, verbatim, not paraphrased into
     something more polished than the respondent actually said.

4. Distinguish a theme that shows up once from a pattern that shows up
   repeatedly. A single strongly-worded comment shouldn't be presented with
   the same weight as a pattern echoed across many responses. Say which is
   which.

5. Don't infer sentiment beyond what the text supports. A neutral factual
   comment isn't negative just because it mentions a problem in passing, and
   a comment with one critical word isn't necessarily an overall negative
   response. Read the whole comment before assigning sentiment.

6. Build a prioritized list from the themes: what shows up most often,
   what's most strongly felt (not just most frequent), and what's most
   actionable. State the basis for the ranking rather than presenting it as
   self-evident.

7. If the response volume is small enough that patterns are genuinely
   uncertain (a handful of comments, a low response rate), say so plainly
   rather than presenting a confident-sounding theme breakdown that implies
   more signal than the sample actually supports.

8. Flag anything in the responses that needs individual follow-up rather than
   aggregate analysis: a specific safety concern, a request to be contacted,
   or a comment naming a specific unresolved issue that a theme summary would
   otherwise bury.

## Guardrails

- Never invent a theme or a sentiment that isn't actually supported by the
  responses.
- Never present a single outlier comment as if it represents a broader
  pattern.
- Don't quote a respondent out of context in a way that changes what they
  meant.
- Don't apply false precision (an exact percentage) to a small or noisy
  sample. Round and caveat instead.
- If responses could reasonably identify a specific individual (a small team,
  a distinctive comment), consider whether that identifiability itself needs
  flagging before the output is shared more broadly.

## Tone

Analytical and specific. Let the data's actual signal drive the structure of
the output, not a template imposed on top of it.
