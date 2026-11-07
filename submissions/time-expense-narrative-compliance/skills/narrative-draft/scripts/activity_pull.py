#!/usr/bin/env python3
"""activity_pull - deterministic raw-export -> activity packet converter (step 1 of 5).

Reads the engagement-scoped exports in a raw/ folder and writes a
ps.time-expense-narrative-compliance.v1 activity packet:

  raw/engagement-letter-extract.md   engagement identity (## Engagement key: value lines)
  raw/calendar-export.csv            calendar metadata (source key: calendar)
  raw/document-activity-log.csv      engagement-workspace document activity (document_activity)
  raw/engagement-workplan.csv        controlled workplan: activity class, deliverable, purpose
  raw/timesheet.csv                  existing time entries

Privacy (client-billing-guidelines.md #10.1): config/signal-sources.json is read FIRST. A source
that is disabled is never opened; timesheet links into a disabled or unknown source are removed
from evidence and recorded under provenance.excluded_signals with the policy citation.
Purpose is copied only from the controlled workplan; when none exists it stays null and the
signal is marked needs_review - it is never invented.

Data minimisation (client-billing-guidelines.md #12.1): only the requesting timekeeper's rows
are returned. Colleagues' rows (--person <other> or --all-timekeepers) are released only in the
engagement-manager team view: the --requester must be the engagement_manager recorded in
raw/engagement-letter-extract.md AND --team-view-confirmation must be exactly
"engagement-manager:<engagement_id>". Otherwise colleague rows are withheld (fail closed); a
malformed confirmation is an input error. The role is never inferred from free text. Every later
engine re-reads the same raw exports (--raw-dir, by default raw/ next to the activity packet) with
the same parsers (signal_policy.read_engagement / read_raw_csv) and honours a recorded team view
only when they confirm it; people: null then covers only the timekeepers the raw exports name.

Re-derivation (#12.1, #13.8): the whole derivation is pull(). Whenever a later engine is given
--raw-dir, and always when the packet records a team view, it imports this file (shipped as
identical copies next to every engine) and re-runs pull() on the raw exports with the packet's
recorded run parameters (rederive, RUN_PARAMETERS); an activity packet that differs from the
result in any field but provenance.generated_at is refused with no output.

Free text is data (#11.1): a signal or entry whose text trips the shared embedded-instruction
tripwire is marked embedded_instruction / needs_review so no later step drafts from it.
IDs are keys (#13.9): every ID and code cell, timesheet link and letter ID must be a bounded record ID
(contract_check.valid_record_id), checked as written; prose in an ID is refused, never echoed. No ID-bearing cell (IDs,
codes, match keys, file names, timekeeper names, letter fields) may take the engines' positional-label form (#13.10,
signal_policy.refuse_reserved), and every row's grammar is checked before its timekeeper, engagement or date can
exclude it, so an out-of-scope row is refused for a malformed cell, never skipped unread.
A requested period with no rows for the requester produces a period_check warning.

Engagement identity (#13.3): only rows whose engagement_id is the engagement letter's are read, and the
letter's engagement_id, client, matter and engagement manager are recorded once in
provenance.engagement_identity. Every later engine refuses a packet whose header differs from it.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signal_policy  # noqa: E402  (shared copy shipped next to each engine)

ENGINE = "engine:activity_pull"
ENGINE_VERSION = signal_policy.STAGE_VERSIONS["activity"]  # "activity_pull/1.0.13"; later stages require it (#13.8)
CONTRACT = "ps.time-expense-narrative-compliance.v1"
POLICY_CITATION = signal_policy.POLICY_CITATION
MATCHED_CONFIDENCE = signal_policy.MATCHED_CONFIDENCE  # shared: later stages re-derive it (#13.5)
UNMATCHED_CONFIDENCE = signal_policy.UNMATCHED_CONFIDENCE  # below the #9.1 floor -> held for review
TIMESHEET_CONFIDENCE = 0.97
NON_BILLABLE_CLASSES = signal_policy.NON_BILLABLE_CLASSES  # client-billing-guidelines.md #5.1
DOCUMENT_CLASS = {"analyze": "document_analysis", "research": "research", "draft": "deliverable_drafting"}
# Activity-ID namespaces used by connectors: lets a disabled source's links be recognised
# without opening the disabled export.
ID_NAMESPACE = (("-CAL-", "calendar"), ("-DOC-", "document_activity"), ("-MAIL-", "mailbox_metadata"))
SOURCE_FILES = (
    ("calendar", "calendar-export.csv", "connector:m365-calendar"),
    ("document_activity", "document-activity-log.csv", "connector:engagement-document-activity"),
    ("mailbox_metadata", "mailbox-summary.txt", "connector:mailbox-metadata"),
    ("mailbox_content", "mailbox-summary.txt", "connector:mailbox-content"),
)
PARSERS_AVAILABLE = ("calendar", "document_activity")
# The workplan item types the joins use (canonical form -> declared spelling); any other is refused (#8.4).
WORKPLAN_ITEM_TYPES = {signal_policy.canon_id(t): t for t in ("calendar_event", "document")}
NO_CONFIRMATION = "no engagement-manager team-view confirmation was supplied"
SELF_SCOPE_REASON = "colleagues' rows withheld: only the requester's rows were requested"


class InputError(ValueError):
    pass


def generated_at(override):
    if override:
        if not signal_policy.contract_check.valid_timestamp(override):
            raise InputError(f"--generated-at must be an ISO-8601 timestamp with seconds and an offset (for example 2026-09-23T00:00:00Z), got a string of {len(override)} character(s)")
        return override
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path, required):
    """One raw CSV export, read strictly by the parser the team-view check shares (signal_policy.read_raw_csv)."""
    return signal_policy.read_raw_csv(path, required, InputError)


DECIMAL_RE = re.compile(r"\d+(?:\.\d+)?")
TIME_RE = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


def cli_date(value, flag):
    if value is None:
        return None
    try:
        signal_policy.check_date(value, flag)
    except signal_policy.SchemaError as exc:
        raise InputError(str(exc)) from exc
    return value


def cell_date(row, key, cite):
    value = row[key].strip()
    try:
        signal_policy.check_date(value, f"{cite} {key}")
    except signal_policy.SchemaError as exc:
        raise InputError(str(exc)) from exc
    return value


def cell_hours(row, key, cite):
    """A plain non-negative decimal; 'nan', 'inf', '1e3', '-1' and '' are rejected, never coerced."""
    value = row[key].strip()
    if not DECIMAL_RE.fullmatch(value):
        raise InputError(f"{cite} {key} must be a non-negative decimal number of hours")
    return float(value)


def cell_id(row, key, cite):
    value = row[key].strip()
    # A21: a value that folds to nothing ("-", "_", a format character) is blank and never a key.
    if not signal_policy.canon_id(value):
        raise InputError(f"{cite} {key} must not be empty (or only separators or format characters)")
    return value


def record_id(value, cite, key, optional=False):
    """#13.9: a raw ID cell (or one activity_ids link) holds a record ID of the documented, bounded shape exactly as
    written - never prose, never padded. optional: a blank cell is no ID (None). The error cites the row, never the
    value."""
    if optional and not value.strip():
        return None
    if not signal_policy.canon_id(value):
        raise InputError(f"{cite} {key} must not be empty (or only separators or format characters)")
    if not signal_policy.contract_check.valid_record_id(value):
        raise InputError(f"{cite} {key} is not {signal_policy.contract_check.ID_RULE}")
    return value


def unreserved(value, cite, key):
    """#13.10 (T&E QA round 15): an ID-bearing cell (an ID, match key, file name or timekeeper name) never has the
    positional-label form the engines give another party's records, so a label can never name an in-scope record.
    signal_policy.refuse_reserved is the one check; the error cites the row only."""
    return signal_policy.refuse_reserved(value, f"{cite} {key}", InputError)


def unreserved_id(value, cite, key, optional=False):
    """#13.9 and #13.10: a record ID of the bounded shape (record_id) that is not in the positional-label form
    (calendar-export-row-4, other-engagement-signal-1). optional: a blank cell is no ID (None)."""
    value = record_id(value, cite, key, optional=optional)
    return value if value is None else unreserved(value, cite, key)


def unique(index, key, cite, what, value=None):
    """Record `key` in `index`; a repeat is malformed input (an index would silently keep only one row). The error
    cites both rows, never the value."""
    if key in index:
        first = index[key][0] if isinstance(index[key], tuple) else index[key]
        raise InputError(f"{cite} repeats the {what} of {first if isinstance(first, str) else 'row ' + str(first)}; "
                         "duplicate IDs are malformed, never silently merged")
    index[key] = value if value is not None else cite


def read_engagement(path):
    """The engagement letter, read by the parser every later engine re-reads it with (signal_policy.read_engagement)."""
    return signal_policy.read_engagement(path, InputError)


def hours_between(start, end, cite="calendar row"):
    start, end = start.strip(), end.strip()
    if not (TIME_RE.fullmatch(start) and TIME_RE.fullmatch(end)):
        raise InputError(f"{cite} start and end must be HH:MM (24-hour)")
    fmt = "%H:%M"
    delta = datetime.datetime.strptime(end, fmt) - datetime.datetime.strptime(start, fmt)
    if delta.total_seconds() < 0:
        raise InputError(f"{cite} ends before it starts")
    return round(delta.total_seconds() / 3600.0, 1)


def subject_from_file(name):
    stem = os.path.splitext(name)[0]
    return re.sub(r"[-_]+", " ", stem).strip()


def in_period(date, period):
    return (not period["start"] or date >= period["start"]) and (not period["end"] or date <= period["end"])


def resolve_scope(args, engagement):
    """Return (allowed person keys or None for everyone, timekeeper_scope record). Fails closed."""
    requester = " ".join((args.requester or "").split())
    if not signal_policy.person_key(requester):
        raise InputError("--requester must name the requesting timekeeper")
    if signal_policy.positional_label(requester):
        raise InputError(f"--requester has the reserved positional-label form the engines give another party "
                         f"({signal_policy.FOREIGN_CITATION})")
    eng_id = engagement["engagement_id"]
    requested = [" ".join(p.split()) for p in (args.person or []) if signal_policy.person_key(p)]
    # Names compare in canonical form (person_key): one colleague named twice in variant spellings is one person.
    distinct = {}
    for p in requested:
        if not signal_policy.same_person(p, requester):
            distinct.setdefault(signal_policy.person_key(p), p)
    others = sorted(distinct.values())
    wants_team = bool(args.all_timekeepers or others)
    token = None
    if args.team_view_confirmation is not None:
        token = args.team_view_confirmation  # compared exactly: no trimming, no case folding
        if not signal_policy.TEAM_VIEW_TOKEN_RE.fullmatch(token):
            raise InputError("--team-view-confirmation must be exactly 'engagement-manager:<engagement_id>' "
                             "(no spaces or other characters)")
        if token != signal_policy.team_view_token(eng_id):
            raise InputError("--team-view-confirmation is for another engagement; it must be "
                             "'engagement-manager:<engagement_id>' with the engagement_id recorded in "
                             "raw/engagement-letter-extract.md")
    scope = {"mode": "self", "requester": requester, "people": [requester], "team_view": None, "withheld": None,
             "citations": [signal_policy.SCOPE_CITATION]}
    if not wants_team:
        return {signal_policy.person_key(requester)}, scope
    manager = engagement.get("engagement_manager")
    if token and manager and signal_policy.same_person(requester, manager):
        people = None if args.all_timekeepers else sorted({requester, *others})
        scope.update({"mode": "team", "people": people, "team_view": {
            "confirmed": True,
            "role": "engagement_manager",
            "confirmation": token,
            "verified_against": "raw/engagement-letter-extract.md #engagement (engagement_manager)",
            "citations": [signal_policy.SCOPE_CITATION],
        }})
        return (None if people is None else {signal_policy.person_key(p) for p in people}), scope
    if not manager or not signal_policy.same_person(requester, manager):
        reason = ("team view requested but not authorized" if args.all_timekeepers
                  else "colleagues named but not authorized") + " by the engagement letter (#12.1)"
        reason += ("; raw/engagement-letter-extract.md records no engagement_manager, so no team view can be granted"
                   if not manager else "; the requester is not the engagement manager recorded in "
                   "raw/engagement-letter-extract.md")
        if not token:
            reason += f"; {NO_CONFIRMATION}"
    else:
        reason = NO_CONFIRMATION
    scope["withheld"] = {
        # #13.10: colleagues whose rows are withheld are other parties; they are recorded by position in sorted order
        # (other-timekeeper-name-1), never by the names given, so no name reaches any output. Re-deriving with the
        # labels as --person gives the same labels.
        "requested": "all timekeepers" if args.all_timekeepers else [
            signal_policy.foreign_label("timekeeper", "name", n) for n in range(1, len(others) + 1)],
        "reason": f"colleagues' rows withheld: {reason}; only the requester's rows are returned",
        "citations": [signal_policy.SCOPE_CITATION],
    }
    return {signal_policy.person_key(requester)}, scope


def period_check(period, dates_available, dates_in_period):
    if not (period["start"] or period["end"]):
        # Missing is not empty: with no period requested, a packet with no in-scope data at all still says so.
        return {"status": "no_period_requested", "warning": None if dates_available else (
            "No activity or time entries in scope were found for any date. An empty packet is not evidence that no "
            "work was done - confirm the timekeeper, the engagement and the exports before relying on it.")}
    available = [min(dates_available), max(dates_available)] if dates_available else None
    in_period = [min(dates_in_period), max(dates_in_period)] if dates_in_period else None
    check = {"requested": dict(period), "data_dates_in_period": in_period, "data_dates_available": available}
    if in_period:
        check.update({"status": "data_found", "warning": None})
    else:
        where = (f"activity and time entries in scope are dated {available[0]} to {available[1]}" if available
                 else "no activity or time entries in scope were found for any date")
        check.update({"status": "no_data_in_period", "warning": (
            f"No activity or time entries were found for {period['start'] or 'the start'} to "
            f"{period['end'] or 'the end'}; {where}. An empty packet is not evidence that no work was done - "
            "confirm the period or re-run for the dates that hold data.")})
    return check


def build_parser():
    ap = signal_policy.ArgumentParser(description="Build a cited activity packet from engagement-scoped raw exports.")
    ap.add_argument("--raw-dir", required=True, help="Folder holding the raw exports")
    ap.add_argument("--out", required=True, help="Output activity packet JSON")
    ap.add_argument("--view-out", help="Optional user-facing JSON summary; flagged records expose only ID, date and hours. "
                    "Never use this view as a contract packet")
    ap.add_argument("--signal-config", help="Additional signal policy JSON; it can only narrow the plugin's config/signal-sources.json, which is always applied (most restrictive wins)")
    ap.add_argument("--requester", required=True, help="The requesting timekeeper; only their rows are returned by default")
    who = ap.add_mutually_exclusive_group()
    who.add_argument("--person", action="append", help="Named colleague for the engagement-manager team view (repeatable)")
    who.add_argument("--all-timekeepers", action="store_true", help="Engagement-manager team view: every timekeeper")
    ap.add_argument("--team-view-confirmation", help="Exactly 'engagement-manager:<engagement_id>', supplied only after the "
                    "user explicitly confirms the engagement-manager team view; the requester must be the engagement "
                    "manager recorded in the engagement letter")
    ap.add_argument("--period-start", help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--period-end", help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--scenario", help="Demo scenario label recorded in provenance")
    ap.add_argument("--generated-at", help="Fixed ISO-8601 UTC timestamp for reproducible golden files")
    return ap


def pull(args, script_dir=None, extra_sources=None):
    """activity_pull's whole derivation: the activity packet for the run parameters in args (the parsed command line).
    Returns (packet, signals read, time entries read); raises InputError or signal_policy.PolicyError and writes
    nothing. main() and every later engine's re-derivation (rederive, #12.1, #13.8) run this one function.
    extra_sources is a recorded --signal-config (signal_policy.stage_policy), applied in that file's place."""
    script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
    stamp = generated_at(args.generated_at)
    plugin_config_path = signal_policy.find_plugin_config(script_dir)
    if plugin_config_path:
        config = signal_policy.read_json(plugin_config_path, InputError, label="config/signal-sources.json")
    else:
        config = {"sources": signal_policy.NARROW_DEFAULT,
                  "note": "plugin config/signal-sources.json not found; documented narrow default applied"}
    if not isinstance(config, dict) or not isinstance(config.get("sources"), dict):
        raise InputError("config/signal-sources.json has no 'sources' object")
    # The plugin config (or narrow default) is always applied; --signal-config may only narrow it.
    enabled, _ = signal_policy.effective_sources({}, config_path=args.signal_config, script_dir=script_dir,
                                                 extra_sources=extra_sources)
    config = json.loads(json.dumps(config))
    for key, value in enabled.items():
        entry = config["sources"].get(key)
        if isinstance(entry, dict):
            entry["enabled"] = value
        else:
            config["sources"][key] = {"enabled": value}
    engagement = read_engagement(os.path.join(args.raw_dir, "engagement-letter-extract.md"))
    workplan_rows = read_csv(os.path.join(args.raw_dir, "engagement-workplan.csv"),
                             signal_policy.RAW_EXPORTS["workplan"][1])
    timesheet_rows = read_csv(os.path.join(args.raw_dir, "timesheet.csv"),
                              signal_policy.RAW_EXPORTS["timesheet"][1])
    people, timekeeper_scope = resolve_scope(args, engagement)
    cli_date(args.period_start, "--period-start")
    cli_date(args.period_end, "--period-end")
    if args.period_start and args.period_end and args.period_start > args.period_end:
        raise InputError("--period-start is after --period-end")

    eng_id = engagement["engagement_id"]
    eng_key = signal_policy.canon_id(eng_id)
    period = {"start": args.period_start, "end": args.period_end}
    dates_available, dates_in_period = set(), set()
    withheld_people = set()

    def allowed(row):
        # people never holds a blank key (A21), so a blank person is never in scope; with everyone in scope cell_id
        # refuses it.
        person = signal_policy.person_key(row["person"])
        permitted = people is None or person in people
        if not permitted and timekeeper_scope["mode"] == "self" and in_period(row["date"], period) \
                and signal_policy.canon_id(row.get("engagement_id", eng_id)) == eng_key:
            withheld_people.add(person)
        return permitted
    workplan, workplan_ids = {}, {}
    for idx, row in enumerate(workplan_rows, start=2):
        cite = f"raw/engagement-workplan.csv row {idx}"
        unique(workplan_ids, signal_policy.canon_id(unreserved_id(row["workplan_id"], cite, "workplan_id")), cite,
               "workplan_id")
        # #8.4: every workplan row states its engagement; a row naming none is refused, never skipped.
        unreserved_id(row["engagement_id"], cite, "engagement_id")
        # Item types and match keys compare in canonical form (A13): a variant spelling of a workplan key is the same
        # key, never a missed match that drops the row's activity class. #8.4: a row whose item type is not one the
        # joins use, or whose match key folds to blank (A21), is refused rather than left unindexed, so a workplan of
        # unrecognised rows is never read as an empty one and a blank key never joins a blank event ID or file.
        # T&E QA round 15: every row's grammar is checked before its scope, so another engagement's row is refused
        # for an unrecognised item type or a blank key exactly as this engagement's is, never skipped unread.
        key = (signal_policy.canon_id(row["item_type"]), signal_policy.canon_id(row["match_key"]))
        if key[0] not in WORKPLAN_ITEM_TYPES:
            raise InputError(f"{cite} item_type must be one of {', '.join(WORKPLAN_ITEM_TYPES.values())}; an "
                             "unrecognised workplan row is refused, never skipped (client-billing-guidelines.md #8.4)")
        if not key[1]:
            raise InputError(f"{cite} match_key must not be empty (or only separators or format characters); a blank "
                             "key never joins (client-billing-guidelines.md #8.4)")
        unreserved(row["match_key"], cite, "match_key")
        unreserved(row["activity_class"], cite, "activity_class")
        if signal_policy.canon_id(row["engagement_id"]) != eng_key:
            continue  # #13.10: another engagement's workplan row is never read further or joined
        unique(workplan, key, cite, "item_type and match_key", value=(idx, row))

    signals, skipped_sources, out_of_scope = [], [], []
    foreign_rows = {}  # canonical activity ID of another engagement's row -> its positional label (#13.10)
    activity_rows = {}
    read_keys = set()
    for key, filename, source in SOURCE_FILES:
        path = os.path.join(args.raw_dir, filename)
        if not enabled.get(key):
            if os.path.exists(path) and key not in {s["policy_key"] for s in skipped_sources}:
                skipped_sources.append({"policy_key": key, "file": f"raw/{filename}", "reason": "source disabled; file not opened",
                                        "citations": [POLICY_CITATION]})
            continue
        if key not in PARSERS_AVAILABLE:
            skipped_sources.append({"policy_key": key, "file": f"raw/{filename}",
                                    "reason": "enabled but no approved parser in this version; not read", "citations": [POLICY_CITATION]})
            continue
        read_keys.add(key)
        if key == "calendar":
            rows = read_csv(path, signal_policy.RAW_EXPORTS["calendar"][1])
        else:
            rows = read_csv(path, signal_policy.RAW_EXPORTS["document_activity"][1])
        for idx, row in enumerate(rows, start=2):
            cite = f"raw/{filename} row {idx}"
            # #8.4: a row naming no timekeeper is refused in every scope (as the team view always refused it), never
            # skipped as someone else's. T&E QA round 15: every cell's grammar is checked here, before the row's
            # timekeeper, engagement or date can exclude it, so another party's or another period's row is refused
            # for a malformed or reserved cell exactly as an in-scope one is, never skipped unread.
            cell_id(row, "person", cite)
            unreserved(row["person"], cite, "person")
            unreserved_id(row["activity_id"], cite, "activity_id")
            unreserved_id(row["engagement_id"], cite, "engagement_id", optional=True)
            if key == "calendar":
                unreserved_id(row["event_id"], cite, "event_id", optional=True)
            unique(activity_rows, signal_policy.canon_id(row["activity_id"]), cite, "activity_id")
            row["date"] = cell_date(row, "date", cite)
            if key == "calendar":
                duration = hours_between(row["start"], row["end"], cite)
                unreserved(row["organizer"], cite, "organizer")
                for attendee in row["attendees"].split(";"):
                    unreserved(attendee, cite, "attendees")
            else:
                duration = round(cell_hours(row, "duration_hours", cite), 2)
                unreserved(row["file_name"], cite, "file_name")
            if not allowed(row):
                continue  # #12.1: other timekeepers' rows are never read into the packet
            if signal_policy.canon_id(row["engagement_id"]) != eng_key:
                # #13.3, #13.10: another engagement's row is recorded by its position only; its supplied ID and
                # fields go nowhere, and a timesheet link to it is recorded under the same label.
                label = signal_policy.raw_row_label(filename, idx)
                foreign_rows[signal_policy.canon_id(row["activity_id"])] = label
                out_of_scope.append({"activity_id": label, "reason": "outside engagement scope", "citations": [cite]})
                continue
            dates_available.add(row["date"])
            if not in_period(row["date"], period):
                continue
            dates_in_period.add(row["date"])
            if key == "calendar":
                match = workplan.get((signal_policy.canon_id("calendar_event"), signal_policy.canon_id(row["event_id"])))
                activity_class = (match[1]["activity_class"] if match else "") or "unclassified_meeting"
                subject = row["subject"].strip()
                meeting_id = record_id(row["event_id"], cite, "event_id", optional=True)
                extra = {"organizer": row["organizer"].strip() or None,
                         "attendees": [a.strip() for a in row["attendees"].split(";") if a.strip()]}
            else:
                # D19: a file name that trips the wire is withheld text and selects no workplan row (no purpose,
                # deliverable or confidence is joined on it); the signal itself is held below.
                match = (None if signal_policy.embedded_instruction(row["file_name"]) else
                         workplan.get((signal_policy.canon_id("document"), signal_policy.canon_id(row["file_name"]))))
                activity_class = DOCUMENT_CLASS.get(signal_policy.canon_id(row["activity_type"]), "unclassified_document_activity")
                subject = subject_from_file(row["file_name"])
                meeting_id = None
                extra = {"file_name": row["file_name"]}
            citations = [cite]
            purpose, deliverable = None, None
            if match:
                citations.append(f"raw/engagement-workplan.csv row {match[0]}")
                purpose = match[1]["purpose"].strip() or None
                deliverable = match[1]["deliverable"].strip() or None
            billable = signal_policy.billable_class(activity_class)
            citations.append(POLICY_CITATION)
            if not billable:
                citations.append("client-billing-guidelines.md #5.1")
            signal = {
                "activity_id": row["activity_id"],
                "person": row["person"],
                "date": row["date"],
                "activity_class": activity_class,
                "duration_hours": duration,
                "subject": subject,
                "purpose": purpose,
                "deliverable": deliverable,
                "meeting_id": meeting_id,
                "billable_signal": billable,
            }
            signal.update(extra)
            signal.update({
                "source": source,
                "confidence": signal_policy.signal_confidence(key, purpose if match else None),
                "citations": citations,
            })
            reasons = []
            if not purpose:
                reasons.append("no controlled source states a purpose; purpose left null (never invented)")
            hits = signal_policy.screen(signal_policy.signal_texts(signal))
            if hits:
                signal["embedded_instruction"] = True
                signal["citations"].append(signal_policy.INJECTION_CITATION)
                reasons.append(signal_policy.hold_reason(hits, "text flagged as embedded_instruction") + "; treated "
                               "as data, never drafted from or displayed (client-billing-guidelines.md #11.2)")
            if reasons:
                signal["needs_review"] = True
                signal["review_reason"] = "; ".join(reasons)
            signals.append(signal)

    # Links resolve in canonical form to the exact ID of the signal (or excluded record) they name, so a variant
    # spelling neither drops the evidence nor creates a second record for one activity (A13).
    kept_ids = {signal_policy.canon_id(s["activity_id"]): s["activity_id"] for s in signals}
    # #12.2: a link is evidence only when the activity is the same timekeeper's (canonical person equality).
    owners = {signal_policy.canon_id(s["activity_id"]): s["person"] for s in signals}
    excluded_ids = {}
    entries, excluded, entry_rows = [], [], {}
    for idx, row in enumerate(timesheet_rows, start=2):
        cite = f"raw/timesheet.csv row {idx}"
        cell_id(row, "person", cite)  # #8.4: a row naming no timekeeper is refused, never skipped
        # T&E QA round 15: every cell's grammar is checked before the row's timekeeper or date can exclude it.
        unreserved(row["person"], cite, "person")
        unreserved_id(row["entry_id"], cite, "entry_id")
        unique(entry_rows, signal_policy.canon_id(row["entry_id"]), cite, "entry_id")
        row["date"] = cell_date(row, "date", cite)
        hours = cell_hours(row, "hours", cite)
        links = [a.strip() for a in (row["activity_ids"] or "").split(";") if a.strip()]
        linked = {}
        for link in links:
            if not signal_policy.canon_id(link):
                raise InputError(f"{cite} activity_ids has a blank link (only separators or format characters); "
                                 "a blank key never matches an activity")
            unreserved_id(link, cite, "activity_ids link")
            unique(linked, signal_policy.canon_id(link), cite, "activity_ids link")
        phase_code = unreserved_id(row["phase_code"], cite, "phase_code", optional=True)
        task_code = unreserved_id(row["task_code"], cite, "task_code", optional=True)
        if not allowed(row):
            continue
        dates_available.add(row["date"])
        if not in_period(row["date"], period):
            continue
        dates_in_period.add(row["date"])
        kept_links, dropped, cross = [], [], []
        for link in links:
            link_key = signal_policy.canon_id(link)
            if link_key in kept_ids:
                # Another timekeeper's activity is never this entry's evidence: it is not drafted from, mapped or
                # counted, and the entry is held (cross_person_link, #12.2).
                (kept_links if signal_policy.same_person(owners[link_key], row["person"]) else cross).append(
                    kept_ids[link_key])
                continue
            activity_id = excluded_ids.setdefault(link_key, foreign_rows.get(link_key, link))
            dropped.append(activity_id)
            hint = None if link_key in foreign_rows else next(
                (k for ns, k in ID_NAMESPACE if f" {signal_policy.canon_id(ns)} " in f" {link_key} "), None)
            if hint and not enabled.get(hint):
                reason = signal_policy.pull_disabled_reason(row["entry_id"], cite, hint)
            else:
                reason = signal_policy.pull_missing_reason(row["entry_id"], cite)
            if signal_policy.canon_id(activity_id) not in {signal_policy.canon_id(e["activity_id"]) for e in excluded}:
                excluded.append({"activity_id": activity_id, "source": None, "policy_key": hint, "reason": reason,
                                 "excluded_by": ENGINE, "citations": [cite, POLICY_CITATION]})
        entry = {
            "entry_id": row["entry_id"],
            "person": row["person"],
            "date": row["date"],
            "duration_hours": hours,
            "narrative": row["narrative"],
            "activity_ids": kept_links,
            "submitted_phase_code": phase_code,
            "submitted_task_code": task_code,
            "source": "connector:timesheet",
            "confidence": TIMESHEET_CONFIDENCE,
            "citations": [cite],
        }
        # #13.4: both link sets are always present once activity-pull has run (empty when there is none), so a later
        # stage can tell a deleted list from an empty one and reconcile every copy of the links exactly.
        entry["excluded_activity_ids"] = dropped
        entry["cross_person_activity_ids"] = cross
        linked_signals = [s for s in signals if s["activity_id"] in kept_links]
        if signal_policy.embedded_instruction(signal_policy.entry_texts({"narrative": row["narrative"]}, linked_signals)):
            entry["embedded_instruction"] = True
        entries.append(entry)

    if withheld_people and timekeeper_scope["withheld"] is None:
        timekeeper_scope["withheld"] = {
            "requested": [signal_policy.foreign_label("timekeeper", "name", n)
                          for n in range(1, len(withheld_people) + 1)],
            "reason": SELF_SCOPE_REASON,
            "citations": [signal_policy.SCOPE_CITATION],
        }

    packet = {
        "contract_version": CONTRACT,
        "engagement": {
            "engagement_id": eng_id,
            "client_name": engagement["client_name"],
            "matter_name": engagement["matter_name"],
            "billing_guidelines_id": engagement.get("billing_guidelines_id"),
            "engagement_manager": engagement.get("engagement_manager"),
            "source": "connector:engagement-workspace",
            "confidence": 0.99,
            "citations": ["raw/engagement-letter-extract.md #engagement"],
        },
        "period": period,
        "signal_config": config,
        "guidelines": {
            "guidelines_id": engagement.get("billing_guidelines_id"),
            "summary": "Synthetic outside-counsel-style billing guideline excerpt for demos.",
            "source": "connector:sharepoint-guidelines",
            "confidence": 0.98,
            "citations": ["client-billing-guidelines.md #1.1", "client-billing-guidelines.md #2.1",
                          "client-billing-guidelines.md #3.1", "client-billing-guidelines.md #8.1"],
        },
        "code_structure": {
            "code_set_id": "SYNTH-PS-CODES-2026",
            "source": "connector:billing-code-repository",
            "confidence": 0.98,
            "citations": ["task-phase-codes.md #1.1", "task-phase-codes.md #2.1", "task-phase-codes.md #3.1", "task-phase-codes.md #4.1"],
        },
        "activity_signals": signals,
        "time_entries": entries,
        "provenance": {
            "demo_scenario": args.scenario,
            "generated_at": stamp,
            "engines": [ENGINE_VERSION],
            "sources_read": sorted(read_keys),
            "skipped_sources": skipped_sources,
            "out_of_scope_rows": out_of_scope,
            "excluded_signals": excluded,
            # #13.3: the engagement identity is fixed here, from the engagement letter; every later engine
            # refuses a packet whose engagement header differs from it.
            "engagement_identity": signal_policy.engagement_identity(
                {"engagement_id": eng_id, "client_name": engagement["client_name"],
                 "matter_name": engagement["matter_name"], "engagement_manager": engagement.get("engagement_manager")},
                ["raw/engagement-letter-extract.md #engagement"]),
            "timekeeper_scope": timekeeper_scope,
            "period_check": period_check(period, dates_available, dates_in_period),
        },
    }
    if not args.scenario:
        packet["provenance"].pop("demo_scenario")
    signal_policy.refuse_supplied_markers(packet, exact_ok=False)  # D20: raw input never carries a marker
    signal_policy.filter_packet(packet, config_path=args.signal_config, script_dir=script_dir, engine=ENGINE,
                                extra_sources=extra_sources)
    signal_policy.validate_packet(packet, "activity")  # never emit a packet the next engine would reject
    return packet, len(signals), len(entries)


