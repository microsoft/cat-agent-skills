from collections import defaultdict

from planning_html import (LEVELS, LIKELIHOODS, POLICY, RISK_STYLE, SEVERITIES, badge, h, id_list,
                           ids, page, records, risk_rating, run, scroll, show, table)


CSS = RISK_STYLE + """
.level-0 { --risk-fill: #75e7d5; }
.level-1 { --risk-fill: #7ca9f7; }
.level-2 { --risk-fill: #b48ff8; }
.level-3 { --risk-fill: #e980ec; }
.level-4 { --risk-fill: #e571ab; }
:is(.level-0, .level-1, .level-2, .level-3, .level-4) { --risk-ink: #171717; }
.matrix { min-width: 38rem; table-layout: fixed; border-collapse: separate; border-spacing: 4px; }
.matrix th, .matrix td { border: 0; border-radius: 10px; font-weight: 400; }
.matrix tbody td { height: 3.6rem; padding: .45rem .65rem; color: var(--risk-ink);
  background: var(--risk-fill);
  background-color: color-mix(in srgb, var(--risk-fill) var(--text-fill-opacity), transparent); }
.matrix th:first-child { width: 8.6rem; }
.matrix tbody th, .matrix thead th:first-child { position: sticky; left: 0; z-index: 1; }
.matrix td a { display: inline-block; margin: .25rem .25rem 0 0; font-size: .78rem; color: inherit; }
.matrix td a:focus-visible { outline-color: currentColor; outline-offset: 2px; }
.matrix td .level:not(.level-unknown) { padding-left: 0; background: transparent; }
.matrix .level, .legend .level { font-weight: 400; }
.legend { display: flex; flex-wrap: wrap; align-items: center; gap: .45rem; font-size: .79rem; }
.risk-title-card { position: fixed; z-index: 3; width: max-content;
  max-width: min(22rem, calc(100vw - 1.5rem)); max-height: calc(100dvh - 1.5rem); overflow: auto;
  padding: .5rem .75rem; background: var(--surface); color: var(--text);
  border: 1px solid var(--border); border-radius: 10px; box-shadow: var(--shadow);
  font-size: .82rem; overflow-wrap: anywhere; }
"""

TITLE_CARD = """
<div class="risk-title-card" hidden aria-hidden="true"></div>
<script>
(() => {
  const card = document.querySelector('.risk-title-card');
  let hovered, focused, current, dismissed, timer;
  const hide = () => { card.hidden = true; current = null; };
  function update() {
    clearTimeout(timer);
    const link = hovered || focused;
    if (!link || link === dismissed) {
      if (!link) timer = setTimeout(hide, 180);
      else hide();
      return;
    }
    if (link === current && !card.hidden) return;
    current = link;
    card.textContent = link.dataset.riskTitle;
    card.hidden = false;
    const {left, top, bottom} = link.getBoundingClientRect();
    const {clientWidth, clientHeight} = document.documentElement;
    const width = card.offsetWidth, height = card.offsetHeight;
    card.style.left = `${Math.max(8, Math.min(left, clientWidth - width - 8))}px`;
    const below = bottom + 6;
    card.style.top = `${below + height <= clientHeight - 8 ? below : Math.max(8, top - height - 6)}px`;
  }
  for (const link of document.querySelectorAll('.matrix [data-risk-title]')) {
    link.addEventListener('pointerenter', event => {
      if (event.pointerType === 'touch') return;
      hovered = link; dismissed = null; update();
    });
    link.addEventListener('pointerleave', () => {
      hovered = null;
      clearTimeout(timer);
      timer = setTimeout(() => hovered || focused ? update() : hide(), 180);
    });
    link.addEventListener('focus', () => { focused = link; dismissed = null; update(); });
    link.addEventListener('blur', () => { focused = null; update(); });
    link.addEventListener('click', hide);
  }
  card.addEventListener('pointerenter', () => clearTimeout(timer));
  card.addEventListener('pointerleave', update);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && current) { dismissed = current; clearTimeout(timer); hide(); }
  });
  document.addEventListener('scroll', event => {
    if (event.target !== card) { clearTimeout(timer); hide(); }
  }, true);
  window.addEventListener('resize', hide);
})();
</script>
"""


def render(data, project):
    risks = records(data, "risks", required=True)
    buckets = defaultdict(list)
    details = []
    unassessed = []
    for index, (ident, risk) in enumerate(risks.items(), 1):
        likelihood, severity, level = risk_rating(risk)
        if level is None:
            unassessed.append(f'<a href="#risk-{index}">{h(ident)}</a>')
        else:
            title = risk["title"]
            buckets[likelihood, severity].append(
                f'<a href="#risk-{index}" aria-label="{h(f"{ident}: {title}")}" '
                f'data-risk-title="{h(title)}">{h(ident)}</a>')
        details.append((f'<span id="risk-{index}">{h(ident)}</span>', h(risk["title"]),
                        h(likelihood or "Not supplied"), h(severity or "Not supplied"), badge(level),
                        show(risk, "owner"), show(risk, "mitigation"), show(risk, "details"),
                        id_list(ids(risk, "task_ids", ident)) if risk.get("task_ids") is not None else "Not supplied"))
    headings = "".join(f'<th scope="col">{label}</th>' for label in SEVERITIES)
    rows = []
    for y, likelihood in enumerate(LIKELIHOODS):
        cells = []
        for x, severity in enumerate(SEVERITIES):
            level = POLICY[y][x]
            links = ", ".join(buckets[likelihood, severity])
            cells.append(f'<td class="level-{level}">{badge(level)}'
                         + (f"<div>{links}</div>" if links else "") + "</td>")
        rows.append(f'<tr><th scope="row">{likelihood}</th>{"".join(cells)}</tr>')
    matrix = scroll("Likelihood and severity risk matrix",
                    '<table class="matrix"><caption>Likelihood by severity · qualitative rating policy</caption>'
                    f'<thead><tr><th scope="col">Likelihood / Severity</th>{headings}</tr></thead>'
                    f'<tbody>{"".join(rows)}</tbody></table>')
    register = table("Risk details (including unassessed risks)",
                     ("ID", "Risk", "Likelihood", "Severity", "Rating", "Owner", "Mitigation", "Details", "Task IDs"),
                     details) if details else "<p>No risk records supplied.</p>"
    body = ('<section><h2>Risk assessment matrix</h2>'
            f'<p>{len(risks) - len(unassessed)} plotted · {len(unassessed)} unassessed. '
            'Ratings use the qualitative policy shown below, not numeric multiplication. '
            'Hover over or focus a plotted risk ID to read its title. Select an ID to see its details.</p>'
            f'<p class="legend">{"".join(badge(i) for i in range(len(LEVELS)))}</p>{matrix}'
            f'<p><strong>Not plotted (unassessed):</strong> {", ".join(unassessed) or "None"}.</p></section>'
            f'<section><h2>Risk details</h2>{register}</section>' + TITLE_CARD)
    return page(project, "Risk matrix", body, CSS)


if __name__ == "__main__":
    run("Render the offline 5×5 qualitative risk matrix.", render)
