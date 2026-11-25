# Microsoft Graph and tool notes

Use the agent's SharePoint tools where they exist; the Graph calls below are what they map to and what to call when a tool is missing. All calls need delegated permissions; page and folder creation needs `Sites.ReadWrite.All` (or a narrower grant your tenant uses). Never paste access tokens into pages, files or chat.

## Capability map

| Capability | Typical agent tool | Graph call |
|---|---|---|
| Resolve a site | site lookup / search sites | `GET /sites/{hostname}:/sites/{path}` (or `:/teams/{path}`) |
| Default Documents drive | default drive / list site drives | `GET /sites/{site-id}/drive` |
| List folders | drive children | `GET /drives/{drive-id}/root/children?$filter=folder ne null` (or filter client-side) |
| Create folder | create folder | `POST /drives/{drive-id}/root/children` body `{"name":"Activate","folder":{},"@microsoft.graph.conflictBehavior":"fail"}` |
| Copy a file into 0 Program | upload file content or a copy call | `POST /drives/{drive-id}/items/{item-id}/copy` body `{"parentReference":{"driveId":"...","id":"<0 Program id>"}}` (async, returns a monitor URL) |
| Find a list by name (list view) | list lists | `GET /sites/{site-id}/lists?$select=id,name,displayName,webUrl,list` then keep entries where `list.hidden` is false and `list.template` is `genericList` (or another non-library template); skip `documentLibrary` unless the user asked for a library. Match `displayName` case-insensitively; several matches: ask which |
| List columns | list columns / list schema | `GET /sites/{site-id}/lists/{list-id}/columns` (input for `build_list_view.py --columns`) |
| Sample items (list view proposal only) | list items | `GET /sites/{site-id}/lists/{list-id}/items?$expand=fields&$top=200`; person and lookup fields come back as `<Name>LookupId` unless the tool expands them |
| Complete items (allowlist or snapshot) | list items with continuation | Start with the items call above, then follow every `@odata.nextLink` exactly (or the tool's continuation token) until none remains. Combine all `value` arrays into one `{"value":[...]}` payload; verify the total count. A 200-item sample is not a complete export. |
| Add Lead column | update list schema | `POST /sites/{site-id}/lists/{list-id}/columns` body `{"name":"Lead","displayName":"Lead","personOrGroup":{"allowMultipleSelection":false,"chooseFromType":"peopleOnly"}}` |
| Set folder Description / Lead | update list item | `PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}/fields` body `{"_ExtendedDescription":"..."}`; person: `{"LeadLookupId":"<user id in the site's User Information List>"}` |
| Create a view | (no Graph endpoint) | Use the list schema tool if it supports views, else the browser, else the manual steps in SKILL.md |
| Find Site Pages | list items | `GET /sites/{site-id}/lists/Site Pages/items?$expand=driveItem` (URL-encode the space). The name `SitePages` returns 404, and the library is hidden from the plain lists listing. |
| Site Pages drive | list drive | `GET /sites/{site-id}/lists/{site-pages-list-id}/drive` |
| Upload HTML | upload file content | `PUT /drives/{site-pages-drive-id}/root:/{Page-Name}.html:/content` (Content-Type `text/html`) |
| Set the site home page (Make homepage) | browser tool (Site Pages > ... > Make homepage) | **No Graph v1.0 endpoint.** SharePoint REST instead (below) |
| Brand kit | brand kit tools | Tenant or site brand kit colors and fonts; map to `extract_brand.py --palette` keys (below) |

Notes:
- The built-in Description column of a document library usually has the internal name `_ExtendedDescription`. Confirm it in the column listing before writing; if the library has no such column, ask before adding one.
- Person fields are written through `<Column>LookupId`, which needs the person's ID in the site's User Information List. If that ID is not available, leave the field empty and add the person to the manual-steps list (Edit in grid view).
- For proposals and page data, require an expanded tool payload or resolve person/lookup IDs against the site's User Information List or the referenced lookup list using authorized tools. Store only audience-approved display names/labels under the original mapped column names (for example `Owners`), not under `OwnersLookupId`. Never guess a display value or show a raw ID as a name. If resolution is unavailable, stop and request expanded data or explicitly exclude that column; verify the live viewer also supplies expanded values before publication.
- Folder creation with `conflictBehavior: fail` never overwrites an existing folder; report existing folders as "already there".

## Site home page (no Graph endpoint)

Graph v1.0 cannot read or set a site's welcome page. Prefer the browser (Site Pages > select the page > ... (More) > Make homepage). Use SharePoint REST only when the agent has a connection that can call `<site>/_api` with a SharePoint token (it usually does not; a Graph token does not work there):

```http
POST https://contoso.sharepoint.com/sites/ContosoActivation/_api/web/rootfolder
Accept: application/json;odata=verbose
Content-Type: application/json;odata=verbose
X-HTTP-Method: MERGE
IF-MATCH: *
X-RequestDigest: <form digest, if the connection needs one>

{"__metadata":{"type":"SP.Folder"},"WelcomePage":"SitePages/Contoso-Activation-Program.html"}
```

Read the current home page first so it can be restored: `GET <site>/_api/web/rootfolder?$select=WelcomePage` (for example `SitePages/Home.aspx`). Needs site owner or edit rights; a 403 means hand the manual step to a site owner. Set it only on a published page, then load the site root to confirm. Unverified for `.html` pages: if the site root does not load the page, set `WelcomePage` back and use the link fallback in SKILL.md 2.8.

## Standard modern page (fallback mode)

Beta endpoint, not supported for production use. Pin this payload shape and re-check the Graph docs before relying on it; if a v1.0 pages endpoint is available in the tenant, prefer it with the same body.

```http
POST https://graph.microsoft.com/beta/sites/{site-id}/pages
Content-Type: application/json

{
  "@odata.type": "#microsoft.graph.sitePage",
  "name": "activation.aspx",
  "title": "Contoso Activation Program",
  "pageLayout": "article",
  "showComments": false,
  "showRecommendedPages": false,
  "canvasLayout": {
    "horizontalSections": [
      {
        "layout": "oneColumn",
        "id": "1",
        "emphasis": "none",
        "columns": [
          { "id": "1", "width": 12, "webparts": [
            { "@odata.type": "#microsoft.graph.textWebPart",
              "innerHtml": "<h2>Activation that pays back</h2><p>Executive summary...</p>" }
          ] }
        ]
      },
      {
        "layout": "threeColumns",
        "id": "2",
        "emphasis": "soft",
        "columns": [
          { "id": "1", "width": 4, "webparts": [ { "@odata.type": "#microsoft.graph.textWebPart", "innerHtml": "<h3>Activate</h3><p>...</p><p><a href=\"<folder link>\">Open folder</a></p>" } ] },
          { "id": "2", "width": 4, "webparts": [ { "@odata.type": "#microsoft.graph.textWebPart", "innerHtml": "<h3>Adopt</h3>" } ] },
          { "id": "3", "width": 4, "webparts": [ { "@odata.type": "#microsoft.graph.textWebPart", "innerHtml": "<h3>Expand</h3>" } ] }
        ]
      }
    ]
  }
}
```

Then publish: `POST /beta/sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage/publish`.

Limits: text web parts accept basic HTML only (headings, paragraphs, lists, links, bold, italic); classes and styles are stripped, so branding comes from the site theme, section emphasis and the user's own web parts. Hero, Quick links and List web parts are best added by the user in the page editor (manual step).

## Brand kit to palette keys

| Brand kit color | `--palette` key |
|---|---|
| Primary / main brand color | `accent1` |
| Secondary | `accent2` |
| Tertiary or third color | `accent3` |
| Darkest neutral or text | `dk1` |
| Background | `lt1` |
| Deep or header color | `dk2` |
| Light neutral | `lt2` |
| Heading font | `major_font` |
| Body font | `minor_font` |
