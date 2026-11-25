#!/usr/bin/env python3
"""Verify a slide built by the ideate skill against its source slide.

Runs the required checks from step 5 of SKILL.md programmatically. On success it
prints REIMAGINE_THIS_SLIDE_VERIFY_OK=1 followed by JSON. On an execution error it prints
REIMAGINE_THIS_SLIDE_VERIFY_ERR_REASON=... to stderr and exits nonzero.

  1. numbers_exact  [required] -- in strict mode, every source figure reappears ON
                       THE BUILT SLIDE,
                       or in its speaker notes if it was deliberately trimmed there,
                       as the SAME token: sign, currency, percent, magnitude suffix
                       and per-unit ("/month") included. ERRORS: the figure is
                       absent; it survives only in the notes while a near-miss of it
                       shows on the slide face (an altered headline); or it was
                       REFORMATTED (e.g. "2,300,000" where the source said "2.3M").
                       Pass --allow-reformat to downgrade that last one to a warning
                       when the user actually asked for the new formatting.

                       Counted as IDENTICAL, being rendering noise rather than a
                       rewrite: a trailing zero ("2.30M" == "2.3M") and a magnitude
                       word versus its symbol ("2.3 million" == "2.3M").

                       Counted as an ALTERATION, never as a reformat, because the
                       meaning changes: a dropped currency symbol ($5M -> 5M), a
                       dropped percent (5% -> 0.05) and a dropped cadence
                       (5/month -> 5). --allow-reformat will NOT wave these through.

                       In broad mode, a source figure may be omitted when no
                       suspicious replacement is present. Clean omissions are
                       warnings and are reported in allowed_omissions; alterations,
                       substitutions, and unapproved reformats remain errors.
  1b. chart_data_readable [required] -- every chart on either slide could be parsed.
                       A chart this script cannot read is an error, not a pass: a
                       chart-heavy source slide must never verify vacuously by
                       yielding no numbers at all.
  1c. footer continuity [required] -- footer, classification and date text on the
                       built slide matches the source, and slide-number presence
                       matches. Slide numbers themselves may differ because the
                       alternatives occupy different positions.
  2. placeholders   [advisory] -- unresolved "[... confirm ...]" markers on the
                       slide OR in its notes. Always a WARNING, never an error: the
                       skill treats these as expected. They must still be named in
                       the handoff and never shipped silently.
  3. position       [required] -- the built slide sits at source + expected offset.
                       --built is REQUIRED; --expected-offset defaults to 1 and
                       should be 1, 2, or 3 for ideate's three-slide output.
  4. theme          [required] -- no thin accent rule under the title, and no font
                       or visual effect type that appears nowhere else in the deck.
  5. title present  [required] -- the built slide has a non-empty title placeholder.

NOT checked. Verify these by hand; the script never claims to cover them:
  * that the SOURCE slide is unmodified -- that needs a pre-build baseline
  * theme COLORS -- only fonts are compared
  * numbers locked inside pictures or SmartArt
  * most chart number formats -- explicit percentage data-label formats are read,
    but formats that render 2300000 as "2.3M" (or vice versa) are not inspected

Charts are read where python-pptx exposes them (categories and series values).

Usage:
    python3 verify_slide.py --deck /abs/path/deck.pptx --source 4 --built 5 \
        --expected-offset 1
    python3 verify_slide.py --deck /abs/path/deck.pptx --source 4 --built 5 \
        --expected-offset 1 --allow-reformat
    python3 verify_slide.py --deck /abs/path/deck.pptx --source 4 --built 5 \
        --expected-offset 1 --content-mode broad

Slide numbers are 1-based, matching the numbers shown in PowerPoint.

Exit codes:  0 = every required check passed (warnings allowed)
             1 = a required check failed
             2 = could not run (bad path, unreadable deck, missing dependency)
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

EMU_PER_INCH = 914400

# A magnitude suffix must be glued to the digits ("2.3M"), so that a unit written
# with a space ("330 m" = 330 metres) is not misread as 330 million. A sign must be
# glued too: in "2.3M - 1.9M" the dash separates two positive figures, and reading
# it as negative 1.9M invents a number the slide never had. Currency and percent are
# captured as well -- "-5%" and "5" are different figures, and collapsing them to
# the same float was how an altered number used to slip through.
NUM_RE = re.compile(
    r"(?<![\d.,])"
    r"(?:(?P<cur1>[$\u20ac\u00a3\u00a5])\s*)?"
    r"(?P<sign>[-+\u2212])?"
    r"(?:(?P<cur2>[$\u20ac\u00a3\u00a5])\s*)?"
    r"(?P<num>\d[\d,]*(?:\.\d+)?)"
    r"(?:\s*(?P<word>million|billion|trillion|thousand)\b"
    r"|(?P<sym>bn|[kmbt])\b)?"
    r"\s*(?P<pct>%)?"
    r"(?:\s*/\s*(?P<per>[A-Za-z]+))?",
    re.IGNORECASE,
)

MAGNITUDES = {
    "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12,
    "k": 1e3, "m": 1e6, "b": 1e9, "bn": 1e9, "t": 1e12,
}

# "2.3 million" and "2.3M" are the same figure written two ways, so they collapse
# to one token. "2,300,000" does NOT collapse to "2.3M" -- expanding a magnitude
# into full digits rewrites what the audience reads, so it surfaces as a warning.
MAG_CANON = {
    "thousand": "k", "k": "k", "million": "m", "m": "m",
    "billion": "b", "b": "b", "bn": "b", "trillion": "t", "t": "t",
}

PLACEHOLDER_RE = re.compile(
    r"\[[^\]]*(?:confirm|tbd|placeholder|xxx|fill in)[^\]]*\]", re.IGNORECASE
)
LITERAL_SLIDE_NUMBER_RE = re.compile(r"\s*\d{1,3}\s*")
FOOTER_BOTTOM_MARGIN = 0.45 * EMU_PER_INCH
FOOTER_BOTTOM_OVERHANG = 0.10 * EMU_PER_INCH
FOOTER_MAX_HEIGHT = 0.55 * EMU_PER_INCH
CUSTOM_FOOTER_MAX_CHARS = 120
CUSTOM_FOOTER_MAX_LINES = 2


def canonical(match):
    """A comparable token: sign, currency, digits, magnitude, percent, per-unit."""
    raw_sign = match.group("sign") or ""
    sign = "-" if raw_sign in {"-", "\u2212"} else ("+" if raw_sign == "+" else "")
    currency = match.group("cur1") or match.group("cur2") or ""
    digits = match.group("num").replace(",", "")
    if "." in digits:
        digits = digits.rstrip("0").rstrip(".")
    magnitude = (match.group("word") or match.group("sym") or "").lower()
    magnitude = MAG_CANON.get(magnitude, "")
    percent = "%" if match.group("pct") else ""
    per = ("/" + match.group("per").lower()) if match.group("per") else ""
    return "%s%s%s%s%s%s" % (sign, currency, digits, magnitude, percent, per)


def signature(match):
    """The SEMANTIC part of a figure: sign, currency, percent, per-unit.

    Two figures may only be called "the same number reformatted" when these match.
    Dropping a currency symbol, a percent or a "/month" changes what the figure
    means, so it is an alteration, not a formatting choice.
    """
    raw_sign = match.group("sign") or ""
    sign = "-" if raw_sign in {"-", "\u2212"} else ("+" if raw_sign == "+" else "")
    currency = match.group("cur1") or match.group("cur2") or ""
    percent = "%" if match.group("pct") else ""
    per = ("/" + match.group("per").lower()) if match.group("per") else ""
    return "%s%s%s%s" % (sign, currency, percent, per)


def fail(message, code=2):
    print(
        "REIMAGINE_THIS_SLIDE_VERIFY_ERR_REASON=%s" % message.replace("\n", " "),
        file=sys.stderr,
    )
    print(json.dumps({"ok": bool(0), "errors": [message], "warnings": []}, indent=2))
    sys.exit(code)


def extract_numbers(text):
    """Return [{'raw','token','sig','value'}, ...] for every figure in text."""
    found = []
    for match in NUM_RE.finditer(text):
        digits = match.group("num").replace(",", "")
        try:
            value = float(digits)
        except ValueError:
            continue
        suffix = (match.group("word") or match.group("sym") or "").lower()
        if suffix in MAGNITUDES:
            value *= MAGNITUDES[suffix]
        if match.group("pct"):
            value /= 100.0
        if (match.group("sign") or "") in {"-", "\u2212"}:
            value = -value
        found.append({
            "raw": match.group(0).strip(),
            "token": canonical(match),
            "sig": signature(match),
            "value": value,
        })
    return found


def formatted_chart_value(value, number_format):
    """Render explicit percentage data-label formats used by PowerPoint charts."""
    if not number_format or "%" not in number_format:
        return None
    section = number_format.split(";", 1)[0]
    match = re.search(r"0(?:\.(0+))?%", section)
    if not match:
        return None
    decimals = len(match.group(1) or "")
    return ("%.*f%%" % (decimals, float(value) * 100.0))


def chart_text(shape, unreadable):
    """Categories and plotted values from a native chart.

    A category axis that won't parse is recorded rather than swallowed: silently
    returning "" here would let a chart-only slide report chart_data_readable=true
    while its numbers went unchecked, which is the exact false pass this check
    exists to prevent.
    """
    parts = []
    for plot in shape.chart.plots:
        try:
            parts.extend(str(c) for c in plot.categories if c is not None)
        except (AttributeError, ValueError, TypeError) as exc:
            unreadable.append("shape %s categories (%s)"
                              % (getattr(shape, "shape_id", "?"),
                                 exc.__class__.__name__))
        number_format = None
        try:
            if plot.has_data_labels and plot.data_labels.show_value:
                number_format = plot.data_labels.number_format
        except (AttributeError, ValueError, TypeError):
            pass
        for series in plot.series:
            values = [v for v in series.values if v is not None]
            parts.extend(str(v) for v in values)
            if number_format:
                parts.extend(
                    rendered for rendered in (
                        formatted_chart_value(v, number_format) for v in values
                    ) if rendered is not None
                )
    return "\n".join(parts)


def shape_text(shape, unreadable, pictures):
    """Text from a shape, including grouped shapes, table cells and chart data."""
    parts = []
    if getattr(shape, "has_text_frame", False):
        parts.append(shape.text_frame.text)
    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    if getattr(shape, "has_chart", False):
        try:
            parts.append(chart_text(shape, unreadable))
        except Exception as exc:  # noqa: BLE001 - any failure must be surfaced
            unreadable.append("shape %s (%s)"
                              % (getattr(shape, "shape_id", "?"),
                                 exc.__class__.__name__))
    try:
        if getattr(shape, "image", None) is not None:
            pictures.append(getattr(shape, "shape_id", "?"))
    except (AttributeError, ValueError, TypeError):
        pass
    if getattr(shape, "shape_type", None) is not None and hasattr(shape, "shapes"):
        for child in shape.shapes:
            parts.append(shape_text(child, unreadable, pictures))
    return "\n".join(p for p in parts if p)


def slide_text(slide, unreadable, pictures, excluded_shape_ids=None):
    excluded_shape_ids = excluded_shape_ids or set()
    return "\n".join(
        shape_text(s, unreadable, pictures)
        for s in slide.shapes
        if s.shape_id not in excluded_shape_ids
    )


def text_only(shape):
    """Text that visibly belongs to a footer candidate shape."""
    parts = []
    if getattr(shape, "has_text_frame", False):
        parts.append(shape.text_frame.text)
    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(part for part in parts if part)


def normalize_footer_text(text):
    return " ".join(text.split())


def field_types(shape):
    """DrawingML field types used by a shape, e.g. slidenum or datetime."""
    found = set()
    for element in shape.element.iter():
        if element.tag.rsplit("}", 1)[-1] != "fld":
            continue
        field_type = element.attrib.get("type", "").strip().lower()
        if field_type:
            found.add(field_type)
    return found


def placeholder_role(shape):
    """Return footer/date/slide_number for a real PowerPoint placeholder."""
    if not getattr(shape, "is_placeholder", False):
        return None
    try:
        from pptx.enum.shapes import PP_PLACEHOLDER

        placeholder_type = shape.placeholder_format.type
    except (AttributeError, KeyError, ValueError):
        return None
    if placeholder_type == PP_PLACEHOLDER.SLIDE_NUMBER:
        return "slide_number"
    if placeholder_type == PP_PLACEHOLDER.DATE:
        return "date"
    if placeholder_type == PP_PLACEHOLDER.FOOTER:
        return "footer"
    return None


def is_bottom_footer_candidate(shape, presentation):
    """Conservative fallback for custom footer/classification text boxes."""
    raw_text = text_only(shape).strip()
    if not raw_text:
        return False
    if shape.top is None or shape.height is None:
        return False
    bottom_margin = presentation.slide_height - (shape.top + shape.height)
    return (
        -FOOTER_BOTTOM_OVERHANG <= bottom_margin <= FOOTER_BOTTOM_MARGIN
        and shape.height <= FOOTER_MAX_HEIGHT
        and len(normalize_footer_text(raw_text)) <= CUSTOM_FOOTER_MAX_CHARS
        and len(raw_text.splitlines()) <= CUSTOM_FOOTER_MAX_LINES
    )


def footer_signature(slide, presentation):
    """Footer text plus slide-number presence, with artifact shape IDs."""
    entries = []
    slide_number_present = False
    artifact_shape_ids = set()

    for shape in slide.shapes:
        role = placeholder_role(shape)
        fields = field_types(shape)
        text = normalize_footer_text(text_only(shape))
        is_slide_number = (
            role == "slide_number"
            or "slidenum" in fields
            or (
                is_bottom_footer_candidate(shape, presentation)
                and bool(LITERAL_SLIDE_NUMBER_RE.fullmatch(text))
            )
        )
        is_footer = role in {"footer", "date"} or is_bottom_footer_candidate(
            shape, presentation
        )

        if is_slide_number:
            slide_number_present = True
            artifact_shape_ids.add(shape.shape_id)
            continue
        if not is_footer:
            continue

        artifact_shape_ids.add(shape.shape_id)
        if text:
            entries.append((role or "footer", text))
        elif role == "date" and any(
            field_type.startswith("datetime") for field_type in fields
        ):
            entries.append(("date", "<dynamic date>"))

    return {
        "entries": sorted(entries),
        "text": [text for _, text in sorted(entries)],
        "slide_number_present": slide_number_present,
        "shape_ids": artifact_shape_ids,
    }


def notes_text(slide):
    if not slide.has_notes_slide:
        return ""
    frame = slide.notes_slide.notes_text_frame
    return frame.text if frame is not None else ""


def slide_fonts(slide):
    fonts = set()
    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if run.font.name:
                    fonts.add(run.font.name)
    return fonts


def theme_fonts(presentation):
    """Return every typeface declared by the presentation's theme."""
    try:
        from pptx.opc.constants import RELATIONSHIP_TYPE as RT

        theme_part = presentation.slide_master.part.part_related_by(RT.THEME)
        root = ET.fromstring(theme_part.blob)
    except (KeyError, ValueError, ET.ParseError):
        return set()

    fonts = set()
    for family_tag in ("majorFont", "minorFont"):
        for family in root.iter():
            if family.tag.rsplit("}", 1)[-1] != family_tag:
                continue
            for element in family.iter():
                typeface = element.attrib.get("typeface", "").strip()
                if typeface:
                    fonts.add(typeface)
    return fonts


