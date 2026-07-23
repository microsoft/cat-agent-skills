# AI Demo Assistant

Spin up a believable, end-to-end **Microsoft 365 Copilot demo** from three inputs: a customer name, a line of business, and the personas you want to impress. The skill proposes demo scenarios, waits for your approval, then generates a complete content pack — sample Office files plus a written delivery/provisioning plan — so a live Copilot demo actually *lands* instead of falling flat on an empty tenant.

## Who it's for

Cloud Solution Architects, sales engineers, and anyone who runs customer-facing Copilot demos and is tired of hand-building fake emails, decks, and spreadsheets before every session.

## What it generates

- **Scenario proposals** — 3–5 realistic, high-impact "day-in-the-life" scenarios mapped to your named personas, presented for approval before anything is built.
- **Office example files** — clearly fictional Word documents, PowerPoint decks, and Excel workbooks with real, specific content (named sections, slide titles, and data columns) so Copilot has something concrete to summarize and analyze.
- **AI Demo Delivery Plan** — the provisioning recipe a human loads into the demo tenant: a persona roster with tenant-account mapping, email and Teams chat scripts, a reusable team + per-scenario channels, calendar meetings with agendas, a meeting transcript/script, **app-tagged Copilot prompt workflows** (each prompt labeled with the exact Copilot app to run it in, written with the **CRAFT framework** — Context, Role, Action, Format, Target audience — and naming its grounding file *inline* so it attaches to the right artifact live on stage), and a **sample-file contents appendix** describing exactly what's inside every generated file.
- **Seeding checklist / file manifest** — a per-file table describing exactly what each file holds and where it gets seeded, so loading the tenant is a checklist, not a guessing game.

## What can and can't be auto-seeded

| Asset | Auto-seed? | How |
|-------|-----------|-----|
| Word / PowerPoint / Excel files | **Yes** | Creates a customer-named OneDrive folder and uploads the files (optional, on request). |
| Teams chat messages | **Optional, with constraints** | Posts live via Graph — timestamped *now*, and each account posts only as itself. |
| Email threads | No | Drafted as scripts for manual paste/seed. |
| Calendar meetings | No | Drafted as scripts with agendas for manual creation. |
| Meeting recordings / transcripts | **No API path** | A transcript/script is generated; a real recording only exists after a live recorded Teams meeting. |

## How to use it

1. Ask Copilot to **"set up a Copilot demo"** (or "build demo content for a customer", "create a demo delivery plan", etc.) and give it the customer, line of business, and personas.
2. Review the proposed scenarios and approve, edit, or swap them.
3. Collect the generated files and Delivery Plan from your output folder.
4. Optionally ask it to **seed the files to OneDrive** or **post the Teams chats** live.
5. Load the content into your demo tenant **24–72 hours before** the demo — Copilot answers from the Microsoft Graph semantic index, which needs time to pick up freshly seeded content.

## Safety & scope

- **All content is fictional dummy data** — invented names, companies, numbers, and dates. Never real customer PII or a production tenant.
- **Scoped live writes only** — the only live actions are creating a OneDrive folder + uploading files, and (optionally) posting Teams chat messages, both gated on explicit confirmation. It never auto-sends email, never auto-books calendar events, and never writes to a production tenant.
- **No backdating, no fake recordings** — the skill is explicit about what Graph can and can't do and won't claim otherwise.

---

*Built for Microsoft 365 Copilot Cowork. Shared under the repository's MIT license.*
