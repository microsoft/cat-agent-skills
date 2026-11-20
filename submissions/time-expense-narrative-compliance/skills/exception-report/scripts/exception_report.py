#!/usr/bin/env python3
"""exception_report - deterministic DRAFT pre-bill exception packet (step 5 of 5).

Reads governed.json from guideline_check and writes a Markdown review packet for the
engagement manager and billing coordinator. It only writes a local draft file: it has no
e-mail, chat or network code and never sends, submits, approves or alters WIP balances.
Engine flags are quoted verbatim; nothing is dropped or softened.

v1.0.6: governed data that holds rows outside the recorded timekeeper scope is refused
(client-billing-guidelines.md #12.1). Every data-derived cell (person, subject, narrative,
flag detail, exclusion reason, engagement names) passes the shared embedded-instruction
tripwire; flagged text is replaced by a withheld marker and never printed (#11.2). The engagement
header fields are screened together as one record, so an instruction split across them is withheld.
A recorded team view must be confirmed by the raw engagement letter and exports (--raw-dir, default raw/
next to --activity) or the data is refused; with --raw-dir, and always for a team view, the activity packet
must equal activity_pull re-run on those exports. Before writing, the rendered report is screened by table
column, by row, by run of bullet lines, in reading order within and across every row, bullet and section
boundary, IDs and citations included, and down the whole report as one sequence of lines (runs of up to 8
consecutive lines and the whole sequence, across sections, punctuation-only filler skipped); a hit adds a hold
notice. The report is then screened as a whole (a hit, or a report too long to screen, is refused). Only the
exact engine lines in FIXED_LINES and TABLE_HEADS, which hold no data, are skipped.

Governed data is never taken on trust (client-billing-guidelines.md #13.8): before rendering, the
engine re-runs narrative-draft, code-map and guideline-check on the activity packet (--activity) and
refuses a governed packet that differs from the result in any engine-owned field or section, provenance
included (entries, verdicts, flags, missing time, summary, exclusion records): no packet is written and
the message names no value, field or path. It then re-runs the guideline rules under the report's own
signal policy and refuses a narrower report-time policy that changes a line item or exclusion (#13.2).
A reject never renders as compliant. Summary figures are derived from the line items, excluded signal IDs
from provenance.excluded_signals, and every printed flag detail and citation from the re-run (a supplied
detail is never printed). An exclusion reason is printed only when it is the signal policy's own wording.

Engagement identity (#13.3): the governed header must equal provenance.engagement_identity, which
activity_pull recorded from the engagement letter, or the data is refused. Signals and time entries scoped
to another engagement are counted, never named or quoted.
"""
import datetime
import os
import re
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import billing_rules  # noqa: E402  (shared rules, identical copies next to code_map.py and guideline_check.py)
import signal_policy  # noqa: E402  (shared copy shipped next to each engine)

ENGINE = "engine:exception_report"
ENGINE_VERSION = "exception_report/1.0.13"
CONTRACT = "ps.time-expense-narrative-compliance.v1"
HEADER_KEYS = ("client_name", "matter_name", "engagement_id")


class InputError(ValueError):
    pass


def generated_at(override):
    if override:
        if not signal_policy.contract_check.valid_timestamp(override):
            raise InputError(f"--generated-at must be an ISO-8601 timestamp with seconds and an offset (for example 2026-09-23T00:00:00Z), got a string of {len(override)} character(s)")
        return override
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_governed(path):
    payload = signal_policy.read_json(path, InputError, "governed input")
    if not isinstance(payload, dict) or payload.get("contract_version") != CONTRACT:
        raise InputError(f"expected a {CONTRACT} object")
    signal_policy.validate_packet(payload, "governed")
    return payload


def cell(text):
    text = str(text if text is not None else "")
    return signal_policy.redact(text).replace("|", "\\|").replace("\n", " ")


def bound(value):
    """A period bound for display: a null bound is an open period, never a blank or 'None'."""
    return cell(value) if value else "open"


