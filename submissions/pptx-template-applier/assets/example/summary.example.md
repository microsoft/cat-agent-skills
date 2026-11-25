# Example chat summary (illustrative)

Output of `summarize_run.py` for the worked example, before the line on the contact sheets is added.

```
Converted: 11 source slides into 11 slides on contoso-brand-template.potx | file: contoso-q3-review-on-template.pptx

| # | Source slide | Template layout | Why |
|---|---|---|---|
| 1 | Contoso Field Services: Q3 Review | Contoso Cover | exact match |
| 2 | Results | Contoso Divider | exact match |
| 3 | Quarter highlights | Contoso Content | exact match |
| 4 | Before and after the scheduling tool | Contoso Two Column | exact match |
| 5 | Two options for Q4 | Contoso Compare | exact match |
| 6 | Results by region | Contoso Content | exact match |
| 7 | Visits per month | Contoso Content | exact match |
| 8 | New service van | Contoso Photo | exact match |
| 9 | Lessons learned from the pilot | Contoso Content | exact match |
| 10 | Rollout path | Contoso Headline Only | exact match |
| 11 | Next steps | Contoso Content | exact match |

Fixes made (7):
- 3 template sample slide(s) removed; masters and layouts kept
- slide 4: title text shrunk from 44 to 42 pt to fit
- slide 6: table 'Table 2' rebuilt with the template's themed table style at 18 pt
- slide 7: chart 'Chart 2' rebuilt from its data; series recolored to theme accents
- slide 8: picture fitted inside the template's picture area (not cropped)
- slide 9: body text shrunk from 32 to 22 pt to fit
- slide 10: 4 free item(s) scaled into the content area (scale 1.36); colors mapped to theme
- colors mapped to theme: #7F3F98 to accent4, #1F4E79 to dk2, #4472C4 to accent1, #FFFFFF to lt1, #ED7D31 to accent6, #70AD47 to accent3

Warnings:
- none

Visual QA: lint 0 FAIL, 0 WARN | rendered 11 slides on 1 contact sheet(s)

Please check: fonts on a machine with the brand fonts installed, chart labels and number formats, picture crops, any slide listed above, and the speaker notes.
```
