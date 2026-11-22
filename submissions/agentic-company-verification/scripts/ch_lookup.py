#!/usr/bin/env python3
"""Companies House lookup. Usage:
  python ch_lookup.py search "Tesco"
  python ch_lookup.py profile|officers|pscs|charges|insolvency|filings 00445790
Requires env var COMPANIES_HOUSE_API_KEY.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.company-information.service.gov.uk"


def get(path):
    key = os.environ.get("COMPANIES_HOUSE_API_KEY")
    if not key:
        sys.exit("COMPANIES_HOUSE_API_KEY is not set")
    token = base64.b64encode(f"{key}:".encode()).decode()
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {'not found' if e.code == 404 else e.reason}")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "search":
        data = get("/search/companies?items_per_page=5&q=" + urllib.parse.quote(arg))
    else:
        num = arg.zfill(8) if arg.isdigit() else arg.upper()
        paths = {
            "profile": f"/company/{num}",
            "officers": f"/company/{num}/officers",
            "pscs": f"/company/{num}/persons-with-significant-control",
            "charges": f"/company/{num}/charges",
            "insolvency": f"/company/{num}/insolvency",
            "filings": f"/company/{num}/filing-history",
        }
        if cmd not in paths:
            sys.exit(__doc__)
        data = get(paths[cmd])
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
