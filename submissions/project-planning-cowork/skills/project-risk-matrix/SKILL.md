---
name: project-risk-matrix
description: Plots project risks in an offline 5-by-5 likelihood and severity matrix with a qualitative rating policy and supporting risk details. Use for risk heatmaps, triage, workshops, or visualizing the risk section of a RAID register.
---

# Project risk matrix

Plot risks (uncertain events) rather than issues that have already happened. Use this chart for prioritization and keep the RAID register for action tracking.

## Input and workflow

1. Use supplied risk data (table, export, notes, JSON) or real, authorized Work IQ results if available and relevant. Otherwise ask for the risk list; never imply an unavailable source was queried. Do not invent risk ratings, owners, or mitigations. The example is synthetic.
2. Normalize to UTF-8 JSON with a `project` title and `risks` array. Reuse RAID's exact risk IDs and shared fields. Each record needs a unique nonblank string `id` and `title`. Optional fields are `likelihood`, `severity`, `owner`, `mitigation`, `details`, and `task_ids` (array of task ID strings).
3. Preserve missing classifications as unassessed. Confirm any conversion from source labels or numeric scores before rendering; an invalid label fails validation. Generate the HTML and reconcile its plotted and unassessed counts against the input. Return it and highlight consequential gaps.

This is the default qualitative lookup, not arithmetic multiplication. Use the exact labels below. If a team uses a different policy, disclose the mismatch rather than presenting this mapping as its policy.

| Likelihood \ Severity | Negligible | Minor | Moderate | Significant | Severe |
|---|---|---|---|---|---|
| Very Likely | Low Med | Medium | Med Hi | High | High |
| Likely | Low | Low Med | Medium | Med Hi | High |
| Possible | Low | Low Med | Medium | Med Hi | Med Hi |
| Unlikely | Low | Low Med | Low Med | Medium | Med Hi |
| Very Unlikely | Low | Low | Low Med | Medium | Medium |

## Generate and deliver

Keep the output light regardless of host theme. Use soft Copilot Studio-inspired fills (aqua, blue, violet, magenta, and pink in order of increasing risk) with dark text. Use rounded cells with neutral gutters and regular-weight text in the grid and legend. Use the shared 90% fill opacity for cells, legend swatches and detail rating badges; keep text fully opaque. The shared design is bundled in `scripts/planning_html.py`; no separate skill or network assets are needed. Run from this skill directory with Python 3 (standard library only):

```sh
python3 scripts/render.py examples/onboarding.json risk-matrix.html
```

In the [synthetic onboarding example](examples/onboarding.json), `R-01` plots as High, `R-02` as Med Hi, and `R-03` stays unassessed because likelihood is missing. Hovering over or keyboard-focusing a plotted ID shows its full risk title; selecting the ID still jumps to details. The self-contained HTML includes a labeled 5-by-5 grid, color-and-text legend, and a full supporting table including unassessed risks. Missing fields are labeled instead of estimated.

If the host cannot run Python or return files, say so and provide the normalized inputs and local command rather than claiming generation.
