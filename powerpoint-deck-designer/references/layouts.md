# Layouts

| slug         | Use for                                                  |
|--------------|----------------------------------------------------------|
| `title`      | Opening slide with deck title and subtitle.              |
| `section`    | Divider slide between major sections.                    |
| `content`    | Bullets or a short body paragraph.                       |
| `two-column` | Comparisons, before/after, pros vs cons.                 |
| `cards`      | 3-6 short concept tiles (e.g. process steps).            |
| `agenda`     | Numbered agenda items.                                   |
| `quote`      | Testimonials or emphasis quotes.                         |
| `closing`    | Thank-you / call-to-action.                              |
| `chart`      | Native PowerPoint chart (bar, column, line, pie, donut). |

## Tips
- Prefer `cards` over `content` when the message is a small set of parallel ideas.
- Prefer `two-column` for genuine comparisons; do not misuse it as a container.
- Keep `agenda` items <= 8. Split longer agendas into two `agenda` slides.

## Chart tips
- Prefer `column` for comparing categories; use `bar` when category labels are long.
- Use `line` for trends over time (multiple series supported, up to ~12 points).
- Use `pie` for parts-of-a-whole with <= 6 categories; `donut` for a lighter look.
- For bar/column, set `stacked: true` to stack absolute values, or `stacked: "100"` for 100% stacked (share of total across categories).
- Series/slices are colour-coded from the theme palette (primary, secondary, accent, muted).