def cells(values):
    """Join a list of data-derived values, each passed through cell(); a non-list is treated as one value."""
    if values is None:
        return ""
    return ", ".join(cell(v) for v in (values if isinstance(values, list) else [values]))


CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
BULLET_SPLIT_RE = re.compile(r": |, | \(|\)|\[|\]|<br>")
RENDERED_HOLD = ("- **Rendered text withheld:** {n} table cell(s) or line(s) read as an instruction only together with "
                 "the neighbouring rows, cells or lines they are printed with; withheld and never followed - check the "
                 "source records (client-billing-guidelines.md #11.1, #11.2)")
# D22: the only report lines the rendered-order screen skips are these exact engine strings, which carry no data. Every
# other line - a table row, a bullet, the engagement header, or any line a later template adds - is data and is
# screened (an unknown heading or table header is screened like data, never exempted). The test-data
# tests/run_tests.py checks every report the suite renders against this list.
FIXED_LINES = frozenset({
    "", "# DRAFT - not sent, not approved", "None.",
    "## Summary", "## Rejects - rewrite or remove before pre-bill", "## Held for review", "## Needs review",
    "## Missing time", "## Privacy exclusions", "## Compliant drafts", "## Next steps (human decisions)",
})
TABLE_HEADS = frozenset({
    "| Entry | Person | Date | Hours | Engine flags (verbatim) |", "| Entry | Person | Date | Hours | Flag (verbatim) |",
    "| Activity | Person | Date | Hours | Subject | Citations |",
})
TABLE_RULE_RE = re.compile(r"\|(?:---\|)+")
HEADER_PREFIX = "**Pre-bill exception packet** - "


def _row_cells(line):
    """A Markdown table row's cells (cell() escapes every | inside data, so only unescaped | separate cells)."""
    return [c.strip() for c in CELL_SPLIT_RE.split(line)[1:-1]]


def rendered_blocks(lines):
    """Every line of the report, in order, as (kind, start, end): "fixed" (one exact FIXED_LINES or table header/rule
    line, no data), "table" (the data rows under a TABLE_HEADS header and its rule), "bullets" (a run of "- " lines) or
    "line" (any other line: data, screened on its own and in reading order)."""
    blocks, n = [], 0
    while n < len(lines):
        line = lines[n]
        if line in TABLE_HEADS and n + 1 < len(lines) and TABLE_RULE_RE.fullmatch(lines[n + 1]):
            blocks.append(("fixed", n, n + 2))
            end = n + 2
            while end < len(lines) and lines[end].startswith("|"):
                end += 1
            if end > n + 2:
                blocks.append(("table", n + 2, end))
            n = end
        elif line.startswith("- "):
            end = n
            while end < len(lines) and lines[end].startswith("- "):
                end += 1
            blocks.append(("bullets", n, end))
            n = end
        else:
            blocks.append(("fixed" if line in FIXED_LINES else "line", n, n + 1))
            n += 1
    return blocks


def _parts(text):
    return [p.strip() for p in BULLET_SPLIT_RE.split(text)]


def _reading_order(units):
    """D22: the values of a table or bullet run in the order they are read (row by row, cell by cell, each cell's
    and bullet's comma, colon, bracket and <br> parts in turn). Runs inside one row or bullet are its own screens
    above; every run that crosses a row or bullet boundary (one row's last citation and the next row's ID) is
    screened joined here. units is one [(owner, text)] list per row or bullet; returns the owners to withhold."""
    return signal_policy.crossing_runs([[(owner, part) for owner, text in unit for part in _parts(text)]
                                        for unit in units])


def _block_values(lines, kind, start, end):
    """One block's values in reading order, each owned by (line, cell) - cell None for a bullet or line."""
    if kind == "table":
        return [((i, c), part) for i in range(start, end) for c, text in enumerate(_row_cells(lines[i]))
                for part in _parts(text)]
    return [((i, None), part) for i in range(start, end)
            for part in _parts(lines[i][2:] if kind == "bullets" else _line_data(lines[i]))]