def slide_effect_types(slide):
    """Return DrawingML effect types used by shapes on a slide."""
    effect_tags = {
        "outerShdw",
        "innerShdw",
        "prstShdw",
        "glow",
        "reflection",
        "softEdge",
        "scene3d",
        "sp3d",
    }
    found = set()
    for shape in slide.shapes:
        for element in shape.element.iter():
            local_name = element.tag.rsplit("}", 1)[-1]
            if local_name in effect_tags:
                found.add(local_name)
    return found


def find_accent_line(slide):
    """Heuristic: a wide, very short shape sitting just under the topmost text."""
    text_shapes = [
        s for s in slide.shapes
        if getattr(s, "has_text_frame", False) and s.text_frame.text.strip()
        and s.top is not None
    ]
    if not text_shapes:
        return None
    title = min(text_shapes, key=lambda s: s.top)
    title_bottom = title.top + (title.height or 0)
    for shape in slide.shapes:
        if shape is title or shape.top is None or shape.height is None:
            continue
        if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
            continue
        thin = shape.height <= 0.12 * EMU_PER_INCH
        wide = (shape.width or 0) >= 1.0 * EMU_PER_INCH
        just_below = title_bottom <= shape.top <= title_bottom + 0.6 * EMU_PER_INCH
        if thin and wide and just_below:
            return shape.shape_id
    return None


