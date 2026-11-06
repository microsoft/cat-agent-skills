#!/usr/bin/env python3
"""Intake structure check, not deviation math or a complete JSON Schema engine."""
import argparse,csv,json,sys,math
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--spec",required=True);ap.add_argument("--measurements",required=True);ap.add_argument("--coc");a=ap.parse_args()
    try:
        p=json.loads(Path(a.spec).read_text());rows=list(csv.DictReader(Path(a.measurements).open(newline="",encoding="utf-8-sig")))
        for k in ("part_number","part_revision","lot_id"):
            if not isinstance(p.get(k),str) or not p[k].strip():raise ValueError("missing documented identity "+k)
        if type(p.get("lot_quantity")) is not int or p["lot_quantity"]<1:raise ValueError("invalid lot quantity")
        chars=p.get("characteristics")
        if not isinstance(chars,list) or not chars:raise ValueError("no characteristics")
        names=[c.get("name") for c in chars]
        if len(set(names))!=len(names) or any(not n for n in names):raise ValueError("duplicate/empty characteristic")
        for c in chars:
            if not c.get("unit") or not c.get("citation"):raise ValueError("missing units/citation")
            for k in ("lsl","usl","nominal"):
                v=c.get(k)
                if v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)):raise ValueError("invalid finite bound")
            if c.get("criticality") not in (None,"minor","major","critical"):raise ValueError("invalid criticality")
            if c.get("rework_permitted") is not None and type(c["rework_permitted"]) is not bool:raise ValueError("invalid rework permission")
            if c.get("tolerance_kind","two_sided") not in ("two_sided","upper_limit_only","lower_limit_only"):raise ValueError("invalid tolerance kind")
        pairs=set()
        for r in rows:
            key=(r.get("part_serial"),r.get("characteristic"))
            if not key[0] or key[1] not in names or key in pairs:raise ValueError("duplicate/unknown/missing row ID")
            pairs.add(key)
            if not math.isfinite(float(r["value"])):raise ValueError("nonfinite reading")
            if not r.get("citation"):raise ValueError("source-row citation required on normalized raw intake")
        if a.coc:
            coc=json.loads(Path(a.coc).read_text())
            for cl in coc.get("claims",[]):
                if not isinstance(cl.get("characteristics"),list) or not cl.get("claim") or not cl.get("citation"):raise ValueError("invalid certificate claim")
        json.loads(json.dumps(p,allow_nan=False))
    except (ValueError,KeyError,TypeError,OSError) as e:print("BLOCKED: "+str(e),file=sys.stderr);return 2
    print("Intake shape checked; not full JSON Schema validation. Identity verification and QE approval remain external prerequisites.");return 0
if __name__=="__main__":sys.exit(main())