def _line_data(line):
    """A data line's values without the engine's header label ("client / matter (ID)" for the header line)."""
    return line[len(HEADER_PREFIX):].replace(" / ", ", ") if line.startswith(HEADER_PREFIX) else line


def _withhold(out, owners):
    """Replace each owned cell, bullet or line with the withheld marker, keeping a bullet's "- " and the header line's
    engine label; returns how many were replaced."""
    count = 0
    for i in sorted({i for i, _ in owners}):
        cols = {c for j, c in owners if j == i}
        if out[i].startswith("|") and None not in cols:
            row = _row_cells(out[i])
            hit = [c for c in sorted(cols) if c < len(row) and row[c] != signal_policy.WITHHELD_TEXT]
            for c in hit:
                row[c] = signal_policy.WITHHELD_TEXT
            if hit:
                out[i] = "| " + " | ".join(row) + " |"
            count += len(hit)
        else:
            prefix = "- " if out[i].startswith("- ") else HEADER_PREFIX if out[i].startswith(HEADER_PREFIX) else ""
            if out[i] != prefix + signal_policy.WITHHELD_TEXT:
                out[i] = prefix + signal_policy.WITHHELD_TEXT
                count += 1
    return count


DOC_POSITIONS = 2  # the whole-report line pass reads this many data values from each end of every line


def _data_lines(lines):
    """D18 / D22, the whole report as a sequence of lines: every data line in document order, across section headings
    and block boundaries, as (block number, its data values [(owner, value)]) - fixed-grammar values (FIXED_VALUE_RE),
    withheld markers (and their parts) and punctuation-only filler dropped. A line with no data value left (a "- ." or
    "| - |" filler line, or one already withheld) is skipped, so filler never separates or dilutes the lines around
    it."""
    marker = {signal_policy.WITHHELD_TEXT, *_parts(signal_policy.WITHHELD_TEXT)}
    data = []
    for block, (kind, start, end) in enumerate(rendered_blocks(lines)):
        if kind == "fixed":
            continue
        for i in range(start, end):
            row = [v for v in _block_values(lines, kind, i, i + 1)
                   if signal_policy.has_data(v[1]) and v[1] not in marker
                   and not signal_policy.FIXED_VALUE_RE.fullmatch(v[1].strip())]
            if row:
                data.append((block, row))
    return data


def _project(rows, pick):
    """The value at position pick (from the start when >= 0, from the end when < 0) of each row; None when too short."""
    return tuple(row[pick] if -len(row) <= pick < len(row) else None for row in rows)


def _document_runs(lines):
    """Owners to withhold from the whole-report line pass (D18 / D22). The report is read as one sequence of data lines
    (_data_lines): the value at each of the first and last DOC_POSITIONS positions of every line - an ID, person,
    subject or narrative, wherever its section puts it - is read down the whole report, every run of 2 to RUN_WINDOW
    consecutive lines and then the whole sequence (signal_policy._tripping_seq). Because a section's line shape can put
    the next part of a split in another position (one table's subjects, then a bullet's ID), every run of up to
    RUN_WINDOW lines that crosses a block boundary is also read with each pair of those positions, one on each side
    (each distinct run screened once). Last, every data value of the report is read joined in order: when only that
    whole sequence trips, every data line is withheld. Runs of consecutive values in reading order are
    signal_policy.crossing_runs."""
    data = _data_lines(lines)
    rows = [row for _, row in data]
    bad = set()
    picks = [k for k in range(DOC_POSITIONS)] + [-1 - k for k in range(DOC_POSITIONS)]
    for pick in picks:
        seq = _project(rows, pick)
        bad.update(seq[i][0] for i in signal_policy._tripping_seq([v[1] if v else None for v in seq]))
    groups = []
    for block, row in data:
        if not groups or groups[-1][0] != block:
            groups.append((block, []))
        groups[-1][1].append(row)
    width, seen = signal_policy.RUN_WINDOW, set()
    for (_, left), (_, right) in zip(groups, groups[1:]):
        left, right = left[-(width - 1):], right[:width - 1]
        for head in {_project(left, pick) for pick in picks}:
            for tail in {_project(right, pick) for pick in picks}:
                seq = head + tail
                live = [i for i, v in enumerate(seq) if v]
                for size in range(2, min(width, len(live)) + 1):
                    for n in range(len(live) - size + 1):
                        run = live[n:n + size]
                        key = tuple(seq[i] for i in run)
                        owners = {owner for owner, _ in key}
                        if run[0] >= len(head) or run[-1] < len(head) or key in seen or bad.intersection(owners):
                            continue
                        seen.add(key)
                        if signal_policy._scan_record({str(k): seq[i][1] for k, i in enumerate(run)}):
                            bad.update(owners)
    values = [v for row in rows for v in row]
    if not bad and len(rows) > 2 and signal_policy._scan_record({str(k): v for k, (_, v) in enumerate(values)}):
        bad = {owner for owner, _ in values}
    return bad


