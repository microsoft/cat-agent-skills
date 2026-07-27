# Company Memory Builder

Maintains one document about the company you're working with: terminology,
tools in use, structure, and preferences, loaded at the start of a session
and updated at the end with anything durable that was newly learned or
corrected.

## What "self-improving" actually means here

It's precise on purpose. This skill doesn't retrain a model or rewrite its
own instructions. It reads and writes one ordinary document, using
`assets/company-memory-template.md` as the starting structure. Later sessions
get better because they load a more accurate document, not because anything
about the skill changes. If you want the stronger sense of "learns and
changes its own behavior," that's a different (and much riskier) thing this
skill deliberately doesn't do.

## Why memory is treated as data, not instructions

A memory file that accumulates across sessions is a bigger target than a
one-off answer: a bad or malicious entry doesn't just affect one response, it
gets read back in every future session. So this skill treats its own memory
the same way a prompt-injection guardrail treats any other retrieved content:
entries are background facts about the company, never commands the agent
executes. And before anything gets written, it applies the same discipline a
secrets-leak or PII-redaction check would: no credentials, no identifiable
personal data, ever stored in company memory.

## Where the memory actually lives

This skill needs a real place to persist a document across sessions: a
SharePoint or OneDrive file, a Dataverse record, or an equivalent connected
store. It doesn't invent persistence a platform doesn't have. Where nothing
is configured, it says so and falls back to exporting the current memory as a
document you re-attach next session, the same honest fallback pattern as
[`own-voice-builder`](../own-voice-builder).

## What it isn't

Not a source of policy truth. It holds operational context (terminology,
tools, preferences, workflow patterns), not HR or expense policy. A skill
built to answer from actual published policy documents always outranks a
memory entry if the two ever disagree.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
