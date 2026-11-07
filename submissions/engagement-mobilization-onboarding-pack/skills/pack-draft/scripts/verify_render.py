#!/usr/bin/env python3
"""Pre-render check for the skills where the model renders from a supplied file (#1.4; checklist A23).

pack-draft drafts the pack from access-checklist.json and mobilization-pack.md, and roster-pull presents the roster
from scope.json. Neither file is trusted: this check re-runs the engines on the raw inputs and refuses, with a clean
InputError and a non-zero exit, a document that differs from the re-derivation in any field (provenance included) or
a pack that differs from the engine's rendering by a single byte. It writes nothing and repeats no value or path.

  verify_render.py --access access-checklist.json --pack mobilization-pack.md --raw-dir <raw> --staffing <staffing.json>
                   --confirmed-roster <raw>/confirmed-roster.csv --closeout <closeout governed.json>
                   --wall-register <raw>/ethical-wall-register.csv --workspace-inventory <raw>/workspace-inventory.csv
  verify_render.py --scope scope.json --raw-dir <raw> --staffing <staffing.json> --confirmed-roster <raw>/confirmed-roster.csv
"""
from safety_text import *
def rederive_scope(doc,raw_dir,staffing,roster,where="scope document"):
    """scope_digest's document for the raw inputs, under the run parameters the supplied document states."""
    import scope_digest
    return scope_digest.derive(raw_dir,staffing,roster,*run_parameters(doc,where))
def rederive_access(doc,raw_dir,staffing,roster,closeout,register,inventory,where="access checklist"):
    """(access checklist document, rendered pack entries) the raw inputs give: all four engines re-run whole. The
    earlier stages' own timestamps are overwritten in the access document, so they re-run under its stage timestamp (#1.4)."""
    import access_checklist, wall_check
    ts=stage_timestamp(doc,where)
    g=reread(wall_check.rederive(doc,raw_dir,staffing,roster,closeout,register,inventory,ts,where),"re-derived governed document")
    return access_checklist.derive_entries(g,register,inventory,ts,closeout,staffing)
def read_bytes(p,label):
    try:
        with open(p,"rb") as f: return f.read()
    except FileNotFoundError as e: raise InputError(f"missing required file: the {label} (path not repeated)") from e
    except OSError as e: raise InputError(f"cannot read the {label}: {type(e).__name__} (path not repeated)") from e
def same_pack(supplied,rendered):
    """The supplied pack must be, byte for byte, the pack the engine renders from the re-derived document."""
    want=text_bytes(None,rendered,"re-derived pack")
    if supplied==want: return
    a,b=supplied.split(b"\n"),want.split(b"\n"); n=sum(x!=y for x,y in zip(a,b))+abs(len(a)-len(b))
    need(False,f"the mobilization pack is not the pack the engines render from the raw inputs ({n} line(s) differ; text not repeated); the file was edited or is stale for the inputs given; do not draft from it - re-run the chain from the raw sources; fail closed (confidentiality-and-ethical-wall-rules.md #1.4)")
def check_supplied(doc,where,stage):
    """The supplied document is held to the stage contract and to cumulative-hold evidence, exactly as every engine
    holds the documents it reads, before it is compared with its re-derivation (#1.3, #1.4)."""
    need(isinstance(doc,dict),f"the {where} must be a JSON object, got {type(doc).__name__}; nothing verified; fail closed")
    need(doc.get("contract_version")==CONTRACT_VERSION,f"expected contract {CONTRACT_VERSION} in the {where} (value not repeated); nothing verified; fail closed")
    check_contract(doc,stage,stage); check_hold_evidence(doc,stage)
def main():
    ap=ArgParser(); ap.add_argument("--access"); ap.add_argument("--pack"); ap.add_argument("--scope")
    for k in ("--raw-dir","--staffing","--confirmed-roster"): ap.add_argument(k,required=True)
    for k in ("--closeout","--wall-register","--workspace-inventory"): ap.add_argument(k)
    a=ap.parse_args()
    if a.scope is not None:
        need(a.access is None and a.pack is None,"give either --scope or --access with --pack, not both; nothing verified; fail closed")
        s=load_json(a.scope,"scope document"); check_supplied(s,"scope document","scope")
        same_document(s,rederive_scope(s,a.raw_dir,a.staffing,a.confirmed_roster),"scope document")
        print("verified: scope.json equals the scope_digest re-derivation from the raw inputs (#1.4)"); return 0
    need(None not in (a.access,a.pack,a.closeout,a.wall_register,a.workspace_inventory),"--access needs --pack, --closeout, --wall-register and --workspace-inventory (or give --scope alone); nothing verified; fail closed")
    d=load_json(a.access,"access checklist"); check_supplied(d,"access checklist","access")
    doc,entries=rederive_access(d,a.raw_dir,a.staffing,a.confirmed_roster,a.closeout,a.wall_register,a.workspace_inventory)
    same_document(d,doc,"access checklist")
    same_pack(read_bytes(a.pack,"mobilization pack"),"\n".join(entries)+"\n")
    # The pack is read as a whole once more, in rendered order: no line, pair or run of its values may read as an
    # instruction (#4.5).
    import access_checklist
    need(not access_checklist.pack_runs(access_checklist.pack_screen(doc,entries)),"the mobilization pack reads as an instruction when its lines are read together (text not repeated); do not draft from it; fail closed (confidentiality-and-ethical-wall-rules.md #4.5)")
    print("verified: access-checklist.json and mobilization-pack.md equal the engines' re-derivation from the raw inputs (#1.4)"); return 0
if __name__=="__main__": guard(main)