def screen_rendered(lines):
    """#11.1 / #11.2 on the report as printed: every cell is screened alone by cell(), but text split across cells or
    lines that end up side by side is screened joined here - each table column (the same cell of neighbouring rows),
    each table row, each run of bullet lines (whole, and part by part), each other data line, and every value of the
    report in reading order, citations, IDs and row references included (D22): within each table and bullet run, then
    across every block boundary (a header line, a bullet run and the next table, read past the engine's fixed
    headings) - and then the whole report as one sequence of data lines (_document_runs: sliding windows of 2 to
    RUN_WINDOW consecutive lines and the whole sequence, across sections, punctuation-only filler skipped). Every
    cell, bullet or line in a run that trips is withheld. Returns (lines, number withheld). Only the exact FIXED_LINES
    and TABLE_HEADS strings, which hold no data, are skipped (rendered_blocks). A report too long to screen is
    returned unscreened: main() then refuses it as oversize (the detector's own oversize hold)."""
    out = list(lines)
    withheld = 0
    if sum(len(line) + 1 for line in out) > signal_policy.steering_guard.MAX_TOTAL_CHARS:
        return out, 0
    for kind, start, end in rendered_blocks(out):
        if kind == "table":
            rows = [_row_cells(line) for line in out[start:end]]
            bad = set()
            for col in range(max((len(r) for r in rows), default=0)):
                column = [r[col] if col < len(r) else None for r in rows]
                bad |= {(i, col) for i in signal_policy._tripping_seq(column)}
            for i, row in enumerate(rows):
                bad |= {(i, int(k)) for k in signal_policy._tripping_fields({str(c): t for c, t in enumerate(row) if t})}
            bad |= _reading_order([[((i, col), t) for col, t in enumerate(row)] for i, row in enumerate(rows)])
            withheld += _withhold(out, {(start + i, col) for i, col in bad})
        elif kind == "bullets":
            items = [line[2:] for line in out[start:end]]
            bad = set(signal_policy._tripping_seq(items))
            # A bullet's fixed wording (ID, person, date, hours) would dilute text split across two bullets, so the
            # parts in the same position - counted from the start and from the end - are screened like a column.
            parts = [[p for p in _parts(item) if p] for item in items]
            width = max((len(p) for p in parts), default=0)
            for k in range(width):
                bad.update(signal_policy._tripping_seq([p[k] if k < len(p) else None for p in parts]))
                bad.update(signal_policy._tripping_seq([p[-1 - k] if k < len(p) else None for p in parts]))
            bad |= _reading_order([[(i, item)] for i, item in enumerate(items)])
            withheld += _withhold(out, {(start + i, None) for i in bad})
        elif kind == "line" and _line_data(out[start]) != signal_policy.WITHHELD_TEXT:
            text = _line_data(out[start])
            parts = {str(k): p for k, p in enumerate(_parts(text)) if p}
            if signal_policy.screen(text) or signal_policy._tripping_fields(parts):
                withheld += _withhold(out, {(start, None)})
    # Reading order across blocks: the last values of one block and the first of the next are read together.
    units = [_block_values(out, kind, start, end) for kind, start, end in rendered_blocks(out) if kind != "fixed"]
    withheld += _withhold(out, signal_policy.crossing_runs(units))
    withheld += _withhold(out, _document_runs(out))
    return out, withheld


