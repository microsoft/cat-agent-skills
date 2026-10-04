# Cowork use case one-pager

Turns something you actually did in Cowork - a conversation, a scheduled task, a workflow you
built - into a single, printable HTML page you can share internally: a headline outcome, a
short narrative, the impact figures, the workflow steps and the outputs it produces.

It's the write-up you'd otherwise spend half an hour formatting, in the house layout, in about
a minute.

## Before you start

Nothing to install and no accounts to connect. The skill ships its own page template
(`assets/template.html`) and writes a self-contained HTML file - no scripts, no dependencies,
no internet access needed.

What it *does* need is source material. Best results come from running it at the end of the
conversation where the work actually happened, so it can read the workflow directly. Failing
that, attach the task brief, the prompt or a previous output - or just describe the workflow
in a few sentences.

## How to use it

Ask for it in plain language:

- "Write this up as a Cowork use case"
- "Make a one-pager for this workflow"
- "Document what this scheduled task does as a case example"
- "Turn what we just did into a slide-style use case summary"

What happens next:

1. **It reads the workflow** - what triggers it, what goes in, what Cowork does step by step,
   what comes out and who receives it.
2. **It drafts the page** - a title framed as the outcome, a short use case paragraph, up to
   four at-a-glance chips (how often it runs, what triggers it, sources, audience), 4–6
   workflow steps and a strip of outputs.
3. **It estimates the impact and shows its working** - manual time versus Cowork time, plus
   one to three metric lines. It will show you the arithmetic and ask you to confirm or
   correct the numbers.
4. **It saves the page** to your files as
   `<use-case>_<your-name>_<YYYY-MM-DD-HHmm>.html`, e.g.
   `media-monitoring-reporting_tim-sparks_2026-08-05-1604.html`.

Open it in a browser to read or share it; print to PDF if you need a fixed copy.

## Good to know

- **It's one page, not a deck.** If you want multiple slides ask for a PowerPoint instead, and
  for an editable document ask for Word or Excel. This skill produces a single printable HTML
  page.
- **Numbers are estimates until you say otherwise.** Time saved and money saved are derived
  from the workflow, labelled as estimates, and shown with the arithmetic. Money figures stay
  as a `$000/month` placeholder unless you supply a rate. Confirm the figures before you share
  the page.
- **It won't invent facts.** If something isn't in the source material or confirmed by you, the
  placeholder stays in rather than a plausible-looking number.
- **Made to be shared, so keep it clean.** Client names, personal data and
  Restricted/Confidential material stay out unless you confirm they're cleared for the
  audience. Describe the account type ("six of the organisation's largest client accounts")
  rather than naming it, and leave the name off entirely for an anonymised version - the file
  is then named `..._anonymous_...`.
- **The avatar is always a generic silhouette**, in one of seven colour shades. Never a real
  photo.
- **It only ever writes a new file.** Nothing on disk is changed or deleted.

## Tips

- Give it a role line for the person card ("Media monitoring & client reporting") if your AD
  description isn't acceptable.
- If the workflow is scheduled, say so and how often. Frequency is what makes the impact
  arithmetic credible.
- Have the volume figures to hand - number of accounts, reports, inboxes or files per run.
  That single number does most of the work in the impact column.
