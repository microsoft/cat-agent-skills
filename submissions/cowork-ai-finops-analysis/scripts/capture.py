"""AI FinOps console snapshot capture (run with core-RunScript, one `part` per run).

Args (JSON): part, today (YYYY-MM-DD), admin_server, act_as, pp_connection_id, out_dir (default working/finops-snap)
Parts, in order: admin_base, admin_periods, admin_trends, viva_7, viva_30, viva_qtd, viva_90, viva_fixed, pp_base, pp_envs, retry
"""
import json, re, time
from pathlib import Path
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, unquote, urlparse
from aether_tools import args, set_result, tools

A = args() or {}
PART = A["part"]
TODAY = date.fromisoformat(A.get("today") or date.today().isoformat())
OUT = Path(A.get("out_dir", "working/finops-snap")); OUT.mkdir(parents=True, exist_ok=True)
ADMIN = A.get("admin_server")
ACT = A.get("act_as")
PPC = dict(connector_id="shared_powerplatformadminv2", connection_id=A.get("pp_connection_id"))
V = "2022-03-01-preview"

def ymd(d): return d.isoformat()
def qstart(d): return date(d.year, (d.month - 1) // 3 * 3 + 1, 1)
def qend(d):
    m = (d.month - 1) // 3 * 3 + 3
    return (date(d.year + (m // 12), m % 12 + 1, 1) - timedelta(days=1)) if m < 12 else date(d.year, 12, 31)
def months_back(d, n):
    y, m = d.year, d.month - n
    while m <= 0: m += 12; y -= 1
    return date(y, m, 1)
PERIODS = {"7": (TODAY - timedelta(days=7), TODAY), "30": (TODAY - timedelta(days=30), TODAY), "qtd": (qstart(TODAY), TODAY), "90": (TODAY - timedelta(days=90), TODAY)}
PERIODS = {k: (ymd(a), ymd(b)) for k, (a, b) in PERIODS.items()}

def key(tool, a): return tool + "|" + json.dumps(a, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def payload_of(r):
    p = getattr(r, "payload", r)
    if isinstance(p, (bytes, bytearray)): p = p.decode()
    return p
def save(name, obj): (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, default=str))
def load(name): return json.loads((OUT / name).read_text())

# ---------------- Microsoft 365 admin center ----------------
def admin_call(tool, a, retries=1):
    err = None
    for attempt in range(retries):
        try:
            r = tools.call(ADMIN, tool, a)
            p = payload_of(r)
            if isinstance(p, str):
                i = min([x for x in (p.find("{"), p.find("[")) if x >= 0] or [0])
                try: p = json.loads(p[i:])
                except Exception: p = {"__error": p[:300]}
            if getattr(r, "is_error", False): p = {"__error": json.dumps(p)[:300]}
            return p
        except Exception as e:
            err = str(e)[:300]
            if attempt + 1 < retries: time.sleep(3 + attempt * 4)
    return {"__error": err}

def run_admin(jobs, fname):
    out = {}
    def go(j):
        t, a = j
        return key(t, a), admin_call(t, a)
    with ThreadPoolExecutor(8) as ex:
        for k, v in ex.map(go, jobs): out[k] = v
    save(fname, out)
    errs = [k.split("|")[0] for k, v in out.items() if isinstance(v, dict) and "__error" in v]
    return {"calls": len(jobs), "errors": len(errs), "error_tools": sorted(set(errs))[:40]}

def admin_base():
    jobs = [(t, {}) for t in ["GetCopilotCreditsSummary","GetCopilotCreditsPaygoOverview","GetCopilotCreditsCallerCapabilities","GetCopilotCreditsPolicyHealthSummary","ListCopilotCreditsAccessPolicies","getAgent365AgentInsights","GetCopilotCreditsOrgFilterOptions","getAgent365PendingRequests",
        "GetWhoCanAccessAgentsSettings","GetWhoCanShareAgentsOrgWideSettings","GetCanInstallMicrosoftAppsAndAgentsSettings","GetCanInstallThirdPartyAppsAndAgentsSettings","GetCanInstallLOBAppsAndAgentsSettings",
        "GetCopilotLicensedActiveUsers","GetCopilotUnlicensedActiveUsers","GetCopilotPromptsSubmitted","GetCopilotChatPromptsSubmitted","GetCopilotReadiness","GetCopilotTopAppsByUsage",
        "GetCopilotAdminSettings","GetOpenCopilotChatSettings","GetCopilotOpenFilesSettings","GetCopilotImageGenerationSettings","GetCopilotAIDisclaimerSettings","GetCopilotScreenSharingSettings","GetCopilotCameraSharingSettings","GetCopilotWebGroundingSettings","Get_PinCopilot_Status","GetOpal",
        "GetTeamsUsageTrend","GetExchangeUsageTrend","GetOfficeAppsUsageTrend","GetOneDriveUsageTrend","GetSharePointUsageTrend","GetBaselineSecurityModeStatus","GetBaselineSecurityModeSettings",
        "GetMtoOrgStatus","GetMtoFederationStatus","GetMtoCalendarSharingStatus","GetMtoExternalTagStatus","GetMtoRoomBookingStatus"]]
    jobs += [("ListCopilotCreditsRequests", {"request": {"includeCount": True, "top": 100}}),
             ("GetSupportTickets", {"state": "All", "lookBackDays": 90, "maxResults": 50}),
             ("GetAiProvider", {"aiProviderName": ""})]
    for s in ["PhishingResistant","BlockLegacyAuth","MFAForAdminUsers","RequireMFAGuestUsers","BlockBasicAuth","BlockInsecureProtocols","DisableEWS","ConsentManagement","BlockUnrestrictedApps","DisableUnusedApps","EnableCAE","EnableMultiAdminApproval","BlockCrossTenantConnection","TeamsConsumerInbound","BlockExcelXLMMacros","BlockActiveX"]:
        jobs.append(("GetBaselineSecurityModeReport", {"settingName": s}))
    for pb in [None,"FirstParty","ThirdParty","LOB","Shared","EntraAgent"]:
        for fl in [None,"noOwner","atRisk","blocked"]:
            a = {"pageSize": 100}
            if pb: a["filterByPublisher"] = pb
            if fl == "noOwner": a["filterByNoOwner"] = True
            if fl == "atRisk": a["filterByAtRisk"] = True
            if fl == "blocked": a["filterByStatus"] = "Blocked"
            jobs.append(("getAgent365Agents", a))
    return run_admin(jobs, "admin_base.json")

def admin_periods():
    jobs = []
    for f, t in PERIODS.values():
        tt = date.fromisoformat(t); ff = max(date.fromisoformat(f), tt - timedelta(days=29))
        jobs += [("GetCopilotCreditsUsers", {"fromDate": f, "toDate": t}), ("GetCopilotCreditsResources", {"fromDate": f, "toDate": t}), ("GetCopilotCreditsGroups", {"fromDate": f, "toDate": t}),
                 ("GetCopilotCreditsTrends", {"fromDate": f, "toDate": t, "interval": "Daily"}), ("GetCopilotCreditsTrends", {"fromDate": f, "toDate": t, "interval": "Monthly"}),
                 ("GetCopilotCreditsServiceTrends", {"request": {"fromDate": ymd(ff), "toDate": t, "pageSize": 100}})]
        for tool in ["GetCopilotCreditsModelConsumption","GetCopilotCreditsEnvironmentConsumption","GetCopilotCreditsPolicyConsumption","GetCopilotCreditsResourceConsumption"]:
            jobs.append((tool, {"request": {"fromDate": f, "toDate": t, "pageSize": 100}}))
    return run_admin(jobs, "admin_periods.json")

def admin_trends():
    f, t = PERIODS["90"]
    per = load("admin_periods.json")
    jobs = []
    for u in (per.get(key("GetCopilotCreditsUsers", {"fromDate": f, "toDate": t}), {}) or {}).get("value", []) or []:
        jobs.append(("GetCopilotCreditsUserTrend", {"userId": u["userId"], "fromDate": f, "toDate": t}))
    for g in (per.get(key("GetCopilotCreditsGroups", {"fromDate": f, "toDate": t}), {}) or {}).get("value", []) or []:
        jobs.append(("GetCopilotCreditsGroupTrend", {"groupId": g["groupId"], "fromDate": f, "toDate": t}))
    return run_admin(jobs[:150], "admin_trends.json")

# ---------------- Viva Insights (A365 Analytics) ----------------
def M(col, alias, fn="Sum", **k): return dict(col=col, alias=alias, fn=fn, **k)
def G(col, alias, **k): return dict(col=col, alias=alias, **k)
COST = "Cost and consumption cost in USD by person, date, service, model, and model provider"
CREDITS = "AI credit units by person, date, and service"
CU = "CostAndConsumptionUnionView"; CV = "CoworkValueByPersonByDate"; AC = "A365AgentConsumptionView"
def M(col, alias, fn="Sum", **k): return dict(col=col, alias=alias, fn=fn, **k)
def G(col, alias, **k): return dict(col=col, alias=alias, **k)
Q = {
 "serviceMonth": dict(target=CU, measures=[M(COST,"cost")], groupBy=[G("ServiceName","service")], timeAgg="Month"),
 "provider": dict(target=CU, measures=[M(COST,"cost")], groupBy=[G("ModelProvider","provider")]),
 "model": dict(target=CU, measures=[M(COST,"cost")], groupBy=[G("ModelName","model")], max=30),
 "creditsService": dict(target=CU, measures=[M(CREDITS,"credits")], groupBy=[G("ServiceName","service")]),
 "usersService": dict(target=CU, measures=[M("PersonId","users","CountDistinct"), M("Session count by person, date, and service","sessions")], groupBy=[G("ServiceName","service")]),
 "org": dict(target=CU, measures=[M(COST,"cost")], groupBy=[G("Organization","organization", ot="PersonHistoricalView")], max=50),
 "daily": dict(target=CU, measures=[M(COST,"cost")], timeAgg="Day"),
 "function": dict(target=CU, measures=[M(COST,"cost")], groupBy=[G("FunctionType","function", ot="PersonHistoricalView")], max=50),
 "creditsModel": dict(target=CU, measures=[M("AI credit units by person, date, service, model, and model provider","credits")], groupBy=[G("ModelName","model")], max=30),
 "dailyService": dict(target=CU, measures=[M(CREDITS,"credits")], groupBy=[G("ServiceName","service")], timeAgg="Day"),
 "forecast": dict(target="AiSpendForecastPersonMonthlyView", dateCol="MonthStart", measures=[M("SteadyCappedCostUSD","steady"), M("GrowthCappedCostUSD","growth")], groupBy=[G("MonthStart","month", type="System.DateTime")], sortDesc=False),
 "kpis": dict(target=CV, measures=[M("Is active in Microsoft 365 Copilot Cowork","activeUsers"),M("Cowork tasks completed","tasks"),M("Cowork user-initiated tasks","userTasks"),M("Cowork scheduled tasks","scheduledTasks"),M("Cowork tasks with output","withOutput"),M("Cowork tasks with plugin usage","withPlugins"),M("Cowork tasks with skill usage","withSkills")]),
 "monthly": dict(target=CV, measures=[M("Cowork tasks completed","tasks"),M("Cowork scheduled tasks","scheduledTasks"),M("Cowork tasks with output","withOutput")], timeAgg="Week"),
 "useCases": dict(target="CoworkUseCaseActivityView", dateCol="ConsumptionDate", measures=[M("SessionId","sessions","CountDistinct"),M("PersonId","users","CountDistinct"),M("SuccessRate","success")], groupBy=[G("DomainName","domain", ot="A365TaskCategoryMetadata"),G("UseCaseName","useCase", ot="A365TaskCategoryMetadata")], max=60),
 "skills": dict(target="CoworkSkillActivityView", dateCol="ConsumptionDate", measures=[M("InvocationCount","calls"),M("SuccessfulInvocationCount","ok"),M("PersonId","users","CountDistinct")], groupBy=[G("SkillName","skill")], max=50),
 "plugins": dict(target="CoworkPluginActivityView", dateCol="ConsumptionDate", measures=[M("InvocationCount","calls"),M("SuccessfulInvocationCount","ok"),M("PersonId","users","CountDistinct")], groupBy=[G("TitleID","plugin")], max=50),
 "useCaseTotal": dict(target="CoworkUseCaseActivityView", dateCol="ConsumptionDate", measures=[M("SessionId","sessions","CountDistinct"),M("PersonId","users","CountDistinct")], groupBy=[G("TaxonomyVersion","taxonomy")]),
 "skillTotal": dict(target="CoworkSkillActivityView", dateCol="ConsumptionDate", measures=[M("InvocationCount","calls"),M("SuccessfulInvocationCount","ok"),M("PersonId","users","CountDistinct")], groupBy=[G("SessionType","sessionType")]),
 "pluginTotal": dict(target="CoworkPluginActivityView", dateCol="ConsumptionDate", measures=[M("InvocationCount","calls"),M("SuccessfulInvocationCount","ok"),M("PersonId","users","CountDistinct")], groupBy=[G("SessionType","sessionType")]),
 "artifacts": dict(target="CoworkArtifactActivityView", dateCol="ConsumptionDate", measures=[M("SessionId","sessions","CountDistinct"),M("PersonId","users","CountDistinct")], groupBy=[G("ContentType","type")]),
 "byModel": dict(target=AC, source="A365Dashboard", dateCol="ConsumptionDate", measures=[M("TotalCostInUSD","cost"),M("TotalCredits","credits"),M("SessionId","sessions","CountDistinct")], groupBy=[G("PrimaryModelName","model")]),
 "agentUsers": dict(target="A365AgentRegistryV1View", source="A365Dashboard", dateCol="ActivityDate", measures=[M("PersonId","users","CountDistinct"),M("RegistryAgentKey","agents","CountDistinct"),M("A365ConversationalSessionCount","sessions")], groupBy=[G("AgentName","agent")], filters=[{"FilterType":"LeafFilter","Property":["IsAnchorRow"],"Operator":"=","Value":0}], extraCols=[dict(col="IsAnchorRow")], max=50),
 "agentCost": dict(target=AC, source="A365Dashboard", dateCol="ConsumptionDate", measures=[M("TotalCostInUSD","cost"),M("TotalCredits","credits"),M("SessionId","sessions","CountDistinct"),M("PersonId","users","CountDistinct")], groupBy=[G("AgentName","agent"),G("ServiceName","service")], max=100),
}
def payload(q, f, t):
    ot = q["target"]; ci = {}
    def add(c, ordinal, nullable=True, deft="System.String"):
        ci[c["col"]] = {"ColumnName": c["col"], "DataType": c.get("type", deft), "Ordinal": ordinal, "OriginalTable": c.get("ot", ot), "IsNullable": nullable}
    dc = q.get("dateCol", "MetricDate")
    add({"col": dc, "type": "System.DateTime"}, 0, False)
    for m in q["measures"]: add(m, 0 if m["fn"] == "CountDistinct" else -1, True, "System.String" if m["fn"] == "CountDistinct" else "System.Double")
    for g in q.get("groupBy", []): add(g, 0)
    for e in q.get("extraCols", []): add(e, -1, False, "System.Double")
    gk = [g["col"] for g in q.get("groupBy", [])]
    ta = q.get("timeAgg", "Aggregated")
    if ta != "Aggregated": gk.insert(0, dc)
    p = {"Aggregates": [{"Column": m["col"], "Function": m["fn"], "SpecialTreatment": "None"} for m in q["measures"]], "ColumnsInfo": ci,
         "Filter": {"FilterType": "CompositeFilter", "BooleanOperator": "AND", "Expressions": [{"FilterType":"LeafFilter","Property":[dc],"Operator":">=","Value":f+"T00:00:00"},{"FilterType":"LeafFilter","Property":[dc],"Operator":"<=","Value":t+"T00:00:00"}] + q.get("filters", [])},
         "GroupByKeys": gk or [dc], "MaxGroupsToReturn": q.get("max", 200), "OnAddColumns": [], "TimeAggregation": ta}
    if dc == "MetricDate": p["DateRangeMode"] = "SelectedDateRange"
    if q.get("sortDesc", True) is not False and q.get("groupBy") and ta == "Aggregated": p["OnSortOrder"] = [{"Order":"Descending","Origin":"Aggregates","OriginIndex":0}]
    return {"QuerySchemaType": "DataModelTable", "TargetMetadata": q["target"], "QueryParameters": p}

def viva_call(body):
    txt = payload_of(tools.call("vivainsightsmcp", "run_query", {"payloadJson": json.dumps(body), "actAs": ACT}))
    if not isinstance(txt, str): txt = json.dumps(txt)
    return json.loads(txt[txt.index("{"):])

def run_viva(name, f, t):
    q = Q[name]
    body = {"Queries": {name: payload(q, f, t)}, "InitialQuery": False, "RequestSource": q.get("source", "UserAIConsumptionActivity"), "CultureDescriptor": "", "DataSource": "ClickHouse"}
    try:
        j = viva_call(body)
        tb = (j.get("Tables") or {}).get(name)
        if not tb:
            e = (j.get("Errors") or {}).get(name)
            return {"error": (json.dumps(e) if e else (j.get("Message") or "No data returned."))[:200]}
        names = [m["alias"] for m in q["measures"]] + (["date"] if q.get("timeAgg", "Aggregated") != "Aggregated" else []) + [g["alias"] for g in q.get("groupBy", [])]
        return [{n: (v if isinstance(v, (int, float, str)) or v is None else str(v)) for n, v in zip(names, r)} for r in tb["Rows"]]
    except Exception as e:
        return {"error": str(e)[:200]}

# Microsoft 365 Copilot usage (CopilotMetrics weekly rows) — mirrors fetchCopilotUsage in the console
CM = "CopilotMetrics"
COPILOT_APPS = ["CopilotAppM365CopilotPromptsCount","CopilotEventsM365Chat","CopilotEventsOutlook","EdgeM365CopilotPromptsCount","CopilotEventsWord","CopilotEventsTeams","CopilotEventsExcel","CopilotEventsPowerpoint","OneNoteM365CopilotPromptsCount"]
def cm_query(aggs, f, t, group=None, gt0=None):
    col = lambda c, ty, o, n=True: {"ColumnName": c, "DataType": ty, "Ordinal": o, "OriginalTable": CM, "IsNullable": n}
    ci = {"PersonId": col("PersonId", "System.String", 0, False), "MetricDate": col("MetricDate", "System.DateTime", 1, False)}
    for c, _ in aggs:
        if c != "PersonId": ci[c] = col(c, "System.Double", -1)
    ex = [{"FilterType": "LeafFilter", "Property": ["MetricDate"], "Operator": ">=", "Value": f + "T00:00:00"},
          {"FilterType": "LeafFilter", "Property": ["MetricDate"], "Operator": "<=", "Value": t + "T00:00:00"}]
    if gt0:
        ci[gt0] = col(gt0, "System.Double", -1)
        ex.append({"FilterType": "LeafFilter", "Property": [f"{CM}.{gt0}"], "Operator": ">", "Value": 0})
    return {"QuerySchemaType": "DataModelTable", "TargetMetadata": CM, "QueryParameters": {
        "Aggregates": [{"Column": c, "Function": fn, "SpecialTreatment": "None"} for c, fn in aggs], "ColumnsInfo": ci,
        "Filter": {"FilterType": "CompositeFilter", "BooleanOperator": "AND", "Expressions": ex},
        "GroupByKeys": group or [], "MaxGroupsToReturn": 1000, "OnAddColumns": []}}
def copilot_usage(f, t):
    qs = {"cpTotals": cm_query([("TotalCopilotActionsTaken","Sum"),("M365PromptsSubmittedEventsCount","Sum"),("CopilotAssistedHours","Sum"),("BusinessChatWebPromptsSubmitted","Sum")], f, t),
          "cpActive": cm_query([("PersonId","CountDistinct")], f, t, gt0="TotalCopilotActionsTaken"),
          "cpEnabled": cm_query([("PersonId","CountDistinct")], f, t, gt0="CopilotEnabledDays"),
          "cpApps": cm_query([(a, "Sum") for a in COPILOT_APPS], f, t),
          "cpWeekly": cm_query([("TotalCopilotActionsTaken","Sum"),("M365PromptsSubmittedEventsCount","Sum")], f, t, group=["MetricDate"])}
    out = {}
    try:
        j = viva_call({"Queries": qs, "InitialQuery": False, "RequestSource": "CopilotDashboard", "CultureDescriptor": "", "DataSource": "ClickHouse"})
        for k in qs:
            tb = (j.get("Tables") or {}).get(k)
            out[k] = [dict(zip([c["ColumnName"] for c in tb["Columns"]], r)) for r in tb["Rows"]] if tb else {"error": "No data returned."}
    except Exception as e:
        for k in qs: out[k] = {"error": str(e)[:200]}
    return out

PERIOD_QUERIES = ["provider","model","creditsService","usersService","org","daily","function","creditsModel","dailyService","kpis","monthly","useCases","skills","plugins","useCaseTotal","skillTotal","pluginTotal","artifacts","byModel","agentUsers"]
def viva_period(pid):
    f, t = PERIODS[pid]
    jobs = [(n, f, t) for n in PERIOD_QUERIES if n in Q]
    res = {}
    with ThreadPoolExecutor(7) as ex:
        for (n, _, _), r in zip(jobs, ex.map(lambda j: run_viva(*j), jobs)): res[n] = r
    res.update(copilot_usage(f, t))
    save(f"viva_{pid}.json", {f"{f}|{t}": res})
    return {"range": f"{f}|{t}", "rows": {k: (len(v) if isinstance(v, list) else "ERR " + str(v.get("error"))[:80]) for k, v in res.items()}}

def viva_fixed():
    f, t = PERIODS["qtd"]
    jobs = [("serviceMonth", ymd(months_back(TODAY, 5)), ymd(TODAY)), ("forecast", ymd(qstart(TODAY)), ymd(qend(TODAY))), ("agentCost", f, t)]
    res = {}
    with ThreadPoolExecutor(3) as ex:
        for (n, a, b), r in zip(jobs, ex.map(lambda j: run_viva(*j), jobs)): res.setdefault(f"{a}|{b}", {})[n] = r
    save("viva_fixed.json", res)
    fixed = {k: {n: (len(v) if isinstance(v, list) else "ERR") for n, v in d.items()} for k, d in res.items()}
    try:
        response = tools.call("vivainsightsmcp", "list_datasets", {"actAs": ACT})
        if getattr(response, "is_error", False):
            raise RuntimeError(str(payload_of(response)))
        ds = payload_of(response)
        ds = json.loads(ds[ds.index("["):]) if isinstance(ds, str) else ds
        if not isinstance(ds, list) or not all(isinstance(d, dict) and isinstance(d.get("DatasetName"), str) for d in ds):
            raise ValueError("Invalid dataset catalog response")
    except Exception as e:
        return {"catalog_error": str(e)[:200], "fixed": fixed}
    def attrs(d):
        try:
            a = payload_of(tools.call("vivainsightsmcp", "list_attributes", {"datasetName": d["DatasetName"], "actAs": ACT}))
            return d["DatasetName"], (json.loads(a[a.index("[{"):]) if "[{" in a else []) if isinstance(a, str) else a
        except Exception as e:
            return d["DatasetName"], {"error": str(e)[:200]}
    with ThreadPoolExecutor(7) as ex:
        at = dict(ex.map(attrs, ds))
    res["__datasets"] = ds; res["__attrs"] = at
    save("viva_fixed.json", res)
    return {"datasets": len(ds), "fixed": fixed}

# ---------------- Power Platform admin ----------------
def pp_op(o, params, retries=1):
    err = None
    for attempt in range(retries):
        try:
            r = payload_of(tools.call("powerplatform", "InvokeConnectorOperation", dict(PPC, operation_id=o, params=params)))
            if isinstance(r, str): r = json.loads(r)
            status = r.get("status", 200)
            if status >= 400:
                err = f"status {status}"
                if status not in (408, 425, 429, 500, 502, 503, 504) or attempt + 1 >= retries:
                    return {"__error": err}
                time.sleep(min(2, 0.5 * (2 ** attempt)))
                continue
            body = r.get("response")
            if r.get("truncated"):
                m = re.search(r"(grounding/responses/[^\s\"']+)", json.dumps(r))
                if m and Path(m.group(1)).exists(): body = Path(m.group(1)).read_text()
                else: return {"__error": "truncated"}
            if isinstance(body, str) and not body.strip(): return {"value": []}
            return json.loads(body) if isinstance(body, str) else body
        except Exception as e:
            err = str(e)[:200]
            if attempt + 1 < retries: time.sleep(4 + attempt * 5)
    return {"__error": err}

def pp_collection(o, params, retries=3, max_pages=100):
    rows = []
    current = dict(params)
    seen = set()
    for _ in range(max_pages):
        response = pp_op(o, current, retries)
        if isinstance(response, dict) and "__error" in response:
            return {"value": rows, "__error": response["__error"],
                    "__incomplete": "A page failed before the inventory was complete."}
        if not isinstance(response, dict) or not isinstance(response.get("value"), list):
            return {"value": rows, "__error": "Invalid collection response",
                    "__incomplete": "A page returned an invalid collection response."}
        rows.extend(response["value"])
        next_link = response.get("nextLink") or response.get("@odata.nextLink")
        if not next_link:
            return {"value": rows}
        query = parse_qs(urlparse(next_link).query)
        token_key = next((key for key in ("$skipToken", "$skiptoken", "skipToken", "skiptoken", "$skip")
                          if key in query and query[key]), None)
        if token_key:
            token = query[token_key][0]
        else:
            token = response.get("continuationToken") or response.get("nextPageToken")
            token_key = "$skipToken" if token else None
        if not token or token in seen:
            return {"value": rows, "__incomplete": "Pagination returned an unusable or repeated continuation token."}
        seen.add(token)
        current[token_key] = token
    return {"value": rows, "__incomplete": f"Inventory exceeded the {max_pages}-page capture limit."}

def slim_apps(d):
    if isinstance(d, dict) and "value" in d:
        out = {"value": [{"name": a.get("name"), "type": a.get("type"), "properties": {k: (a.get("properties") or {}).get(k) for k in ["displayName","owner","appType","createdTime","lastModifiedTime","sharedUsersCount","sharedGroupsCount"]}} for a in d["value"]]}
        out.update({k: d[k] for k in ("__error", "__incomplete") if k in d})
        return out
    return d
def slim_flows(d):
    if isinstance(d, dict) and "value" in d:
        out = {"value": [{k: f.get(k) for k in ["displayName","name","stateCode","state","statecode","createdOn","modifiedOn","ownerId","createdBy"]} for f in d["value"]]}
        out.update({k: d[k] for k in ("__error", "__incomplete") if k in d})
        return out
    return d

def pp_base():
    base = {"envs": ("ListEnvironmentsForUser", {"api-version": V}), "capacity": ("GetTenantCapacityDetails", {"api-version": V}), "currency": ("ListCurrencyReports", {"api-version": V, "includeAllocations": True, "includeConsumptions": True}),
            "billing": ("ListBillingPolicies", {"api-version": V}), "storage": ("ListStorageWarnings", {"api-version": V}), "finops": ("GetFinOpsLicenseSummaryV2", {"api-version": V}),
            "envGroups": ("ListEnvironmentGroups", {"api-version": V}), "ruleSets": ("GetRuleSetListForTenant", {"api-version": V}), "ruleAssign": ("ListRuleAssignments", {"api-version": V, "includeRuleSetCounts": True}),
            "rbp": ("ListRuleBasedPolicies", {"api-version": V}), "roleDefs": ("ListRoleDefinitions", {"api-version": V}), "roleAssign": ("ListRoleAssignments", {"api-version": V}),
            "xtenant": ("ListCrossTenantConnectionReports", {"api-version": V}), "packages": ("GetTenantApplicationPackage", {"api-version": V}), "recs": ("GetRecommendations", {"api-version": V})}
    out = {}
    with ThreadPoolExecutor(5) as ex:
        for k, r in zip(base, ex.map(lambda kv: pp_op(kv[0], kv[1], 3), base.values())): out[k] = r
    if isinstance(out.get("rbp"), dict) and "__error" not in out["rbp"]:
        out["rbp"] = {"value": [{"name": p.get("name"), "ruleSets": [{"id": r.get("id")} for r in p.get("ruleSets", [])], "ruleSetCount": p.get("ruleSetCount"), "lastModified": p.get("lastModified")} for p in out["rbp"].get("value", [])]}
    if isinstance(out.get("packages"), dict) and "__error" not in out["packages"]:
        out["packages"] = {"value": [{"localizedName": p.get("localizedName"), "uniqueName": p.get("uniqueName"), "publisherName": p.get("publisherName"), "applicationVisibility": p.get("applicationVisibility")} for p in out["packages"].get("value", [])]}
    res = {}
    for rec in (out.get("recs") or {}).get("value", []) if isinstance(out.get("recs"), dict) else []:
        sc = rec.get("scenario"); pages = {}; tok = None
        for _ in range(10):
            p = {"scenario": sc, "api-version": V}
            if tok: p["$skipToken"] = tok
            d = pp_op("GetRecommendationResources", p, 3)
            pages[tok or ""] = d
            nl = d.get("nextLink") if isinstance(d, dict) else None
            m = re.search(r"[?&]\$?skipToken=([^&]+)", nl or "", re.I)
            if not m: break
            tok = unquote(m.group(1))
        res[sc] = pages
    out["recResources"] = res
    save("pp_base.json", out)
    return {k: ("ERR " + v["__error"] if isinstance(v, dict) and "__error" in v else "ok") for k, v in out.items() if k != "recResources"}

def pp_envs():
    envs = [e["id"] for e in (load("pp_base.json").get("envs") or {}).get("value", [])]
    off = int(A.get("env_offset", 0)); limit = int(A.get("env_limit", 50))
    def detail(eid):
        return eid, {"apps": slim_apps(pp_collection("Get-AdminApps", {"environmentId": eid, "api-version": V, "$top": 250})),
                     "flows": slim_flows(pp_collection("ListCloudFlows", {"environmentId": eid, "api-version": V})),
                     "billing": pp_op("GetEnvironmentBillingPolicy", {"environmentId": eid, "api-version": V}, 2),
                     "backups": pp_op("GetEnvironmentBackups", {"environmentId": eid, "api-version": V}, 2)}
    batch = envs[off:off + limit]
    out = load("pp_envs.json") if off and (OUT / "pp_envs.json").exists() else {}
    with ThreadPoolExecutor(4) as ex:
        out.update(dict(ex.map(detail, batch)))
    save("pp_envs.json", out)
    bad = sum(1 for d in out.values() for v in d.values() if isinstance(v, dict) and "__error" in v)
    incomplete_apps = sum(1 for d in out.values() if isinstance(d.get("apps"), dict) and d["apps"].get("__incomplete"))
    incomplete_flows = sum(1 for d in out.values() if isinstance(d.get("flows"), dict) and d["flows"].get("__incomplete"))
    nxt = off + limit if off + limit < len(envs) else None
    return {"environments_total": len(envs), "captured": len(out), "failed_reads": bad,
            "incomplete_app_inventories": incomplete_apps, "incomplete_flow_inventories": incomplete_flows,
            "incomplete_inventories": incomplete_apps + incomplete_flows, "next_env_offset": nxt}

def retry():
    fixed = left = attempted = 0
    limit = max(0, int(A.get("limit", 80)))
    deadline = time.monotonic() + 240
    admin_jobs = []
    admin_data = {}
    for fname in ["admin_base.json", "admin_periods.json", "admin_trends.json"]:
        if not (OUT / fname).exists(): continue
        data = load(fname)
        admin_data[fname] = data
        bad = [k for k, v in data.items() if isinstance(v, dict) and "__error" in v and not re.search(r"404|NotFound|403|Forbidden", v["__error"])]
        admin_jobs.extend((fname, k) for k in bad)
    pp_jobs = []
    pp_data = None
    ops = {"apps": ("Get-AdminApps", {"api-version": V, "$top": 250}), "flows": ("ListCloudFlows", {"api-version": V}), "billing": ("GetEnvironmentBillingPolicy", {"api-version": V}), "backups": ("GetEnvironmentBackups", {"api-version": V})}
    if (OUT / "pp_envs.json").exists():
        pp_data = load("pp_envs.json")
        pp_jobs = [(e, p) for e, d in pp_data.items() for p, v in d.items() if isinstance(v, dict) and "__error" in v and ("status 4" not in v["__error"] or v["__error"] == "status 429")]
    jobs = []
    for i in range(max(len(admin_jobs), len(pp_jobs))):
        if i < len(admin_jobs): jobs.append(("admin", admin_jobs[i]))
        if i < len(pp_jobs): jobs.append(("pp", pp_jobs[i]))
    for source, job in jobs:
        if attempted >= limit or time.monotonic() >= deadline: break
        attempted += 1
        if source == "admin":
            fname, k = job
            t, a = k.split("|", 1)
            r = admin_call(t, json.loads(a))
            admin_data[fname][k] = r
            data = admin_data[fname]
        else:
            e, p = job
            o, prm = ops[p]
            r = pp_collection(o, dict(prm, environmentId=e)) if p in ("apps", "flows") else pp_op(o, dict(prm, environmentId=e), 3)
            r = slim_apps(r) if p == "apps" else slim_flows(r) if p == "flows" else r
            pp_data[e][p] = r
            fname, data = "pp_envs.json", pp_data
        tmp = OUT / (fname + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, default=str))
        tmp.replace(OUT / fname)
        if isinstance(r, dict) and "__error" in r: left += 1
        else: fixed += 1
    return {"attempted": attempted, "fixed": fixed, "still_failing": left, "remaining": len(jobs) - attempted}

DISPATCH = {"admin_base": admin_base, "admin_periods": admin_periods, "admin_trends": admin_trends,
            "viva_7": lambda: viva_period("7"), "viva_30": lambda: viva_period("30"), "viva_qtd": lambda: viva_period("qtd"), "viva_90": lambda: viva_period("90"),
            "viva_fixed": viva_fixed, "pp_base": pp_base, "pp_envs": pp_envs, "retry": retry}
set_result({"part": PART, "today": ymd(TODAY), "result": DISPATCH[PART]()})