# --- Re-derivation by every later engine (client-billing-guidelines.md #12.1, #13.8; hardening checklist A23, C6) ---
# The activity packet fields that no raw export determines: activity_pull's run parameters. rederive() reads them back
# from the packet and re-runs pull() on the raw exports with them; the result must still equal the whole packet, so
# each of these is compared like every other field, and a value activity_pull would not have written is a difference.
# Every other field is derived from the raw exports, the skill's config/signal-sources.json or this engine's
# constants. The test-data tests/run_tests.py (qa13_tests) fails when the contract gains a top-level or provenance field that is
# neither derived nor listed here.
RUN_PARAMETERS = {
    ("period",): "--period-start and --period-end: the requested period, which selects rows but is not in any export",
    ("provenance", "demo_scenario"): "--scenario: a demo label recorded as given; it decides nothing",
    ("provenance", "generated_at"): "--generated-at or the clock: the run's own timestamp (signal_policy.NOT_ENGINE_OWNED)",
    ("provenance", "timekeeper_scope"): "--requester, --person or --all-timekeepers and --team-view-confirmation: who "
                                        "asked and which view; the letter and exports decide what that grants",
    ("provenance", "signal_policy"): "--signal-config: an additional policy (signal_policy.stage_policy), which can only "
                                     "narrow the plugin's config/signal-sources.json",
}


