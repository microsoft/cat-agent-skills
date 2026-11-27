"""Assemble captured data and inject it into the console template -> one self-contained HTML file.

python build.py --snap working/finops-snap --template <skill>/assets/console-template.html \
                --out working/ai-finops-admin-console-<tenant>.html --today 2026-11-26 --tenant "Contoso"
"""
import argparse, json, os
from datetime import date

ap = argparse.ArgumentParser()
ap.add_argument("--snap", default="working/finops-snap")
ap.add_argument("--template", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--today", default=date.today().isoformat())
ap.add_argument("--tenant", default="")
a = ap.parse_args()

def trim(o, n=240):
    if isinstance(o, str): return o if len(o) <= n else o[:n] + "…"
    if isinstance(o, list): return [trim(x, n) for x in o]
    if isinstance(o, dict): return {k: trim(v, n) for k, v in o.items()}
    return o
def load(name, default=None):
    p = os.path.join(a.snap, name)
    if not os.path.exists(p):
        print(f"missing: {name}"); return default if default is not None else {}
    return json.load(open(p))

admin = {}
for f in ["admin_base.json", "admin_periods.json", "admin_trends.json"]: admin.update(load(f))
viva = {}
for f in ["viva_7.json", "viva_30.json", "viva_qtd.json", "viva_90.json", "viva_fixed.json"]:
    for k, v in load(f).items():
        if k.startswith("__"): continue
        viva.setdefault(k, {}).update(v)
fx = load("viva_fixed.json")
attrs = {k: [{"AttributeName": x.get("AttributeName"), "Description": (x.get("Description") or "")[:400]} for x in v] if isinstance(v, list) else v for k, v in (fx.get("__attrs") or {}).items()}
pp = load("pp_base.json"); pp["envDetail"] = load("pp_envs.json")
snap = {"capturedAt": a.today, "tenantName": a.tenant, "admin": trim(admin), "viva": viva, "datasets": fx.get("__datasets", []), "attrs": attrs, "pp": trim(pp, 400)}
data = json.dumps(snap, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\u0021--")
html = open(a.template, encoding="utf-8").read()
d = date.fromisoformat(a.today)
title = f"AI FinOps Admin Console – {a.tenant + ' – ' if a.tenant else ''}snapshot {d.day} {d.strftime('%b %Y')}"
title = title.replace("&", "&amp;").replace("<", "&lt;")
assert html.count("__FINOPS_DATA__") == 1
html = html.replace("__FINOPS_TITLE__", title, 1).replace("__FINOPS_DATA__", data, 1)
warning = (
    '<div role="note" style="padding:12px;background:#fff3cd;color:#3d3000;'
    'font:14px sans-serif">Data completeness warning: unavailable or failed '
    'reports may appear as zero or empty, including AI spend and forecasts. '
    'Verify source availability and values before relying on this snapshot.</div>'
)
incomplete_apps = sum(1 for env in pp["envDetail"].values()
                      if isinstance(env, dict) and isinstance(env.get("apps"), dict)
                      and env["apps"].get("__incomplete"))
incomplete_flows = sum(1 for env in pp["envDetail"].values()
                       if isinstance(env, dict) and isinstance(env.get("flows"), dict)
                       and env["flows"].get("__incomplete"))
if incomplete_apps or incomplete_flows:
    inventory_summary = ", ".join(
        f"{count} {name} environment(s)" for name, count in
        (("app", incomplete_apps), ("cloud-flow", incomplete_flows)) if count
    )
    warning += (
        f'<div role="note" style="padding:12px;background:#fff3cd;color:#3d3000;'
        f'font:14px sans-serif">Power Platform inventory is incomplete in {inventory_summary}. '
        f'Additional pages or reads were not captured; do not treat these inventory counts as complete.</div>'
    )
if html.count("<body>") != 1:
    raise ValueError("Console template must contain exactly one <body> tag")
html = html.replace("<body>", "<body>" + warning, 1)
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
open(a.out, "w", encoding="utf-8").write(html)
errs = sum(1 for v in admin.values() if isinstance(v, dict) and "__error" in v)
print(json.dumps({"out": a.out, "bytes": len(html.encode()), "admin_reads": len(admin), "admin_errors": errs, "viva_ranges": list(viva), "pp_envs": len(pp["envDetail"]), "incomplete_app_inventories": incomplete_apps, "incomplete_flow_inventories": incomplete_flows}))
