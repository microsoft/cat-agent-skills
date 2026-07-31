# Grab My Files

**Collect everything your Copilot Studio agent produced in a session into one
downloadable zip — on demand, in a single step.**

Grab My Files gathers every file the agent generated during a session, packages
them into one timestamped `.zip`, and hands it back as a download. It's a deliberately
lightweight utility: no bundled script, nothing to wire up — import the `SKILL.md` and
it works.

---

## The gap it closes

Modern Copilot Studio is a genuinely strong **file generator**. In a single session an
agent can populate a Word doc, spin up a PDF, build an Excel sheet, produce an
interactive HTML report, and more — and a busy session often produces several of them as
it works.

Handed back inline as they're made, those files are easy to use in the moment. But across
a **long session** that's harder than it sounds: revisions happen, new sets of content
get generated, and the files just live in the chat history. That infographic the agent
made early on is easy to lose track of ten tasks later — you know it exists, you just
can't find where it landed.

This skill removes the hunt. At any point you ask for everything the agent made, and you
get **one zip** — every produced file, in a single output, without scrolling back through
the conversation to collect them one at a time.

## What it does

- **Reads from `/app/created/`** — the sandbox directory where Copilot Studio writes
  generated files — **recursively**, so nested outputs (e.g. `charts/adoption.png`) are
  included, not just top-level files.
- **Filters out noise** — any earlier export (`all_files_produced_*.zip`) and hidden /
  system junk (`.DS_Store`, `Thumbs.db`, `*.tmp`, dotfiles) are skipped.
- **Packages one archive** named `all_files_produced_<YYYYMMDD_HHMMSS>.zip` (a sortable
  UTC timestamp), preserving the session's folder structure inside.
- **Cleans up safely** — the new archive is built *first*, then older exports are pruned,
  so a failed run never destroys your previous bundle.
- **Handles a subset** — ask for "just the PDFs" and it zips only the matching files.
- **Delivers the file** — returns the finished `.zip` as a download, not just a "done"
  message. If nothing qualifies, it says so plainly instead of shipping an empty zip.

## What it looks like

You ask, at any point in the session:

> **"Zip up everything you've made and give it to me."**

The agent packages the session's outputs and hands back a single download:

```
all_files_produced_20260724_223104.zip
├── onboarding_overview.pdf
├── q3_headcount.xlsx
├── launch_brief.docx
└── charts/
    └── adoption_curve.png
```

> I've packaged **4 files** into `all_files_produced_20260724_223104.zip`
> (`onboarding_overview.pdf`, `q3_headcount.xlsx`, `launch_brief.docx`,
> `charts/adoption_curve.png`). It's attached and ready to download.

## Runs when you ask

The skill triggers on natural "give me my files" phrasings, for example:

- "Export all the files you produced in this session"
- "Zip up my files so I can download them"
- "Package everything you made into one download"
- "Just zip the PDFs you created and send them over"

It deliberately **does not** fire for adjacent-but-different asks — downloading a single
named file, creating or converting a file, or persisting files to SharePoint / OneDrive /
Dataverse — so it stays out of the way of those flows.

## Where it fits

| You want to… | Grab My Files gives you… |
| --- | --- |
| **Grab everything at the end of a session** | One zip of every file produced, in a single step. |
| **Find a file that scrolled out of view** | All outputs collected in one place — no hunting the chat. |
| **Hand off a session's deliverables** | A single, cleanly named archive with the folder layout preserved. |
| **Pull just one kind of output** | A filtered zip (e.g. only the PDFs). |

## How it works

1. **Inventories `/app/created/`** recursively and selects the produced files, excluding
   prior exports and system junk.
2. **Builds the archive** — a UTC-timestamped `.zip` that preserves relative folder
   structure — then prunes older exports only after it's safely written.
3. **Returns `all_files_produced_<timestamp>.zip`** to the user as a downloadable file.

## Honest boundaries

This is a **convenience utility, not a storage or backup system.**

- Files in `/app/created/` are **ephemeral** — Copilot Studio's sandbox is cleared when
  the session ends. The zip is a way to walk away with a session's outputs, not a place
  they persist. For durable storage, route files to SharePoint, OneDrive, or Dataverse
  with a flow instead.
- It assumes generated files land in **`/app/created/`**.

## Files

- `SKILL.md` — the agent-facing trigger and packaging instructions.