def run_parameters(packet, raw_dir):
    """The command line that would have written packet from raw_dir, read back from the fields in RUN_PARAMETERS. A
    value activity_pull could not have written gives a command line that fails or writes another packet."""
    provenance = packet["provenance"]
    scope = provenance["timekeeper_scope"]
    args = argparse.Namespace(raw_dir=raw_dir, signal_config=None, requester=scope["requester"], person=None,
                              all_timekeepers=False, team_view_confirmation=None,
                              period_start=packet["period"]["start"], period_end=packet["period"]["end"],
                              scenario=provenance.get("demo_scenario"), generated_at=provenance["generated_at"])
    withheld = scope.get("withheld")
    if scope.get("mode") == "team":
        if scope.get("people") is None:
            args.all_timekeepers = True
        else:
            args.person = list(scope["people"])
        args.team_view_confirmation = (scope.get("team_view") or {}).get("confirmation")
    elif isinstance(withheld, dict) and withheld.get("reason") != SELF_SCOPE_REASON:
        if withheld.get("requested") == "all timekeepers":
            args.all_timekeepers = True
        else:
            args.person = list(withheld.get("requested") or [])
        # A confirmation that was supplied leaves only the withheld reason behind; activity_pull accepts no other token
        # than the engagement's own.
        if NO_CONFIRMATION not in str(withheld.get("reason")):
            args.team_view_confirmation = signal_policy.team_view_token(packet["engagement"]["engagement_id"])
    return args


