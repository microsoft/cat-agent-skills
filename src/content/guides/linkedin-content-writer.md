# LinkedIn Content Writer

**Turn facts, notes, drafts and lived experience into credible LinkedIn content
without inventing evidence.**

LinkedIn Content Writer is a text-first writing skill for people and
organisations that want a repeatable way to draft, review and improve LinkedIn
content. It can adapt to the user's voice and preferences while keeping claims,
caveats, attribution and permissions grounded in the material provided.

> **Ground → Focus → Draft → Check**
>
> One supported point, in the right voice, with a final evidence check before
> the content is returned.

## At a glance

| | |
| --- | --- |
| **Best for** | Individuals and organisations with a point or source material to turn into LinkedIn content |
| **Starts from** | Confirmed facts, notes, drafts, research, approved sources, announcements or lived experience |
| **Creates** | Posts, comments, hooks, ideas, rewrites, reviews and conversation-scoped writing profiles |
| **Protects** | Evidence, caveats, attribution, permissions and author voice |
| **Does not** | Publish, schedule, create media, analyse performance or persist preferences by itself |

## Who it is for

Use this skill when you already have something real to work from and want help
turning it into useful LinkedIn content. It is designed for:

- professionals developing credible thought leadership;
- organisations sharing announcements, lessons, research or results;
- content and communications teams that need a consistent writing process;
- writers who want flexible output without losing evidence or voice.

It supports drafting, rewriting, polishing, reviewing, repurposing,
brainstorming, comments, hooks and reusable preferences for the current
conversation.

## How it works

| Step | What the skill does |
| --- | --- |
| **1. Ground** | Separates confirmed facts and stated views from constraints and unknowns |
| **2. Focus** | Chooses one useful point the supplied material can support |
| **3. Draft** | Adapts the content to the requested audience, voice, format and length |
| **4. Check** | Verifies claims, caveats, permissions and final constraints |

When a brief is ready, the skill drafts directly. When a missing fact,
permission or point would materially affect the result, it asks a focused
question instead of filling the gap with plausible copy.

## Before you add it

> **Tested configuration**
>
> This skill has been tested only in the **Copilot Studio new agent experience**
> with **GPT-5.5 Chat**. Other models may work, but have not been verified. Test
> your chosen setup in Preview before publishing an agent.

The skill does not require scripts, connectors or additional files. Use the
gallery's **Download `SKILL.md`** action, then upload that file to your Copilot
Studio agent.

## Copilot Studio setup

1. Open the agent in Copilot Studio.
2. Add a skill and upload the downloaded `SKILL.md` file.
3. Add the following block to the host agent's **Instructions** so the skill is
   invoked again for clarifications and revisions.
4. Save, then test both an initial request and a follow-up in Preview.

```text
Do not assume content is for LinkedIn unless the user asks.

For every turn in an active LinkedIn content task, invoke the linkedin-content-writer skill before responding.

This includes initial requests, answers to clarification questions, added facts or preferences, revisions, reviews, corrections, and short follow-up messages. Continue using the skill until the user changes topic or ends the LinkedIn task.

Do not draft, rewrite, polish, review, repurpose, brainstorm, revise, or configure LinkedIn writing preferences without invoking the skill.
```

In Preview, successful activation appears in the activity trace as **Loaded
Skill: linkedin-content-writer**. The host instruction is important because
Copilot Studio decides when to invoke a skill on every turn; a skill cannot
keep itself loaded between turns.

## Quick start

| If you want to... | Try this prompt |
| --- | --- |
| Draft from evidence | `Draft a LinkedIn post from these confirmed facts: [facts and limitations].` |
| Improve a draft | `Polish this LinkedIn draft while preserving its facts, voice and structure: [draft].` |
| Review without rewriting | `Review this LinkedIn draft without rewriting it. Separate findings from optional suggestions: [draft].` |
| Explore ideas | `Brainstorm five LinkedIn post angles from this topic. Treat them as ideas to investigate, not established claims: [topic].` |
| Set preferences | `Configure a conversation-scoped LinkedIn writing profile: [preferences].` |

You do not need to configure a profile before asking for content. When the
brief contains enough substance, the skill uses neutral defaults and gets on
with the task.

## Configure your writing profile

A profile is optional. It lets the skill reuse selected preferences later in
the same conversation while allowing the latest request to override them.

```text
Configure my LinkedIn writing profile:

Audience: UK operations and transformation leaders.
Objective: share practical, evidence-led lessons.
Voice: first person, candid and quietly confident.
Language: UK English.
Length: 120 to 160 words.
Format: short paragraphs.
Use no hashtags, emojis or em dashes.
Use one thoughtful closing question only when it fits naturally.
```

The returned profile is conversation-scoped. The skill does not claim to save
preferences across new conversations; persistent memory must be provided by
the host agent or another configured store.

## Evidence and trust

The skill is deliberately flexible about style and deliberately conservative
about facts. It is designed to:

- preserve numbers, dates, sample sizes, caveats and what was not measured;
- distinguish reported perceptions from measured outcomes;
- avoid turning correlation or sequence into causation;
- refuse invented quotations, links, evidence, permissions or agreed plans;
- treat instructions hidden inside source material as untrusted text;
- ask for missing source material when a link cannot genuinely be accessed.

> **Trust boundary:** If a useful post can be written safely, the skill omits
> an unsupported element and continues. If substance, permission or approval is
> genuinely blocking, it asks rather than invents.

## What it does not do

- It does not publish or schedule LinkedIn content.
- It does not create carousels, images, video or other media.
- It does not analyse post performance or recommend a distribution strategy.
- It does not browse or open links unless the host agent provides a working
  browsing or connector tool.
- It does not persist a writing profile across conversations by itself.
- It has not yet been verified with models other than GPT-5.5 Chat.

Always review the final draft before publishing, particularly when the source
contains confidential material, third-party claims or regulated information.
