"""Offline contract validator. Standard library only; no network or operations."""
import json, math, re
from pathlib import Path

def validate(value, schema, path="$", root=None):
    root = schema if root is None else root
    if "$ref" in schema:
        if not schema["$ref"].startswith("#/"): raise ValueError("external schema references unsupported")
        resolved=root
        for k in schema["$ref"][2:].split("/"): resolved=resolved[k]
        return validate(value,resolved,path,root)
    if "const" in schema and value != schema["const"]: raise ValueError(path+": wrong constant")
    if "enum" in schema and value not in schema["enum"]: raise ValueError(path+": invalid enum")
    types=schema.get("type")
    if types:
        types=[types] if isinstance(types,str) else types
        def istype(t):
            return {"object":isinstance(value,dict),"array":isinstance(value,list),"string":isinstance(value,str),
                    "number":type(value) in (int,float) and math.isfinite(value),"integer":type(value)==int,
                    "boolean":type(value)==bool,"null":value is None}.get(t,False)
        if not any(istype(t) for t in types): raise ValueError(path+": invalid or nonfinite type")
    if type(value) in (int,float):
        if not math.isfinite(value): raise ValueError(path+": nonfinite number")
        if "minimum" in schema and value<schema["minimum"]: raise ValueError(path+": below minimum")
        if "maximum" in schema and value>schema["maximum"]: raise ValueError(path+": above maximum")
        if "exclusiveMinimum" in schema and value<=schema["exclusiveMinimum"]: raise ValueError(path+": nonpositive quantity")
    if isinstance(value,str) and "pattern" in schema and re.search(schema["pattern"],value) is None: raise ValueError(path+": pattern mismatch")
    if isinstance(value,dict):
        for k in schema.get("required",[]):
            if k not in value: raise ValueError(path+": missing "+k)
        for k,v in value.items():
            if k in schema.get("properties",{}): validate(v,schema["properties"][k],path+"/"+k,root)
    if isinstance(value,list):
        for i,v in enumerate(value): validate(v,schema.get("items",{}),path+"/"+str(i),root)

def validate_payload(payload, hop=None):
    schema=json.loads((Path(__file__).resolve().parent.parent/"contracts/mfg.work-order-assist.v1.json").read_text())
    validate(payload,schema)
    for k in ("work_order_id","asset_id"):
        if not payload.get(k) or not payload[k].strip(): raise ValueError("missing identity "+k)
    if hop in ("similar_work","parts_readiness"):
        for k in ("component","asset_criticality","sop_ref","required_parts"):
            if not payload.get(k): raise ValueError("missing prerequisite "+k)
        for row in payload["required_parts"]:
            if type(row.get("qty")) not in (int,float) or not math.isfinite(row["qty"]) or row["qty"]<=0: raise ValueError("qty must be positive finite number")
        catalog=payload.get("parts_catalog",[])
        if not isinstance(catalog, list): raise ValueError("parts_catalog must be an array when supplied")
        seen=set()
        for row in catalog:
            if not isinstance(row, dict): raise ValueError("parts_catalog rows must be objects")
            part=row.get("part_no")
            if not isinstance(part,str) or not part or part in seen: raise ValueError("missing or duplicated catalog part_no")
            seen.add(part)
            q=row.get("on_hand")
            if type(q) not in (int,float) or not math.isfinite(q) or q<0: raise ValueError("on_hand must be nonnegative finite number")
        prior=payload.get("history",{}).get("prior_work_orders",[])
        ids=[r.get("wo_id") for r in prior]
        if any(not x for x in ids) or len(set(ids))!=len(ids): raise ValueError("missing or duplicate history identity")
    return payload

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--hop",choices=["similar_work","parts_readiness"])
    a=ap.parse_args(); validate_payload(json.loads(Path(a.input).read_text()),a.hop); print("contract validation passed")
