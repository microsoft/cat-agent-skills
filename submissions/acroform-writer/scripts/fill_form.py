#!/usr/bin/env python3
"""
fill_form.py — inspect, fill, and (optionally) flatten AcroForm PDF fields.

Usage:
  # 1. Discover fields (always run this first)
  python fill_form.py list  <input.pdf>

  # 2. Fill from a JSON file of {field_name: value}
  python fill_form.py fill  <input.pdf> <data.json> <output.pdf> [--flatten]

Exit codes:
  0  success
  1  no AcroForm found (not a fillable PDF — needs an overlay/OCR approach instead)
  2  other error (bad path, malformed JSON, etc.)
"""
import sys
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject


def die(msg: str, code: int = 2):
    print(json.dumps({"error": msg}))
    sys.exit(code)


def cmd_list(pdf_path: str):
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    if not fields:
        die(
            "No AcroForm fields found in this PDF. It is likely a scanned/flat "
            "PDF with no fillable fields — this script cannot help; consider an "
            "overlay (reportlab) or OCR-based approach instead.",
            code=1,
        )

    out = []
    for name, f in fields.items():
        entry = {
            "name": name,
            "type": str(f.get("/FT")),
            "value": f.get("/V"),
        }
        # Dropdown / choice options, if present
        if f.get("/Opt"):
            entry["options"] = [str(o) for o in f.get("/Opt")]
        # Checkbox / radio "on" state, if discoverable
        states = f.get("/_States_")
        if states:
            entry["states"] = list(states)
        out.append(entry)

    print(json.dumps({"field_count": len(out), "fields": out}, indent=2, default=str))


def cmd_fill(pdf_path: str, data_path: str, out_path: str, flatten: bool):
    data = json.loads(Path(data_path).read_text())

    reader = PdfReader(pdf_path)
    if not reader.get_fields():
        die(
            "No AcroForm fields found in this PDF — nothing to fill. Run the "
            "'list' command first to confirm this PDF has real form fields.",
            code=1,
        )

    writer = PdfWriter()
    writer.append(reader)

    # Fill every page (fields can live on any page)
    for page in writer.pages:
        writer.update_page_form_field_values(page, data, auto_regenerate=False)

    unmatched = set(data.keys()) - set((reader.get_fields() or {}).keys())

    if flatten:
        # Make viewers render the typed-in appearance instead of regenerating it
        if "/AcroForm" in writer._root_object:
            writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

        # Mark every field read-only (Ff bit 1) so it no longer behaves as an
        # editable form field in viewers that respect the flag.
        from pypdf.generic import NumberObject

        for page in writer.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            for a in annots:
                obj = a.get_object()
                if obj.get("/Subtype") == "/Widget":
                    ff = int(obj.get("/Ff", 0))
                    obj[NameObject("/Ff")] = NumberObject(ff | 1)

    with open(out_path, "wb") as fh:
        writer.write(fh)

    result = {
        "output": out_path,
        "fields_filled": len(data) - len(unmatched),
        "unmatched_fields": sorted(unmatched),
        "flattened": flatten,
    }
    print(json.dumps(result, indent=2))
    if unmatched:
        # Non-fatal, but surfaced clearly so the caller can flag it to the user
        print(
            f"WARNING: {len(unmatched)} field(s) in the data file did not match "
            f"any field in the PDF: {sorted(unmatched)}",
            file=sys.stderr,
        )


def main():
    if len(sys.argv) < 3:
        die(__doc__, code=2)

    mode = sys.argv[1]
    if mode == "list":
        cmd_list(sys.argv[2])
    elif mode == "fill":
        if len(sys.argv) < 5:
            die("fill requires: <input.pdf> <data.json> <output.pdf> [--flatten]", code=2)
        flatten = "--flatten" in sys.argv[5:]
        cmd_fill(sys.argv[2], sys.argv[3], sys.argv[4], flatten)
    else:
        die(f"Unknown mode '{mode}'. Use 'list' or 'fill'.", code=2)


if __name__ == "__main__":
    main()
