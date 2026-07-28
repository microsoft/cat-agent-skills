#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""
qr_generate.py  --  QR Code Kit builder layer.

Turns ONE JSON spec into a correct payload string, encodes it with the bundled
(vendored) segno engine as a standard QR code, saves an image, and reports
auditable metadata plus an ASCII preview.

The *encoding* is done by segno (BSD-3, Lars Heuer, vendored under ./vendor).
This script's job is the part a language model gets wrong on its own: building
and validating the payload string for each type (escaping, field rules, capacity).

Usage:
    python qr_generate.py --json '{"type":"url","data":"https://example.com"}'
    python qr_generate.py --spec spec.json
    echo '{"type":"text","data":"hello"}' | python qr_generate.py --json -

Output: a JSON object on stdout. Exit code 0 on success, 1 on error.
"""
import sys
import os
import io
import json
import argparse

# --- Make the vendored, zero-dependency segno engine importable (offline, no pip) ---
# segno is bundled under ../assets/vendor (a shipped dependency, not a skill script).
_HERE = os.path.dirname(os.path.abspath(__file__))
_VENDOR = os.path.normpath(os.path.join(_HERE, os.pardir, "assets", "vendor"))
sys.path.insert(0, _VENDOR)
import segno              # noqa: E402  (vendored)
from segno import helpers  # noqa: E402  (vendored)

SUPPORTED = ("url", "text", "email", "tel", "sms", "wifi",
             "vcard", "geo", "event", "epc")

SUPPORTED_FORMATS = ("png", "svg", "eps", "pdf")


class SpecError(ValueError):
    """Raised when a spec is invalid -- surfaced to the user, never guessed around."""


# --------------------------------------------------------------------------- #
#  Payload builders  (the value-add: correct strings the model gets wrong)     #
# --------------------------------------------------------------------------- #
def _req(spec, key):
    val = spec.get(key)
    if val is None or (isinstance(val, str) and val.strip() == ""):
        raise SpecError(f'"{key}" is required for type "{spec.get("type")}"')
    return val


def _ical_escape(text):
    """Escape a value for an iCalendar (VEVENT) text field per RFC 5545."""
    return (str(text).replace("\\", "\\\\")
                     .replace(";", "\\;")
                     .replace(",", "\\,")
                     .replace("\n", "\\n"))


def _to_ical_dt(value):
    """Accept ISO 8601 -> emit iCal basic form. Date-only -> VALUE=DATE form.

    A timezone-aware time is normalized to UTC and emitted with a trailing 'Z'
    (RFC 5545 UTC form), so an offset like +02:00 is preserved as the correct
    instant instead of being silently dropped. A naive time stays floating.
    """
    from datetime import datetime, date, timezone
    s = str(value).strip()
    try:
        if "T" in s or " " in s:
            dt = datetime.fromisoformat(s.replace(" ", "T"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc)
                return ("DATETIME", dt.strftime("%Y%m%dT%H%M%SZ"))
            return ("DATETIME", dt.strftime("%Y%m%dT%H%M%S"))
        d = date.fromisoformat(s)
        return ("DATE", d.strftime("%Y%m%d"))
    except ValueError:
        raise SpecError(f'Invalid date/time "{value}"; use ISO 8601 '
                        f'(e.g. 2026-08-01T18:00 or 2026-08-01)')


def build_url(spec):
    data = _req(spec, "data").strip()
    lower = data.lower()
    has_scheme = "://" in data or lower.startswith(("mailto:", "tel:", "sms:", "geo:"))
    warning = None
    if not has_scheme:
        data = "https://" + data
        warning = 'no URL scheme supplied; defaulted to "https://"'
    return data, warning


def build_text(spec):
    return str(_req(spec, "data")), None


def build_email(spec):
    to = _req(spec, "to")
    return helpers.make_make_email_data(
        to=to, cc=spec.get("cc"), bcc=spec.get("bcc"),
        subject=spec.get("subject"), body=spec.get("body")), None


def build_tel(spec):
    num = _req(spec, "number")
    cleaned = "".join(ch for ch in str(num) if ch.isdigit() or ch == "+")
    if not cleaned:
        raise SpecError('"number" contains no digits')
    return "tel:" + cleaned, None


def build_sms(spec):
    num = _req(spec, "number")
    cleaned = "".join(ch for ch in str(num) if ch.isdigit() or ch == "+")
    if not cleaned:
        raise SpecError('"number" contains no digits')
    message = spec.get("message", "")
    # SMSTO is the most widely scanned SMS QR format across phones.
    return f"SMSTO:{cleaned}:{message}", None


def build_wifi(spec):
    ssid = _req(spec, "ssid")
    security = spec.get("security")
    password = spec.get("password")
    warning = None
    if security is not None:
        sec_norm = str(security).upper()
        if sec_norm not in ("WPA", "WEP", "NOPASS"):
            raise SpecError('"security" must be one of WPA, WEP, or nopass')
        security = "nopass" if sec_norm == "NOPASS" else sec_norm
    if password and security is None:
        security = "WPA"
        warning = 'password supplied without "security"; assumed WPA'
    if security in (None, "nopass"):
        password = None
    return helpers.make_wifi_data(
        ssid=ssid, password=password, security=security,
        hidden=bool(spec.get("hidden", False))), warning


def build_vcard(spec):
    name = _req(spec, "name")
    displayname = spec.get("displayname") or name
    return helpers.make_vcard_data(
        name=name, displayname=displayname,
        email=spec.get("email"), phone=spec.get("phone"),
        cellphone=spec.get("cellphone"), url=spec.get("url"),
        org=spec.get("org"), title=spec.get("title"),
        memo=spec.get("memo"), nickname=spec.get("nickname"),
        birthday=spec.get("birthday"), street=spec.get("street"),
        city=spec.get("city"), region=spec.get("region"),
        zipcode=spec.get("zipcode"), country=spec.get("country")), None


def build_geo(spec):
    try:
        lat = float(_req(spec, "lat"))
        lng = float(_req(spec, "lng"))
    except (TypeError, ValueError):
        raise SpecError('"lat" and "lng" must be numbers')
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise SpecError("latitude must be -90..90 and longitude -180..180")
    return helpers.make_geo_data(lat, lng), None


def build_event(spec):
    summary = _req(spec, "summary")
    start_kind, start = _to_ical_dt(_req(spec, "start"))
    lines = ["BEGIN:VEVENT", f"SUMMARY:{_ical_escape(summary)}"]
    if start_kind == "DATE":
        lines.append(f"DTSTART;VALUE=DATE:{start}")
    else:
        lines.append(f"DTSTART:{start}")
    if spec.get("end"):
        end_kind, end = _to_ical_dt(spec["end"])
        lines.append(f"DTEND;VALUE=DATE:{end}" if end_kind == "DATE" else f"DTEND:{end}")
    if spec.get("location"):
        lines.append(f"LOCATION:{_ical_escape(spec['location'])}")
    if spec.get("description"):
        lines.append(f"DESCRIPTION:{_ical_escape(spec['description'])}")
    lines.append("END:VEVENT")
    return "\r\n".join(lines), None


# --------------------------------------------------------------------------- #
#  Encoding + output                                                          #
# --------------------------------------------------------------------------- #
_BUILDERS = {
    "url": build_url, "text": build_text, "email": build_email,
    "tel": build_tel, "sms": build_sms, "wifi": build_wifi,
    "vcard": build_vcard, "geo": build_geo, "event": build_event,
}


def _ascii_preview(qr, border=2, max_modules=41):
    """Render a compact ASCII/block preview from the QR matrix (offline eyeball check)."""
    size = qr.symbol_size(scale=1, border=0)[0]
    if size > max_modules:
        return None  # too big to preview cleanly in text
    rows = []
    for row in qr.matrix_iter(scale=1, border=border):
        rows.append("".join("\u2588\u2588" if bit else "  " for bit in row))
    return "\n".join(rows)


def generate(spec):
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    qtype = str(spec.get("type", "")).lower().strip()
    if qtype not in SUPPORTED:
        raise SpecError(f'"type" must be one of: {", ".join(SUPPORTED)} (got "{qtype}")')

    out_opts = spec.get("output") or {}
    error = str(out_opts.get("error", "M")).upper()
    if error not in ("L", "M", "Q", "H"):
        raise SpecError('output.error must be one of L, M, Q, H')

    warning = None
    # EPC payment has its own strict factory (fixed ECC "M", capacity checked).
    if qtype == "epc":
        name = _req(spec, "name")
        iban = _req(spec, "iban")
        amount = _req(spec, "amount")
        try:
            # Build the exact EPC/SEPA payload segno itself encodes (same internal
            # helper make_epc_qr calls), then make the QR from those same bytes so
            # the reported payload matches the QR content exactly. EPC forces ECC
            # "M" with boost disabled, per the standard.
            epc_data = helpers._make_epc_qr_data(
                name=name, iban=iban, amount=amount,
                text=spec.get("text"), reference=spec.get("reference"),
                bic=spec.get("bic"))
            qr = segno.make_qr(epc_data, error="m", boost_error=False)
        except SpecError:
            raise
        except (ValueError, ArithmeticError) as exc:
            raise SpecError(str(exc))
        # segno's auto-encoding always selects UTF-8 first (it never fails), so
        # decoding as UTF-8 reproduces the payload exactly.
        payload = epc_data.decode("utf-8", "replace")
        if error != "M":
            warning = 'EPC standard mandates error level "M"; ignored requested level'
        error = "M"
    else:
        try:
            payload, warning = _BUILDERS[qtype](spec)
        except SpecError:
            raise
        except ValueError as exc:
            raise SpecError(str(exc))
        try:
            qr = segno.make_qr(payload, error=error.lower())
        except segno.DataOverflowError as exc:
            raise SpecError(f"data too large to encode as a QR code: {exc}")

    # --- output file ---
    fmt = str(out_opts.get("format", "")).lower().strip()
    out = out_opts.get("out") or spec.get("out")
    if not out:
        out = f"qr_{qtype}.{fmt or 'png'}"
    if fmt and not out.lower().endswith("." + fmt):
        out = os.path.splitext(out)[0] + "." + fmt
    if not os.path.splitext(out)[1]:
        out += "." + (fmt or "png")

    kind = os.path.splitext(out)[1].lstrip(".").lower()
    if kind not in SUPPORTED_FORMATS:
        raise SpecError(f'unsupported output format "{kind}"; '
                        f'use one of: {", ".join(SUPPORTED_FORMATS)}')

    try:
        scale = int(out_opts.get("scale", 10))
    except (TypeError, ValueError):
        raise SpecError('output.scale must be an integer')
    try:
        border = int(out_opts["border"]) if out_opts.get("border") is not None else 4
    except (TypeError, ValueError):
        raise SpecError('output.border must be an integer')
    if scale < 1:
        raise SpecError('output.scale must be >= 1')
    if border < 0:
        raise SpecError('output.border must be >= 0')

    save_kwargs = dict(scale=scale, border=border)
    dark = out_opts.get("dark")
    light = out_opts.get("light")
    if dark:
        save_kwargs["dark"] = dark
    if light is not None:
        save_kwargs["light"] = light

    try:
        qr.save(out, **save_kwargs)
    except (TypeError, ValueError) as exc:
        raise SpecError(f'could not save QR as "{kind}": {exc}')
    size_px = qr.symbol_size(scale=scale, border=border)

    result = {
        "ok": True,
        "type": qtype,
        "payload": payload,
        "file": os.path.abspath(out),
        "format": os.path.splitext(out)[1].lstrip(".").lower(),
        "version": qr.version,
        "error": qr.error,
        "designator": qr.designator,
        "modules": qr.symbol_size(scale=1, border=0)[0],
        "image_pixels": {"width": size_px[0], "height": size_px[1]},
        "engine": "segno (BSD-3, vendored)",
    }
    if warning:
        result["warning"] = warning
    preview = _ascii_preview(qr)
    if preview:
        result["preview"] = preview
    return result


def _load_spec(args):
    raw = None
    if args.spec:
        with open(args.spec, "r", encoding="utf-8") as fh:
            raw = fh.read()
    elif args.json is not None:
        raw = sys.stdin.read() if args.json == "-" else args.json
    else:
        # allow piping the JSON with no flag
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    if not raw or not raw.strip():
        raise SpecError("no spec provided; pass --json '<json>' or --spec <file>")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecError(f"spec is not valid JSON: {exc}")
    if args.out:
        spec.setdefault("output", {})["out"] = args.out
    return spec


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a QR code from a JSON spec.")
    parser.add_argument("--json", help="Inline JSON spec, or '-' to read from stdin.")
    parser.add_argument("--spec", help="Path to a JSON spec file.")
    parser.add_argument("--out", help="Output file path (overrides output.out in the spec).")
    args = parser.parse_args(argv)
    # QR payloads and the ASCII preview are UTF-8; don't let a legacy console
    # code page (e.g. Windows cp1252) corrupt or crash the JSON output.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    try:
        spec = _load_spec(args)
        result = generate(spec)
    except SpecError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout)
        sys.stdout.write("\n")
        return 1
    except Exception as exc:  # noqa: BLE001 - surface unexpected errors honestly
        json.dump({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sys.stdout)
        sys.stdout.write("\n")
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
