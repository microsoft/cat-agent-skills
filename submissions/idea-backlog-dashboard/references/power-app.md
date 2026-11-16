# Power Apps canvas app: Idea Backlog

Tablet layout, data source: Dataverse table **Ideas**. Screens: `scrDashboard` -> `scrDetail` (+ optional `scrNew`).
Reference source: `assets/IdeaBacklog.pa.yaml` (replace `PREFIX` with the publisher prefix; the display-name syntax `'Status'` works if display names are kept).

## Dashboard (`scrDashboard`)
- Header: app title, Refresh button: `Refresh(Ideas)`.
- KPI tiles (Label text):
  - Total: `CountRows(Ideas)`
  - New: `CountRows(Filter(Ideas, Status = 'Status (Ideas)'.New))`
  - In Progress: `CountRows(Filter(Ideas, Status = 'Status (Ideas)'.'In Progress'))`
  - Completed: `CountRows(Filter(Ideas, Status = 'Status (Ideas)'.Completed))`
  - Clicking a tile sets `Set(varStatus, "New")` (etc.; "All" for total).
- Search box `txtSearch`, status tabs/dropdown `drpStatus` (All, New, In Progress, Completed).
- Gallery `galIdeas` Items:
```
SortByColumns(
  Filter(Ideas,
    (drpStatus.Selected.Value = "All" || Text(Status) = drpStatus.Selected.Value) &&
    (IsBlank(txtSearch.Text) || txtSearch.Text in Title || txtSearch.Text in Description)),
  "createdon", SortOrder.Descending)
```
  Each card: Title, submitter, priority badge, status pill coloured with
  `Switch(Text(ThisItem.Status), "New", RGBA(0,120,212,1), "In Progress", RGBA(255,140,0,1), "Completed", RGBA(16,124,16,1))`.
  `OnSelect: Set(varIdea, ThisItem); Navigate(scrDetail, ScreenTransition.Fade)`.

## Detail (`scrDetail`)
- Back button: `Navigate(scrDashboard)`.
- Shows `varIdea.Title`, `.Description`, `.'Business Value'`, `.Category`, `.Priority`, `.'Submitted By'`, `.'Submitter Email'`, `.'Status Notes'`, `Text(varIdea.'Created On', "dd mmm yyyy")`, status pill.
- Edit controls (for owners/triage): status dropdown, notes input, Save button:
```
Patch(Ideas, varIdea, {
  Status: drpEditStatus.Selected.Value,
  'Status Notes': txtNotes.Text,
  'Completed On': If(drpEditStatus.Selected.Value = 'Status (Ideas)'.Completed, Today(), Blank())});
Set(varIdea, LookUp(Ideas, Idea = varIdea.Idea)); Notify("Saved", NotificationType.Success)
```

## Publish
Save, Publish, add to solution (Solutions > IdeaBacklog > Add existing > App > Canvas app), share with users. Optional: use the Canvas Authoring MCP (`canvas-apps-canvas-app` skill) to apply the YAML.
