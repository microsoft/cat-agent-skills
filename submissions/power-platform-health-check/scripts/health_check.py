#!/usr/bin/env python3
"""Read-only health check of Dataverse solution components."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "/api/data/v9.2/"


class Client:
    def __init__(self, env_url):
        self.base = env_url.rstrip("/")
        self.token = self._token()

    def _token(self):
        tok = os.environ.get("DATAVERSE_ACCESS_TOKEN")
        if tok:
            return tok
        app = os.environ.get("POWERPLATFORM_SP_APP_ID")
        tenant = os.environ.get("POWERPLATFORM_SP_TENANT_ID")
        secret = os.environ.get("POWERPLATFORM_SP_CLIENT_SECRET")
        if not (app and tenant and secret):
            raise SystemExit("Missing POWERPLATFORM_SP_* variables (or DATAVERSE_ACCESS_TOKEN).")
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials", "client_id": app,
            "client_secret": secret, "scope": self.base + "/.default",
        }).encode()
        url = "https://login.microsoftonline.com/%s/oauth2/v2.0/token" % tenant
        with urllib.request.urlopen(urllib.request.Request(url, data=data)) as r:
            return json.load(r)["access_token"]

    def get(self, path):
        url = path if path.startswith("http") else self.base + API + path
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + self.token, "Accept": "application/json",
            "OData-MaxVersion": "4.0", "OData-Version": "4.0",
        })
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    def get_all(self, path):
        out, url = [], path
        while url:
            page = self.get(url)
            out.extend(page.get("value", []))
            url = page.get("@odata.nextLink")
        return out

    def try_get(self, path):
        try:
            return self.get(path), None
        except urllib.error.HTTPError as e:
            return None, "not found" if e.code == 404 else "HTTP %s" % e.code
        except Exception as e:
            return None, str(e)


results = []


def add(sol, ctype, name, cid, level, detail=""):
    results.append({"solution": sol, "type": ctype, "name": name, "id": cid,
                    "level": level, "detail": detail})


def v_workflow(r):
    is_flow = r.get("category") in (5, 6)
    if (is_flow or r.get("type") == 1) and r.get("statecode") != 1:
        return "FAIL", "Not activated (statecode=%s)" % r.get("statecode")
    if is_flow and not r.get("clientdata"):
        return "FAIL", "clientdata is empty"
    return "PASS", "category=%s" % r.get("category")


def v_webres(r):
    return ("PASS", "") if r.get("content") else ("FAIL", "Content is empty")


def v_step(r):
    if r.get("statecode") != 0:
        return "WARN", "Step is disabled"
    return "PASS", "stage=%s mode=%s" % (r.get("stage"), r.get("mode"))


def v_form(r):
    if not r.get("formxml"):
        return "FAIL", "formxml is empty"
    return ("PASS", "") if r.get("formactivationstate") in (None, 1) else ("WARN", "Form inactive")


def v_view(r):
    if not r.get("fetchxml") or not r.get("layoutxml"):
        return "FAIL", "fetchxml or layoutxml empty"
    return "PASS", ""


def v_app(r):
    return ("PASS", "") if r.get("publishedon") else ("WARN", "Never published")


def v_envdef(r):
    vals = r.get("environmentvariabledefinition_environmentvariablevalue") or []
    if r.get("defaultvalue") or vals:
        return "PASS", "type=%s" % r.get("type")
    return "WARN", "No default or current value"


def v_connref(r):
    return ("PASS", "") if r.get("connectionid") else ("WARN", "No connection bound")


def v_assembly(r):
    return "PASS", "isolation=%s sourcetype=%s" % (r.get("isolationmode"), r.get("sourcetype"))


# type code -> (label, table, select, name field, validator, expand)
SIMPLE = {
    29: ("Workflow/Flow", "workflows", "name,category,type,statecode,clientdata", "name", v_workflow, ""),
    61: ("Web resource", "webresourceset", "name,content", "name", v_webres, ""),
    91: ("Plug-in assembly", "pluginassemblies", "name,isolationmode,sourcetype", "name", v_assembly, ""),
    92: ("Plug-in step", "sdkmessageprocessingsteps", "name,statecode,stage,mode", "name", v_step, ""),
    60: ("Form", "systemforms", "name,formxml,formactivationstate", "name", v_form, ""),
    26: ("View", "savedqueries", "name,fetchxml,layoutxml", "name", v_view, ""),
    80: ("Model-driven app", "appmodules", "name,publishedon", "name", v_app, ""),
    300: ("Canvas app", "canvasapps", "displayname", "displayname", None, ""),
    380: ("Environment variable definition", "environmentvariabledefinitions",
          "displayname,defaultvalue,type", "displayname", v_envdef,
          "&$expand=environmentvariabledefinition_environmentvariablevalue($select=value)"),
    381: ("Environment variable value", "environmentvariablevalues", "schemaname", "schemaname", None, ""),
}

METADATA = {
    1: ("Table", "EntityDefinitions", "LogicalName"),
    2: ("Column", "AttributeDefinitions", "LogicalName"),
    9: ("Option set", "GlobalOptionSetDefinitions", "Name"),
    10: ("Relationship", "RelationshipDefinitions", "SchemaName"),
}

_type_cache = {}


def resolve_type(c, code):
    if code not in _type_cache:
        data, _ = c.try_get("EntityDefinitions?$select=LogicalName,PrimaryNameAttribute,EntitySetName"
                            "&$filter=ObjectTypeCode eq %d" % code)
        rows = (data or {}).get("value", [])
        _type_cache[code] = rows[0] if rows else None
    return _type_cache[code]


def check_component(c, sol, comp):
    code, cid = comp["componenttype"], comp["objectid"]
    if code in METADATA:
        label, coll, field = METADATA[code]
        rec, err = c.try_get("%s(%s)?$select=%s" % (coll, cid, field))
        add(sol, label, (rec or {}).get(field, cid), cid, "PASS" if rec else "FAIL", "" if rec else err)
        return
    if code in SIMPLE:
        label, table, select, nf, validator, expand = SIMPLE[code]
    else:
        info = resolve_type(c, code)
        if not info:
            add(sol, "Type %d" % code, cid, cid, "PASS", "Inventoried, not deep-checked")
            return
        label, table, nf = info["LogicalName"], info["EntitySetName"], info.get("PrimaryNameAttribute")
        select = ",".join(x for x in [nf, "connectionid" if label == "connectionreference" else None] if x)
        validator = v_connref if label == "connectionreference" else None
        expand = ""
    q = "%s(%s)" % (table, cid)
    if select:
        q += "?$select=" + select + expand
    rec, err = c.try_get(q)
    if rec is None:
        add(sol, label, cid, cid, "FAIL", "Record lookup failed: %s" % err)
        return
    lvl, det = validator(rec) if validator else ("PASS", "" if code in SIMPLE else "Inventoried, not deep-checked")
    add(sol, label, rec.get(nf) or cid, cid, lvl, det)


def check_dependencies(c, sol_id, name):
    safe_name = name.replace("'", "''")
    data, err = c.try_get("RetrieveMissingDependencies(SolutionUniqueName='%s')" % safe_name)
    if data is None:
        add(name, "Dependencies", name, sol_id, "WARN", "Could not evaluate: %s" % err)
        return
    missing = data.get("value", [])
    if not missing:
        add(name, "Dependencies", name, sol_id, "PASS", "No missing dependencies")
    for d in missing:
        rid = d.get("requiredcomponentobjectid")
        add(name, "Missing dependency", rid, rid, "FAIL",
            "Required type %s needed by type %s %s" % (
                d.get("requiredcomponenttype"), d.get("dependentcomponenttype"),
                d.get("dependentcomponentobjectid")))


def render(args, summaries):
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for r in results:
        counts[r["level"]] += 1
    lines = ["# Power Platform Health Check", "", "- Environment: %s" % args.env_url]
    for s in summaries:
        lines.append("- Solution `%s` v%s (%s), %d components" % (
            s["name"], s["version"], "managed" if s["managed"] else "unmanaged", s["count"]))
    lines += ["", "**Totals:** %d PASS, %d WARN, %d FAIL" % (counts["PASS"], counts["WARN"], counts["FAIL"]),
              "", "## Findings", ""]
    findings = [r for r in results if r["level"] != "PASS"]
    if not findings:
        lines.append("None.")
    else:
        lines += ["| Level | Solution | Type | Component | ID | Detail |", "|---|---|---|---|---|---|"]
        lines += ["| %(level)s | %(solution)s | %(type)s | %(name)s | %(id)s | %(detail)s |" % r for r in findings]
    lines += ["", "## All components", "", "| Level | Solution | Type | Component | Detail |", "|---|---|---|---|---|"]
    lines += ["| %(level)s | %(solution)s | %(type)s | %(name)s | %(detail)s |" % r for r in results]
    return "\n".join(lines) + "\n", counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--env-url", default=os.environ.get("POWERPLATFORM_ENV_URL"))
    ap.add_argument("--solutions", help="Comma-separated solution unique names")
    ap.add_argument("--list-solutions", action="store_true")
    ap.add_argument("--skip-dependencies", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args()
    if not args.env_url:
        print("Environment URL required.", file=sys.stderr)
        return 2
    summaries = []
    try:
        c = Client(args.env_url)
        if args.list_solutions:
            for s in c.get_all("solutions?$select=uniquename,friendlyname,version&$filter=isvisible eq true"):
                print("%s\t%s\t%s" % (s["uniquename"], s["friendlyname"], s["version"]))
            return 0
        if not args.solutions:
            print("--solutions required.", file=sys.stderr)
            return 2
        for name in [s.strip() for s in args.solutions.split(",") if s.strip()]:
            found = c.get_all("solutions?$select=solutionid,uniquename,version,ismanaged"
                              "&$filter=uniquename eq '%s'" % name)
            if not found:
                add(name, "Solution", name, "", "FAIL", "Solution not found")
                continue
            sol = found[0]
            comps = c.get_all("solutioncomponents?$select=componenttype,objectid"
                              "&$filter=_solutionid_value eq %s" % sol["solutionid"])
            summaries.append({"name": name, "version": sol["version"],
                              "managed": sol["ismanaged"], "count": len(comps)})
            add(name, "Solution", name, sol["solutionid"], "PASS", "%d components" % len(comps))
            for comp in comps:
                check_component(c, name, comp)
            if not args.skip_dependencies:
                check_dependencies(c, sol["solutionid"], name)
    except (urllib.error.URLError, KeyError) as e:
        print("Connection or authentication error: %s" % e, file=sys.stderr)
        return 2

    text, counts = render(args, summaries)
    out = json.dumps({"summaries": summaries, "counts": counts, "results": results}, indent=2) if args.json else text
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    print(out)
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
