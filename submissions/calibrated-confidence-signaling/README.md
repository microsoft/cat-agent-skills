# Calibrated Confidence Signaling

A general agent-quality skill: make the confidence in how something is said
match the confidence behind it. A verified fact, a careful inference, an
educated guess, and outright speculation shouldn't all come out sounding
equally certain.

## How it's different from grounded-citation-guardrail

grounded-citation-guardrail is specific to
answering from retrieved knowledge sources: cite what's actually there, don't
fill gaps from general knowledge. This skill is broader. It applies to any
claim in any response, including reasoning, estimates, and recommendations
that were never meant to be sourced from a document in the first place. Use
both together when answering from a knowledge base; use this one on its own
for everything else.

## The two failure modes it targets

Most agents drift to one of two extremes: hedging everything so heavily that
the one caveat that actually matters gets lost in boilerplate, or stating
everything with flat confidence so a rough guess reads exactly like a
verified fact. This skill's job is calibration, matching the wording to the
actual certainty, not maximizing either caution or confidence by default.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
