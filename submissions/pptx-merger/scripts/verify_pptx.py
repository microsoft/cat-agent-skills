#!/usr/bin/env python3
"""
verify_pptx.py — Hard gate: a PPTX is "good" only if it actually opens.

Two prior rounds passed a structural validator yet produced files PowerPoint
could not open, because that validator checks neither the content-types
namespace prefix nor whether the package truly loads. This stage closes that
gap: it runs the structural checks AND performs a real render conversion with
LibreOffice. If the render step is unavailable in the sandbox it degrades to
structural-only and says so, rather than claiming success it can't prove.

Usage:
    python verify_pptx.py <file.pptx> [--render] [--json]

--render forces the render check on (it is on by default when soffice exists).
Exit code 0 only if every enabled check passes.
"""

import sys
import json
import shutil
import zipfile
import argparse
import subprocess
import tempfile
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    import sys
    sys.exit("ERROR: lxml is required. Install it with: pip install lxml")
_SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)

NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_P  = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_R  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def structural_checks(path: Path):
    errors, warnings = [], []
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad is not None:
            errors.append(f"ZIP CRC error in {bad}")
        names = set(z.namelist())

        if "[Content_Types].xml" not in names:
            errors.append("[Content_Types].xml missing")
        else:
            ct_bytes = z.read("[Content_Types].xml")
            root = etree.fromstring(ct_bytes, _SAFE_PARSER)
            # The Types element MUST be in the default (unprefixed) namespace.
            if root.prefix is not None:
                errors.append(
                    f"[Content_Types].xml uses namespace prefix '{root.prefix}:' — "
                    "must be the default namespace or the package will not open.")
            declared = {ov.get("PartName") for ov in root.findall(f"{{{NS_CT}}}Override")}
            defaults = {d.get("Extension", "").lower() for d in root.findall(f"{{{NS_CT}}}Default")}

        # Every part referenced by a .rels must exist; no absolute internal targets.

        zip_names = set(names)
        for n in names:
            if n.endswith(".rels"):
                try:
                    root = etree.fromstring(z.read(n), _SAFE_PARSER)
                except etree.XMLSyntaxError as exc:
                    errors.append(f"{n}: malformed XML — {exc}")
                    continue
                part_folder = "/".join(n.split("/")[:-2])  
                for rel in root:
                    tgt = rel.get("Target", "")
                    mode = rel.get("TargetMode", "")
                    if mode == "External":
                        continue
                    if tgt.startswith("/"):
                        errors.append(f"{n}: absolute internal Target '{tgt}' "
                                      "(needs relative path or TargetMode=External)")
                        continue
                    import posixpath
                    resolved = posixpath.normpath(part_folder + "/" + tgt).lstrip("/")
                    if resolved not in zip_names:
                        errors.append(f"{n}: Target '{tgt}' resolves to '{resolved}' which is missing from ZIP")

        # presentation.xml sanity: masters and slides have required ids.
        if "ppt/presentation.xml" in names:
            pr = etree.fromstring(z.read("ppt/presentation.xml"), _SAFE_PARSER)
            gids = []
            ml = pr.find(f".//{{{NS_P}}}sldMasterIdLst")
            if ml is not None:
                for e in ml:
                    if not e.get("id"):
                        errors.append("sldMasterId missing required 'id' attribute")
                    else:
                        gids.append(e.get("id"))
            # collect layout ids from every master for global-uniqueness check
            for n in names:
                if n.startswith("ppt/slideMasters/slideMaster") and n.endswith(".xml"):
                    m = etree.fromstring(z.read(n), _SAFE_PARSER)
                    ll = m.find(f".//{{{NS_P}}}sldLayoutIdLst")
                    if ll is not None:
                        for e in ll:
                            if e.get("id"):
                                gids.append(e.get("id"))
            dupes = {x for x in gids if gids.count(x) > 1}
            if dupes:
                errors.append(f"Duplicate global master/layout IDs: {sorted(dupes)}")

    return errors, warnings


def render_check(path: Path):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None, "soffice not available; render check skipped"
    with tempfile.TemporaryDirectory() as td:
        prof = Path(td) / "profile"
        outdir = Path(td) / "out"
        outdir.mkdir()
        try:
            subprocess.run(
                [soffice, "--headless", f"-env:UserInstallation=file://{prof}",
                 "--convert-to", "pdf", "--outdir", str(outdir), str(path)],
                capture_output=True, timeout=180,
            )
        except subprocess.TimeoutExpired:
            return False, "render timed out"
        pdfs = list(outdir.glob("*.pdf"))
        if pdfs and pdfs[0].stat().st_size > 0:
            return True, f"rendered to {pdfs[0].stat().st_size} byte PDF"
        return False, "LibreOffice could not load the file"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--render", action="store_true",
                    help="Force render check (default: on when soffice exists).")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.pptx)
    result = {"ok": False, "stage": "validate", "file": str(path),
              "structural_errors": [], "render": None}

    if not path.exists():
        result["structural_errors"] = ["file does not exist"]
        print(json.dumps(result, indent=2) if args.json else "file does not exist")
        return 2

    errors, warnings = structural_checks(path)
    result["structural_errors"] = errors
    result["warnings"] = warnings

    soffice_present = shutil.which("soffice") or shutil.which("libreoffice")
    do_render = args.render or (soffice_present and not args.no_render)

    if args.render and not soffice_present:
        errors = errors + ["render: soffice/libreoffice not found but --render was explicitly requested"]
        result["render"] = {"passed": False, "detail": "soffice not available"}
    elif do_render:
        ok, msg = render_check(path)
        result["render"] = {"passed": ok, "detail": msg}
        if ok is False:
            errors = errors + [f"render: {msg}"]
    else:
        if args.no_render:
            result["render"] = {"passed": None, "detail": "render disabled (--no-render)"}
        elif not soffice_present:
            result["render"] = {"passed": None, "detail": "soffice not available; render check skipped"}
        else:
            result["render"] = {"passed": None, "detail": "render check skipped"}

    
    render_failed = do_render and result["render"]["passed"] is False
    result["ok"] = (len(errors) == 0) and (not render_failed)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["ok"]:
            r = result["render"]["detail"] if result["render"] else "structural only"
            print(f"PASS — {r}")
        else:
            print("FAIL")
            for e in errors:
                print(f"  - {e}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