def title_text(slide):
    """Return text from the required title placeholder."""
    if slide.shapes.title is None:
        return ""
    return slide.shapes.title.text.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Verify an ideate slide against its source slide."
    )
    parser.add_argument("--deck", required=True,
                        help="Absolute path to the .pptx file.")
    parser.add_argument("--source", required=True, type=int,
                        help="1-based number of the original slide.")
    parser.add_argument("--built", required=True, type=int,
                        help="1-based number of the built slide. Required: the "
                             "script must not assume the position, because where the "
                             "slide actually landed is one of the things it checks.")
    parser.add_argument("--expected-offset", type=int, default=1,
                        help="Required offset from the source slide. Use 1, 2, or 3 "
                             "for ideate's first, second, or third alternative.")
    parser.add_argument(
        "--content-mode",
        choices=("strict", "broad"),
        default="strict",
        help=(
            "strict requires every source figure on the built slide or in notes; "
            "broad permits clean supporting-figure omissions but still rejects "
            "altered, substituted, or reformatted figures."
        ),
    )
    parser.add_argument("--allow-reformat", action="store_true",
                        help="Downgrade a reformatted source figure (e.g. "
                             "'2,300,000' for '2.3M') from an error to a warning. "
                             "Use only when the user asked for the new formatting.")
    args = parser.parse_args()

    if not os.path.isabs(args.deck):
        fail("--deck must be an absolute path, got: %s" % args.deck)
    if not os.path.isfile(args.deck):
        fail("Deck not found: %s" % args.deck)
    if not 1 <= args.expected_offset <= 3:
        fail("--expected-offset must be 1, 2, or 3, got: %d"
             % args.expected_offset)

    try:
        from pptx import Presentation
    except ImportError:
        fail("The container's required python-pptx runtime is unavailable. "
             "Do not install packages at runtime; verify the checks manually "
             "and report the missing dependency.")

    built_no = args.built

    try:
        prs = Presentation(args.deck)
    except Exception as exc:  # noqa: BLE001 - any read failure means "cannot run"
        fail("Could not open %s as a PowerPoint file (%s: %s). Verify the required "
             "checks manually." % (args.deck, exc.__class__.__name__, exc))

    slides = prs.slides
    for label, number in (("--source", args.source), ("--built", built_no)):
        if not 1 <= number <= len(slides):
            fail("%s=%d is out of range; deck has %d slides."
                 % (label, number, len(slides)))
    if built_no == args.source:
        fail("--built and --source are the same slide (%d); nothing to compare."
             % args.source)

    source = slides[args.source - 1]
    built = slides[built_no - 1]

    errors, warnings, checks = [], [], {}
    unreadable, src_pictures, built_pictures = [], [], []

    src_footer = footer_signature(source, prs)
    built_footer = footer_signature(built, prs)
    src_text = slide_text(
        source, unreadable, src_pictures, src_footer["shape_ids"]
    )
    built_text = slide_text(
        built, unreadable, built_pictures, built_footer["shape_ids"]
    )

    # 0. chart_data_readable ----------------------------------------------------
    # A source slide whose charts cannot be parsed would otherwise yield no numbers
    # and "pass" without checking anything. Refuse to do that.
    checks["chart_data_readable"] = not unreadable
    if unreadable:
        errors.append(
            "Chart data could not be read from %s. Numbers inside it were NOT "
            "checked — verify them by hand before handing the slide over."
            % ", ".join(unreadable))

    # 0b. footer continuity -----------------------------------------------------
    checks["footer_text_matches_source"] = (
        src_footer["entries"] == built_footer["entries"]
    )
    if not checks["footer_text_matches_source"]:
        errors.append(
            "Footer text differs from the source (source: %s; built: %s). "
            "Preserve the source footer, classification marking and date text."
            % (src_footer["text"] or "none", built_footer["text"] or "none")
        )

    checks["slide_number_presence_matches_source"] = (
        src_footer["slide_number_present"]
        == built_footer["slide_number_present"]
    )
    if not checks["slide_number_presence_matches_source"]:
        errors.append(
            "Built slide slide-number presence does not match the source "
            "(source: %s; built: %s). Preserve the source slide-number "
            "placeholder or field."
            % (
                src_footer["slide_number_present"],
                built_footer["slide_number_present"],
            )
        )

    # 1. numbers_exact ----------------------------------------------------------
    # Slide and notes are pooled separately on purpose. Cutting a figure down into
    # the notes is legitimate (the skill trims detail that way), but a HERO figure
    # rewritten on the face of the slide while the original still sits in the notes
    # must not pass -- pooling them together is exactly how that used to slip by.
    built_notes = notes_text(built)
    on_slide = extract_numbers(built_text)
    in_notes = extract_numbers(built_notes)
    built_pool = on_slide + in_notes
    slide_tokens = {n["token"] for n in on_slide}
    notes_tokens = {n["token"] for n in in_notes}

    src_numbers = extract_numbers(src_text)
    src_tokens = {n["token"] for n in src_numbers}

    def near_misses(num):
        """On-slide figures close to num that aren't themselves source figures.

        Excluding source tokens matters: on a slide reading "Revenue 100, target
        105", the 105 must not be mistaken for a corrupted 100.
        """
        return [b["raw"] for b in on_slide
                if b["token"] not in src_tokens and num["value"]
                and abs(b["value"] - num["value"]) <= 0.1 * abs(num["value"])]

    missing, reformatted, suspect = [], [], []
    for num in src_numbers:
        if num["token"] in slide_tokens:
            continue
        # Same value AND same semantic signature, but written differently = the
        # number was re-rendered. Checked before the notes branch so a reformatted
        # hero is reported as a reformat (which --allow-reformat can bless) rather
        # than as an alteration. Same-token matches are excluded: those are the
        # figure itself, trimmed into the notes, which the branch below handles.
        rewrites = [b["raw"] for b in built_pool
                    if b["token"] != num["token"]
                    and b["sig"] == num["sig"]
                    and abs(b["value"] - num["value"]) < 1e-9]
        if rewrites:
            reformatted.append((num["raw"], rewrites))
            continue
        if num["token"] in notes_tokens:
            # Trimmed into the notes, which the skill allows. Alarming only if
            # something close to it - and not itself a source figure - is now
            # showing on the face of the slide.
            near = near_misses(num)
            if near:
                suspect.append((num["raw"], near))
            continue
        missing.append({"raw": num["raw"], "possible_alteration": near_misses(num)})

    allowed_omissions = []
    hard_missing = []
    for item in missing:
        if args.content_mode == "broad" and not item["possible_alteration"]:
            allowed_omissions.append(item["raw"])
            warnings.append(
                "Source figure %s was intentionally omitted in broad content "
                "mode. Name the omission in the handoff." % item["raw"]
            )
        else:
            hard_missing.append(item)

    checks["numbers_exact"] = not (hard_missing or reformatted or suspect)
    for item in hard_missing:
        if item["possible_alteration"]:
            errors.append(
                "Source figure %s is missing from the built slide and its notes; "
                "nearby value(s) %s suggest it was ALTERED. Restore the exact "
                "source figure."
                % (item["raw"], ", ".join(item["possible_alteration"])))
        else:
            errors.append(
                "Source figure %s appears on neither the built slide nor its "
                "notes. Cut detail belongs in the notes, not deleted — restore it "
                "to the slide or its notes." % item["raw"])
    for raw, near in suspect:
        errors.append(
            "Source figure %s survives only in the speaker notes while %s is shown "
            "on the slide itself. That reads as an ALTERED headline figure — put "
            "the source's number back on the face of the slide."
            % (raw, ", ".join(near)))
    for raw, equivalent in reformatted:
        message = (
            "Source figure %s was REFORMATTED as %s. The value matches but the "
            "audience reads something different." % (raw, ", ".join(equivalent)))
        if args.allow_reformat:
            warnings.append(message + " Allowed via --allow-reformat.")
        else:
            errors.append(
                message + " Restore the source's formatting, or re-run with "
                "--allow-reformat if the user asked for the change.")
    if args.allow_reformat and reformatted:
        checks["numbers_exact"] = not (hard_missing or suspect)
    if src_pictures or built_pictures:
        warnings.append(
            "Picture shape(s) present (source: %s; built: %s). Numbers baked into "
            "an image cannot be read — check those by eye."
            % (src_pictures or "none", built_pictures or "none"))

    # 2. placeholders -----------------------------------------------------------
    # Notes are searched too: a placeholder hidden in the speaker notes is exactly
    # the one that gets read aloud by accident.
    found_placeholders = PLACEHOLDER_RE.findall(built_text + "\n" + built_notes)
    checks["no_placeholders"] = not found_placeholders
    if found_placeholders:
        warnings.append(
            "Unresolved placeholder(s): %s. Not a defect, but name them explicitly "
            "in your handoff so they are never presented as real figures."
            % ", ".join(found_placeholders))

    # 3. position ---------------------------------------------------------------
    expected_position = args.source + args.expected_offset
    checks["position_matches_expected_offset"] = built_no == expected_position
    if built_no != expected_position:
        errors.append(
            "Built slide is at position %d; expected source+%d (%d). Move it."
            % (built_no, args.expected_offset, expected_position))

    # 4. theme ------------------------------------------------------------------
    accent = find_accent_line(built)
    checks["no_accent_line_under_title"] = accent is None
    if accent is not None:
        errors.append(
            "A thin rule sits just under the title (shape id %s) — an AI-slop tell. "
            "Remove it; use whitespace or a color block." % accent)

    deck_fonts = theme_fonts(prs)
    generated_start = args.source + 1
    generated_end = args.source + 3
    for slide_no, slide in enumerate(slides, start=1):
        if not generated_start <= slide_no <= generated_end:
            deck_fonts |= slide_fonts(slide)
    off_theme = sorted(slide_fonts(built) - deck_fonts)
    checks["fonts_match_deck"] = not off_theme
    if off_theme:
        errors.append(
            "Font(s) used nowhere else in the deck: %s. Match the deck's theme."
            % ", ".join(off_theme))

    deck_effects = set()
    for slide_no, slide in enumerate(slides, start=1):
        if not generated_start <= slide_no <= generated_end:
            deck_effects |= slide_effect_types(slide)
    novel_effects = sorted(slide_effect_types(built) - deck_effects)
    checks["effects_match_deck"] = not novel_effects
    if novel_effects:
        errors.append(
            "Visual effect type(s) used nowhere else in the deck: %s. Match the "
            "source deck's treatment; a flat deck must stay flat."
            % ", ".join(novel_effects))

    built_title = title_text(built)
    checks["title_present"] = bool(built_title)
    if not checks["title_present"]:
        errors.append("Built slide has no title in its title placeholder.")

    ok = not errors
    if ok:
        print("REIMAGINE_THIS_SLIDE_VERIFY_OK=1")
    else:
        print(
            "REIMAGINE_THIS_SLIDE_VERIFY_ERR_REASON=%s" % errors[0].replace("\n", " "),
            file=sys.stderr,
        )
    print(json.dumps({
        "ok": ok,
        "deck": args.deck,
        "source_slide": args.source,
        "built_slide": built_no,
        "content_mode": args.content_mode,
        "allowed_omissions": allowed_omissions,
        "checks": checks,
        "not_checked": [
            "source slide unmodified (needs a pre-build baseline)",
            "theme colors (only fonts are compared)",
            "numbers inside pictures or SmartArt",
            "most chart number formats (only explicit percentage data labels are rendered)",
        ],
        "source_footer_text": src_footer["text"],
        "built_footer_text": built_footer["text"],
        "source_slide_number_present": src_footer["slide_number_present"],
        "built_slide_number_present": built_footer["slide_number_present"],
        "source_numbers": [n["raw"] for n in src_numbers],
        "errors": errors,
        "warnings": warnings,
    }, indent=2))
    if ok:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