def rederive(packet, raw_dir, script_dir=None):
    """activity_pull re-run on raw_dir with the packet's recorded run parameters: the activity packet it would write
    (as written, a JSON round trip), for a later engine to compare with the whole carried packet. Writes nothing."""
    args = run_parameters(packet, raw_dir)
    derived, _, _ = pull(args, script_dir=script_dir,
                         extra_sources=signal_policy.stage_policy(packet, "activity", writer=True))
    return json.loads(signal_policy.dump_json(derived))


def activity_view(packet):
    """A presentation-only projection; flagged records never expose any of their free text (#11.2)."""
    def row(record, id_key, fields, flagged):
        if flagged:
            return {id_key: record[id_key], "date": record["date"],
                    "duration_hours": record["duration_hours"],
                    "notice": "[withheld: flagged as embedded_instruction]"}
        return {key: record[key] for key in fields if key in record}

    provenance = packet["provenance"]
    return {
        "view": "activity summary (not a contract packet)",
        "period": packet["period"],
        "timekeeper_scope": provenance["timekeeper_scope"],
        "period_check": provenance["period_check"],
        "activity_signals": [
            row(signal, "activity_id",
                ("activity_id", "date", "person", "activity_class", "duration_hours", "subject", "purpose",
                 "deliverable", "needs_review", "review_reason", "citations"),
                signal_policy.signal_flagged(signal))
            for signal in packet["activity_signals"]],
        "time_entries": [
            row(entry, "entry_id",
                ("entry_id", "date", "person", "duration_hours", "submitted_task_code", "activity_ids", "citations"),
                entry.get("embedded_instruction") is True
                or signal_policy.embedded_instruction(signal_policy.entry_texts(entry, [])))
            for entry in packet["time_entries"]],
        "excluded_signals": provenance["excluded_signals"],
        "skipped_sources": provenance["skipped_sources"],
        "out_of_scope_rows": provenance["out_of_scope_rows"],
    }


