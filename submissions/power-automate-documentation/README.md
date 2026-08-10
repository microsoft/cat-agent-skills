# Power Automate Documentation Skill

Turns a solution `.zip` with Power Automate workflows into a readable Markdown reference: what each flow does, its trigger, the connectors it uses, every place it reads, writes, or deletes data, and how flows call each other.

## What to give it
- One or more solution `.zip` files, unpacked-solution style (`solution.xml`, `customizations.xml`, `Workflows/*.json` inside).
- Works with real Dataverse exports (from `pac solution unpack` or a live environment).
- Upload several zips at once if you want cross-checks for flows in one solution calling flows in another.

## What you get back
- One Markdown file per solution zip.
- Per flow: a plain-English purpose and walkthrough, its trigger, the connection references it uses, a read/write/delete table of every external system it touches, and which flows it calls or is called by.
- Defaults to Markdown.