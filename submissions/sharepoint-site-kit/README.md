# SharePoint Site Kit

Give your agent a program plan, deck or charter and get back a working SharePoint team site: one folder per workstream, a branded landing page in Site Pages that links to every folder, and a simple way to keep the two in step.

## What it does

The kit has three parts. Use them together or on their own.

1. **Library setup.** Creates a folder for each workstream, a "0 Program" folder that sorts first, a Lead person column, descriptions and a "Workstreams" view. It shows you the plan before it writes anything.
2. **Page builder.** Builds a self-contained, branded page for the Site Pages library in one of three modes:
   - **Static showcase HTML:** a polished landing page with cards that open each workstream folder directly.
   - **Live list-backed HTML:** a gallery page that reads items from a SharePoint list on the same site.
   - **Standard modern page (.aspx):** the fallback when HTML pages are blocked on your tenant.

   You can add **list view sections** to any HTML page: items from a list on the same site, with search, filters generated from the list's columns, and a cards or table layout. The first page the kit builds on a site becomes the site's home page through **Make homepage**, after you approve it.
3. **Upkeep.** After you rename or add folders, it rechecks the page, fixes only the links that changed and flags folders that have no card.

## Bring your own brand

Attach a PowerPoint template or brand deck (.potx or .pptx). The kit reads its theme colors and fonts and styles the page to match. With no template, it uses the site's brand kit, then a neutral default.

Every page uses the same modern design: a gradient hero with a light or dark style, a light/dark switch, a sticky section menu, an executive summary card, rounded cards in rotating theme colors and a feedback banner. The hero background is a generic pattern (soft glows, rings or a dot grid) in your colors, or a photo you attach. The kit can also take the page colors from that photo.

## Example prompts

- "Set up our SharePoint site for the program in this deck and build a landing page with our brand template."
- "Add a list view of our Resources list to the page, with filters."
- "Make the new page our site's home page."
- "Use this photo for the page header."
- "We renamed the Kickoff folder to Activate. Update the site page."

## What you need

- SharePoint access through your agent's SharePoint tools or Microsoft Graph, with rights to create folders and pages on the site.
- A browser tool for link click-tests and Make homepage.
- Python 3 with lxml and Pillow. Playwright is optional, for screenshots in the visual check.

## Good to know

- **Your approval comes first.** The kit shows you the folder plan before it creates anything, and uploads the page unpublished so you can review it before it goes live.
- **List permissions do not travel with copied data.** Before embedding saved rows or links, approve which rows may be republished to the page's audience. Access to an item, column approval, or a page preview approval alone is not enough. Without row/audience approval, the kit omits that list's saved data and links.
- **Clean page names.** Pages are named after your program, for example `AI-FinOps-Cowork-Workshop.html`, never `-preview`.
- **Publishing can be blocked by your tenant.** Some tenants block publishing HTML pages through baseline security settings. The kit runs a small probe first and falls back to SharePoint's own **Upload HTML page** command or a standard page.
- **Some steps stay manual.** Setting the site logo (the kit draws one from your page colors), folder colors and deleting old files are done by you. The kit ends with a checklist.
- **Early features.** The live list-backed mode, list view sections and Make homepage are new and have had limited testing across tenants. If something does not work on your site, open a discussion on this page so it can be fixed.