def main():
    args = build_parser().parse_args()
    try:
        if args.view_out and (
                os.path.normcase(os.path.realpath(args.out)) == os.path.normcase(os.path.realpath(args.view_out))
                or (os.path.exists(args.out) and os.path.exists(args.view_out)
                    and os.path.samefile(args.out, args.view_out))):
            raise InputError("--view-out must differ from --out; the user-facing view cannot replace the contract packet")
        packet, signal_count, entry_count = pull(args)
    except (InputError, signal_policy.PolicyError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        # PolicyError covers SchemaError and a missing contract (no traceback).
        sys.exit(f"activity_pull: {signal_policy.error_text(exc)}")
    try:
        if args.view_out:
            signal_policy.write_output(args.view_out, signal_policy.dump_json(activity_view(packet)))
        signal_policy.write_output(args.out, signal_policy.dump_json(packet))
    except (OSError, ValueError) as exc:  # ValueError covers NaN in dump_json and UnicodeEncodeError
        sys.exit(f"activity_pull: cannot write output: {signal_policy.error_text(exc)}")
    timekeeper_scope = packet["provenance"]["timekeeper_scope"]
    print(f"activity_pull: {signal_count} signal(s), {entry_count} time entr(ies), "
          f"{len(packet['provenance']['excluded_signals'])} excluded link(s) -> activity packet written")
    if timekeeper_scope["withheld"]:
        print(f"activity_pull: WARNING {timekeeper_scope['withheld']['reason']} ({signal_policy.SCOPE_CITATION})")
    if packet["provenance"]["period_check"].get("warning"):
        print(f"activity_pull: WARNING {packet['provenance']['period_check']['warning']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
