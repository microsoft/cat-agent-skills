---
name: SharePoint List Formatter
description: "Turns any SharePoint list data into a clean, consistent markdown table. Dynamic columns based on list type and query, plus a one-click Open link for every row."
agentDescription: "Use this skill any time SharePoint list is being fetched, searched, or shown to the user — whether it comes from a SharePoint/Microsoft 365 connector, a search result, a pasted export, or a fetched SharePoint URL. Apply it instead of dumping raw JSON or an ad hoc table whenever the user asks to \"pull,\" \"check,\" \"look up,\" \"find,\" or \"show\" anything from a SharePoint list, even if they never say the word \"format.\"."
platforms: [Cowork, Copilot Studio, Scout]
tags: [sharepoint, microsoft-365, productivity, tables, data]
author: Mathias Salomonsen
authorUrl: "https://www.linkedin.com/in/mathias-salomonsen-331949201"
authorGithub: adilei
version: 1.0.0
createdAt: 2026-07-17
updatedAt: 2026-07-17
---
Reformat every SharePoint result the same way so the person always gets a predictable, scannable table instead of a one-off dump, with a one-click path to open each item.

## Core columns — always present
Every table, no matter the list type, keeps these:

- **Title** — the item's name (task title, file name, event name, contact name, etc.), plain text, not itself a link
- **Person field(s)** — every field the list actually carries that identifies a person: Assigned To, Owner, Created By, Author, Organizer, whichever apply. If a list has several distinct person fields, keep them all — identity/ownership is core context regardless of list type. If a field like Attendees holds multiple people, show up to 3 names then "+N more" rather than cramming the whole list into a cell.
- **Description** — if the item has a description/notes-style field, show only its first sentence, never the full text (see formatting conventions below for how to trim it)
- **Modified** — last modified date, reformatted per the conventions below
- **Open** — always the last column, always a link built from the fixed URL pattern below

If the list genuinely has no person field, or no description field, just drop that column rather than leaving it empty — "always present" means "always present when the underlying field exists," not padding in blank columns.

Column order left to right: Title, Description, person field(s), any dynamic columns (see below), Modified, Open.

## Everything else — judge it dynamically
Beyond the core columns, decide what to include using two signals together, don't default to a fixed template:

1. **What the query is actually asking about.** If the person asks about deadlines, add Due Date. If they ask what's urgent, add Priority. If they ask about file size or storage, add File Size. Let their own words point at the fields that matter — a query about "what's overdue" wants Due Date front and center; a query about "who's been editing this" wants Modified By over Created By.
2. **What's structurally central to that type of list** — the field the table would be useless without, even if the person didn't spell it out. A task list without Status is hard to scan. A calendar table without the event's Date/Time defeats the point of showing it at all. Use judgment here the way a knowledgeable coworker would, not a rigid checklist.

Don't add a column just because the API happened to return that field — extra columns the query didn't ask for and the list type doesn't demand just add noise. Aim for lean, relevant tables: usually 4-6 columns total including the core ones.

## Row order: preserve search relevance
Don't silently re-sort rows by date, name, or anything else. When results come from a search or query, keep the relevance order the search already returned — that ordering reflects how well each item matched what was asked, and re-sorting throws that signal away. Only change the order if the user explicitly asks for one ("sort by due date", "show me overdue items first", "group by owner").

## Formatting conventions
- **Dates**: human-readable, e.g. `Jul 17, 2026` — never raw ISO strings like `2026-07-17T00:00:00Z`
- **Missing/empty fields**: an em dash `—`, applied consistently — never a blank cell, never "N/A" in one row and "-" in another
- **Status**: keep the list's own status label (don't paraphrase or invent new terms), but bold it when it signals something needing attention, e.g. **Blocked**, **Overdue**
- **Description**: show the first sentence only — split at the first `.`, `?`, or `!` followed by a space or end of string. If that first sentence itself runs long (roughly 25+ words), truncate it with `…` rather than let one row blow out the table. Never include the full description text.
- **Other long text** (comments, notes, anything that isn't the description field): still don't inline a full paragraph into a cell — leave it out or reduce it to a short phrase; "Open ↗" is there for anyone who wants the full text

## Multiple lists or a broad search
If a query spans more than one SharePoint list, don't merge them into a single table with mismatched columns — each list type will have earned a different dynamic column set anyway. Give each source its own small heading and its own table:

```
### Project Tracker
| Title | Assigned To | Description | Status | Modified | Open |
|---|---|---|---|---|---|
| API rate limiting | Marcus Webb | Add throttling to the public endpoints… | **Blocked** | Jul 15, 2026 | [Open ↗](https://contoso.sharepoint.com/sites/Engineering/lists/Project%20Tracker/DispForm.aspx?ID=42) |

### Team Documents
| Title | Author | Modified | Open |
|---|---|---|---|
| Q3 Campaign Brief.docx | Sarah Nguyen | Jul 14, 2026 | [Open ↗](https://contoso.sharepoint.com/sites/Marketing/lists/Team%20Documents/DispForm.aspx?ID=118) |
```

## Open link format — always this pattern
Don't link to whatever URL field the API happens to return (`webUrl`, `_links.self`, etc.). Every "Open" link is built from this fixed path, populated with real values pulled from the source data:

```
/sites/[site name]/lists/[list name]/DispForm.aspx?ID=[itemID]
```

- **[site name]** — the SharePoint site the list lives in (from the site URL/context in the source data)
- **[list name]** — the list's name (from the list title/internal name in the source data)
- **[itemID]** — the specific item's numeric ID (from the item's `ID`/`id` field)

Prefix the tenant's SharePoint domain if it's known (e.g. `https://contoso.sharepoint.com` + the path above) so the link is fully clickable;

Format the url as Markdown:
[Open ↗](LINK)

