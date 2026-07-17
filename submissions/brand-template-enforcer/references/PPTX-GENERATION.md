# Safe PowerPoint Template Generation

Use these procedures whenever a PowerPoint template is retrieved, inspected, or
used by a generation script.

## 1. Move the binary out of the uploads directory

Files retrieved from SharePoint may be downloaded to `/app/uploads/`. Tool hooks
can block downstream scripts from reading that directory even after analysis
preprocessing completes.

Immediately create a workspace copy. Use Python so the same procedure works
consistently across runtime environments:

```python
from pathlib import Path
import shutil

source = Path("/app/uploads/<configured-template-file>.pptx")
target = Path("/app/workspace/template.pptx")
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, target)
```

Use `/app/workspace/template.pptx` for every subsequent command. Do not pass the
original `/app/uploads/` path to generation scripts.

After the workspace copy exists, invoke the built-in `analyzing-pptx` skill on
`/app/workspace/template.pptx`. Use its output to identify slide masters,
available layouts, and placeholder indices. Keep the workspace binary; the
analysis output does not replace the template file needed for generation.

## 2. Inspect layouts and placeholder indices

Do not assume that body placeholders use index `1`. Inspect every target layout
and slide before writing:

```python
for layout in prs.slide_layouts:
    print("LAYOUT", layout.name)
    for ph in layout.placeholders:
        print(" ", ph.placeholder_format.idx, ph.name)

for slide_number, slide in enumerate(prs.slides, start=1):
    print("SLIDE", slide_number)
    for ph in slide.placeholders:
        print(" ", ph.placeholder_format.idx, ph.name)
```

Some templates use non-standard placeholder indices; for example, a body
placeholder may use `idx=12` instead of `idx=1`. Select placeholders by the
inspected index or placeholder type rather than assuming a fixed value.

For a slide-master or image-only template, content OCR may return zero
characters for every slide. When this occurs, do not retry OCR. Skip directly to
master, layout, and placeholder inspection. If the manifest sets
`inspectionMode` to `master-layout-only`, skip OCR from the start.

Example:

```python
body = next(
    ph for ph in slide.placeholders
    if ph.placeholder_format.idx == 12
)
body.text = "Body content"
```

If a layout differs, use the index reported by inspection. Do not hard-code
`12` for unrelated templates.

## 3. Remove existing slides without corrupting the package

Do not call `prs.slides._sldIdLst.clear()`. Clearing only the slide ID list
leaves relationships and slide parts orphaned inside the Office ZIP.

Use this sequence:

```python
from pptx.oxml.ns import qn

sldIdLst = prs.slides._sldIdLst
rIds = [s.get(qn("r:id")) for s in list(sldIdLst)]

for s in list(sldIdLst):
    sldIdLst.remove(s)

for rId in rIds:
    if rId in prs.part._rels:
        prs.part._rels.pop(rId)
```

This removes both the slide IDs and their presentation relationships so the
orphaned slide parts are not written to the generated package.
`_Relationships.pop()` accepts only the relationship ID; do not pass a default
argument such as `None`.

## 4. Generate from template-native layouts

1. Open `/app/workspace/template.pptx`.
2. Invoke `analyzing-pptx` on the workspace copy. For master-only templates,
   skip or stop OCR as described above.
3. Record all layout names and placeholder indices.
4. Remove sample slides with the safe relationship-aware procedure above.
5. Add new slides from the template's existing layouts.
6. Populate placeholders using inspected indices or placeholder types.
7. Preserve the template theme, master, fonts, colors, logos, and recurring
   elements.
8. Save to a new output path. Never overwrite the workspace template.
9. Reopen the generated `.pptx` and confirm that it is readable.
10. Check for leftover sample text, missing body content, overflow, and layout
   damage before returning the file.

## 5. Failure behavior

- If the SharePoint binary cannot be copied to `/app/workspace/`, stop and
  report the inaccessible source.
- If no suitable layout or placeholder exists, stop and report the inspected
  layout and placeholder list instead of silently placing content incorrectly.
- If the generated package cannot be reopened, discard it and regenerate from
  the original workspace template.