def flag_lines(flags):
    return "<br>".join(f"`{cell(f.get('flag'))}` ({cell(f.get('severity'))}): {cell(f.get('detail'))} [{cells(f.get('citations', []))}]"
                       for f in flags if isinstance(f, dict))


def main():
    ap = signal_policy.ArgumentParser(description="Write a DRAFT pre-bill exception packet (Markdown). Sends nothing.")
    ap.add_argument("--governed", required=True, help="governed.json from guideline_check")
    ap.add_argument("--activity", required=True, help="The activity packet the governed packet was derived from (activity_pull's output); "
                    "the governed packet must equal its re-derivation from it (client-billing-guidelines.md #13.8)")
    ap.add_argument("--out", required=True, help="Output Markdown draft")
    ap.add_argument("--raw-dir", help=signal_policy.RAW_DIR_HELP)
    ap.add_argument("--requested-start", help="Period the user asked about (YYYY-MM-DD)")
    ap.add_argument("--requested-end", help="Period the user asked about (YYYY-MM-DD)")
    ap.add_argument("--signal-config", help="Additional signal policy JSON; it can only narrow the plugin's config/signal-sources.json, which is always applied (most restrictive wins)")
    ap.add_argument("--generated-at", help="Fixed ISO-8601 UTC timestamp for reproducible golden files")
    args = ap.parse_args()

    try:
        stamp = generated_at(args.generated_at)
        signal_policy.check_date(args.requested_start, "--requested-start", null=True)
        signal_policy.check_date(args.requested_end, "--requested-end", null=True)
        if args.requested_start and args.requested_end and args.requested_start > args.requested_end:
            raise InputError("--requested-start is after --requested-end")
        data = deepcopy(load_governed(args.governed))
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # A team view the activity packet records is honoured only once the raw exports confirm it (#12.1), and with
        # --raw-dir or a team view the activity packet must equal activity_pull re-run on them (#13.8).
        activity = signal_policy.load_activity_root(args.activity, InputError, raw_dir=args.raw_dir)
        # #13.8: the whole governed packet, provenance included, must equal narrative-draft, code-map and
        # guideline-check re-run on the activity packet before anything is reconciled or rendered.
        billing_rules.check_rederived(data, activity, "governed", script_dir)
        signal_policy.enforce_timekeeper_scope(data, engine=ENGINE, strict=True)
        # The report's effective signal policy is applied inside the re-run, before anything is compared or
        # rendered, so filtering, govern() and rendering all use the same configuration.
        problems, rerun = billing_rules.reconcile_governed(data, script_dir=script_dir, engine=ENGINE,
                                                           config_path=args.signal_config)
        if problems:
            raise InputError(
                f"governed data does not match a re-run of the guideline-check rules ({billing_rules.RECONCILE_CITATION}): "
                + "; ".join(problems[:6]) + (f"; and {len(problems) - 6} more" if len(problems) > 6 else "")
                + (". No packet was written; re-run narrative_draft.py, code_map.py and guideline_check.py with the "
                   "same --signal-config" if args.signal_config else
                   ". No packet was written; re-run guideline_check.py on the coded data"))
        signal_policy.filter_packet(data, config_path=args.signal_config,
                                    script_dir=script_dir, engine=ENGINE)
    except (InputError, signal_policy.PolicyError) as exc:
        sys.exit(f"exception_report: {signal_policy.error_text(exc)}")

    # Only re-derived flag detail and citations are printed; supplied detail text never is (#13.2).
    for entry, want in zip(data["time_entries"], rerun["time_entries"]):
        entry["compliance"]["flags"] = billing_rules.rendered_flags(entry["compliance"].get("flags"),
                                                                    want["compliance"]["flags"])
    eng = data.get("engagement", {})
    # The header fields are one record: an instruction split across client and matter name is withheld.
    header = {k: eng.get(k) for k in HEADER_KEYS if isinstance(eng.get(k), str)}
    header_hits = signal_policy.screen_record(header, pair_keys=HEADER_KEYS)
    header_withheld = bool(header_hits) or signal_policy.WITHHELD_TEXT in header.values()
    if header_withheld:
        eng = {k: signal_policy.WITHHELD_TEXT for k in HEADER_KEYS}
    packet_hold = signal_policy.packet_held(data)
    period = data.get("period") or {}
    figures = billing_rules.summary_figures(data["time_entries"], data["missing_time_report"])
    other_ids = {signal_policy._id_key(x) for x in signal_policy.other_engagement_ids(data)}
    other_entries = len(data.get("provenance", {}).get("excluded_entries", []))
    other_note = (f"{len(other_ids)} activity signal(s) and {other_entries} time entr(ies) scoped to another engagement "
                  f"were excluded and are not shown ({signal_policy.POLICY_CITATION}; {signal_policy.ENGAGEMENT_CITATION})"
                  if other_ids or other_entries else "")
    data_dates = sorted({d for d in [e.get("date") for e in data["time_entries"]]
                         + [s.get("date") for s in data.get("activity_signals", [])] if isinstance(d, str) and d})
    actual = (data_dates[0], data_dates[-1]) if data_dates else (None, None)
    by_verdict = {}
    by_flag_severity = {}
    for entry in data["time_entries"]:
        compliance = entry.get("compliance", {})
        verdict = compliance.get("verdict")
        if verdict not in signal_policy.VERDICTS:
            verdict = "hold_for_review"  # unrecognised verdicts fail closed (validate_packet rejects them first)
        if verdict == "compliant" and (compliance.get("flags")
                                       or signal_policy.embedded_instruction(entry.get("draft", {}).get("narrative"))):
            verdict = "needs_review"  # a flagged entry is never listed as a compliant draft
        if packet_hold and signal_policy.SEVERITY_RANK[verdict] < signal_policy.SEVERITY_RANK["hold_for_review"]:
            verdict = "hold_for_review"  # a metadata hold governs every entry (#11.3); reconcile refuses it first
        by_verdict.setdefault(verdict, []).append(entry)
        for flag in compliance.get("flags", []):
            severity = flag.get("severity") if flag.get("severity") in signal_policy.SEVERITIES else "hold_for_review"
            by_flag_severity.setdefault(severity, []).append((entry, flag))

    lines = [
        "# DRAFT - not sent, not approved",
        "",
        f"**Pre-bill exception packet** - {cell(eng.get('client_name'))} / {cell(eng.get('matter_name'))} "
        f"({cell(eng.get('engagement_id'))})",
        "",
        f"- Prepared for: engagement manager and billing coordinator (review only)",
    ]
    if header_withheld:
        lines.append("- **Engagement names withheld:** " + signal_policy.hold_reason(
            header_hits, "the client, matter and engagement fields read together as an instruction")
            + "; check the engagement record (client-billing-guidelines.md #11.1, #11.2)")
    if packet_hold:
        lines.append(f"- **Metadata withheld:** {signal_policy.PACKET_HOLD_REASON}; every entry is held for review "
                     f"({signal_policy.METADATA_CITATION})")
    lines += [
        f"- Period covered by the governed data: {bound(period.get('start'))} to {bound(period.get('end'))} "
        + (f"(entries and activity actually dated {cell(actual[0])} to {cell(actual[1])})" if data_dates
           else "(no dated entries or activity)"),
    ]
    if args.requested_start or args.requested_end:
        req = (args.requested_start or period.get("start") or actual[0], args.requested_end or period.get("end") or actual[1])
        declared = (period.get("start"), period.get("end"))
        beyond_declared = bool(declared[0] and declared[1]) and (req[0] < declared[0] or req[1] > declared[1])
        beyond_data = not data_dates or req[0] < actual[0] or req[1] > actual[1]
        narrower = bool(data_dates) and (actual[0] < req[0] or actual[1] > req[1])
        if beyond_declared or beyond_data:
            lines.append(f"- **Period caveat:** you asked about {bound(req[0])} to {bound(req[1])}, but the governed data "
                         + (f"contains entries and activity dated only {actual[0]} to {actual[1]}" if data_dates
                            else "contains no dated entries or activity")
                         + ". Time outside those dates has not been "
                         "checked; re-run the chain for the requested period, or confirm no other time exists, before relying on this packet.")
        elif narrower:
            lines.append(f"- **Period caveat:** you asked about {req[0]} to {req[1]}, but this packet also covers entries and "
                         f"activity dated {actual[0]} to {actual[1]}. Re-run the chain for the requested period for a packet limited to it.")
        else:
            lines.append("- Requested period matches the governed data.")
    if not data["time_entries"] and not data.get("activity_signals"):
        # Missing is not empty (Mobilization QA round 20): a packet with nothing in scope is never presented as clean.
        lines.append("- **No data:** the governed data holds no time entries and no activity signals in scope. An empty "
                     "packet is not evidence that no work was done; confirm the period, the timekeeper and the exports, "
                     "then re-run the chain before relying on it.")
    policy_excluded = cells([x for x in billing_rules.excluded_ids(data) if signal_policy._id_key(x) not in other_ids])
    lines += [
        f"- Generated: {stamp} by {ENGINE_VERSION} from guideline_check output (flags quoted verbatim)",
        "",
        "## Summary",
        "",
        f"- Entries: {figures['total_entries']} ({figures['total_hours']} h)",
        "- Verdicts: " + (", ".join(f"{cell(k)} {cell(v)}" for k, v in sorted(figures["verdict_counts"].items()))
                          or "none (no time entries)"),
        f"- Missing time: {figures['missing_time_hours']} h across {len(data['missing_time_report'])} activity signal(s)",
        f"- Excluded by signal policy: {policy_excluded} [{signal_policy.POLICY_CITATION}]" if policy_excluded
        else "- Excluded by signal policy: none",
    ]
    if other_note:
        lines.append(f"- Other engagements: {other_note}")
    lines += [
        "",
    ]
    sections = (("hold_for_review", "Held for review"),
                ("needs_review", "Needs review"))
    reject_rows = by_verdict.get("reject", [])
    lines += ["## Rejects - rewrite or remove before pre-bill", ""]
    if not reject_rows:
        lines += ["None.", ""]
    else:
        lines += ["| Entry | Person | Date | Hours | Engine flags (verbatim) |", "|---|---|---|---|---|"]
        for e in reject_rows:
            lines.append(f"| {cell(e.get('entry_id'))} | {cell(e.get('person'))} | {cell(e.get('date'))} | {cell(e.get('duration_hours'))} | "
                         f"{flag_lines(e['compliance']['flags'])} |")
        lines.append("")
    listed_under = {id(e): "Rejects" for e in reject_rows}
    for severity, title in sections:
        own = by_verdict.get(severity, [])
        # An entry listed under a more severe status is cross-referenced here, not repeated (its row holds every flag).
        refs = {}
        for e, flag in by_flag_severity.get(severity, []):
            if id(e) in listed_under:
                refs.setdefault(id(e), (e, []))[1].append(flag)
        lines += [f"## {title}", ""]
        if not own and not refs:
            lines += ["None.", ""]
            continue
        if own:
            lines += ["| Entry | Person | Date | Hours | Engine flags (verbatim) |", "|---|---|---|---|---|"]
            for e in own:
                lines.append(f"| {cell(e.get('entry_id'))} | {cell(e.get('person'))} | {cell(e.get('date'))} | {cell(e.get('duration_hours'))} | "
                             f"{flag_lines(e.get('compliance', {}).get('flags', [])) or 'no engine flag; not compliant'} |")
            lines.append("")
        for e, flags in refs.values():
            names = ", ".join(f"`{cell(f.get('flag'))}`" for f in flags)
            lines.append(f"- {cell(e.get('entry_id'))} (listed under {listed_under[id(e)]}): also {cell(severity)} - {names}; "
                         f"see that row for the verbatim flags and citations.")
        if refs:
            lines.append("")
        for e in own:
            listed_under[id(e)] = title
    lines += ["## Missing time", ""]
    if data["missing_time_report"]:
        lines += ["| Activity | Person | Date | Hours | Subject | Citations |", "|---|---|---|---|---|---|"]
        for m in data["missing_time_report"]:
            # An item held for text split across neighbouring items may owe the split to its ID (D22): the ID is
            # withheld too; its raw-row citation still locates it.
            split = m.get("embedded_instruction") is True and billing_rules.SPLIT_MISSING_REASON in str(m.get("finding"))
            shown_id = signal_policy.WITHHELD_TEXT if split else m.get("activity_id")
            lines.append(f"| {cell(shown_id)} | {cell(m.get('person'))} | {cell(m.get('date'))} | {cell(m.get('duration_hours'))} | "
                         f"{cell(m.get('subject'))} | {cells(m.get('citations', []))} |")
    else:
        lines.append("None.")
    lines += ["", "## Privacy exclusions", ""]
    excluded = [x for x in data.get("provenance", {}).get("excluded_signals", [])
                if signal_policy._id_key(x.get("activity_id")) not in other_ids]
    # check_rederived has already matched every reason and citation to the engines' own wording (#13.8).
    for x in excluded:
        lines.append(f"- {cell(x.get('activity_id'))}: {cell(x.get('reason'))} [{cells(x.get('citations', []))}]")
    if other_note:
        lines.append(f"- {other_note}.")
    if not excluded and not other_note:
        lines.append("- None. Only enabled sources were used.")
    compliant = by_verdict.get("compliant", [])
    lines += ["", "## Compliant drafts", ""]
    lines += [f"- {cell(e.get('entry_id'))} ({cell(e.get('person'))}, {cell(e.get('date'))}, {cell(e.get('duration_hours'))} h): "
              f"{cell(e.get('draft', {}).get('narrative'))}" for e in compliant] or ["None."]
    lines += [
        "",
        "## Next steps (human decisions)",
        "",
        "- The billing coordinator or engagement manager decides every reject, hold and missing-time item (client-billing-guidelines.md #9.2).",
        "- Nothing has been sent, submitted, approved, recoded or used to alter WIP balances. To share this packet, the assistant prepares a draft message, "
        "shows the recipients and content, and waits for your explicit confirmation. It is never sent to the client.",
        "",
    ]
    lines, withheld = screen_rendered(lines)
    if withheld:
        lines.insert(5, RENDERED_HOLD.format(n=withheld))  # after the title, header and "Prepared for" lines
    text = "\n".join(lines)
    # The whole report, as written, is screened last: one that still trips (or is too long to screen) is not written.
    if signal_policy.screen(text):
        sys.exit("exception_report: the rendered packet reads as an instruction (or is too long to screen) as a whole "
                 "after its tripping cells and lines were withheld; no packet was written - check the source records "
                 "(client-billing-guidelines.md #11.1, #11.2)")
    try:
        signal_policy.write_output(args.out, text)  # encodes first, then temp file + os.replace
    except (OSError, UnicodeError) as exc:
        sys.exit(f"exception_report: cannot write output: {signal_policy.error_text(exc)}")
    print("exception_report: DRAFT exception packet written (not sent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
