---
name: grab-my-files
description: Bundle every file the agent produced in this session into a single timestamped .zip and hand it back as a download. Use when the user asks to "export all produced files", "zip my files", "package everything you made", "bundle my files", "give me all the files", or similar. Files are read from /app/created/. Do NOT use to fetch a single named file the user can already download on its own, to create or convert a file, or to save/persist files to SharePoint, OneDrive, or Dataverse — those are separate flows, not a local zip-and-download.
---

# Grab My Files

## When to use

Invoke when the user says anything like:
- "export all produced files" / "package everything"
- "zip up my files" / "bundle my files"
- "give me everything you made" / "download all the outputs"

If the user names a subset ("just the PDFs", "only the report"), honor that and zip
only the matching files, but still follow the rules below.

## How to export

1. **Inspect the folder.** List `/app/created/` **recursively** so nested outputs
   (e.g. `/app/created/charts/foo.png`) are included, not just top-level files.
2. **Decide what goes in.** Include every produced file **except**:
   - any previous export archive (files named `all_files_produced_*.zip`), and
   - hidden/system junk (`.DS_Store`, `Thumbs.db`, `*.tmp`, dotfiles).
3. **Prune old exports *after* the new one is written.** Build the new archive
   first, then delete any *other* `all_files_produced_*.zip` in `/app/created/`.
   Doing it in this order means a failed build never destroys the user's previous
   bundle, and no old export gets nested inside the new one.
4. **Handle the empty case.** If nothing qualifies, tell the user there are no
   produced files to export and stop — do not create an empty zip.
5. **Name the archive** `all_files_produced_<YYYYMMDD_HHMMSS>.zip` — a sortable,
   UTC timestamp — and write it to `/app/created/`.
6. **Preserve structure.** Keep the relative folder layout inside the zip so files
   restore to the same subfolders they came from.
7. **Deliver it.** Return the finished `.zip` to the user as a download — don't just
   report that it was created. In Copilot Studio, writing the file to `/app/created/`
   surfaces it as a downloadable attachment; make sure the user gets that link.

## Confirm to the user

After the zip is written, reply with:
- the archive name (including its timestamp),
- the total count of files packaged, plus a list of up to 50 packaged paths (sorted). If there are more than 50, list the first 50 and say how many additional files were included, and
- a note that the zip is attached and ready to download.

> I've packaged **3 file(s)** into **`all_files_produced_20260724_215812.zip`**:
> - `onboarding_overview.pdf`
> - `onboarding_overview.docx`
> - `charts/headcount.png`
>
> It's attached above and ready to download. 📦
