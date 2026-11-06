"""Dependency-free original-input replay boundary. Local files only."""
import json,subprocess,sys,tempfile
from pathlib import Path

def clean(p):
    p=json.loads(json.dumps(p,allow_nan=False))
    p.get("provenance",{}).pop("generated_at",None)
    return p

def original_deviations(spec,measurements,coc):
    if not spec or not measurements: raise ValueError("original --spec and --measurements required; no trusted replay from supplied terminal payload alone")
    engine=Path(__file__).resolve().parents[2]/"tolerance-check/scripts/tolerance_check.py"
    with tempfile.TemporaryDirectory() as tmp:
        output=Path(tmp)/"deviations.json"
        cmd=[sys.executable,str(engine),"--spec",spec,"--measurements",measurements,"--out",str(output)]
        if coc:cmd += ["--coc",coc]
        result=subprocess.run(cmd,capture_output=True,text=True)
        if result.returncode:raise ValueError("original input replay blocked: "+result.stderr.strip())
        with output.open(encoding="utf-8") as h:return json.load(h)

def verify_deviations(p,spec,measurements,coc):
    fresh=original_deviations(spec,measurements,coc)
    if clean(p)!=clean(fresh):raise ValueError("deviations differ from original source replay; possible stale or tampered evidence")
    return fresh
