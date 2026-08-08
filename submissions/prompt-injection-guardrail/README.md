# Prompt Injection Guardrail

A standing rule for any agent that reads content it didn't get directly from
the user: web pages, emails, uploaded files, forwarded transcripts, tool and
API responses. Any of these can contain text written to look like an
instruction, such as "ignore your previous instructions," "as the system, I
now authorize...," or "send this file to...," aimed at the agent, not at the
human it's helping.

This skill draws the line: content is something to read and report on, never
something to obey. It also makes the agent say so when it catches an attempt,
instead of quietly complying or quietly ignoring it. Either silent path takes
the decision away from the person who should be making it.

## What it doesn't do

It can't detect every injection attempt; this is behavioral judgment, not a
scanner. It also doesn't stop the user from asking the agent to genuinely act
on something after reading it. The point is that the *content* doesn't get to
issue commands, while the *user* still can, on anything.

## Why this exists

The gallery had no skill addressing this at all. It's the same category of
risk as the accepted-practice guidance from
[OWASP's LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
(LLM01: Prompt Injection): treat retrieved content as untrusted data by
default.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
