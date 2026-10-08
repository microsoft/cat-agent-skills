"""template-based-document-generation - single entry point.

Subcommands (see SKILL.md):
    doctor     check the runtime
    inspect    snapshot the template, inventory paragraphs and candidates, write manifest.json + plan.draft.json
    execute    compile plan + values -> apply -> verify -> report.json (+ output/<stem>__<job_id>.docx)
               --dry-run prints the change list and review items without writing anything
    selftest   run the bundled fixtures end to end against the oracle under <workdir>/selftest/
    tests      run the unit test modules; source tree only, fails (exit 1) when they are absent

Exit codes: 0 ok, 1 failed (unreadable or blocked template, invalid inputs, verification failed, I/O
error), 2 needs_review (the document was produced; the report lists what a person should look at).

Standard library only. Every path is an argument; nothing is assumed about the platform.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import sys
import time
from datetime import datetime, timezone
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import models  # noqa: E402

REFERENCES = os.path.normpath(os.path.join(HERE, "..", "references"))
POLICY_DEFAULT = os.path.join(REFERENCES, "policy.json")
PROFILE_DEFAULT = os.path.join(REFERENCES, "profile.default.json")

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_NEEDS_REVIEW = 2
RESULT_EXIT = {"ok": EXIT_OK, "needs_review": EXIT_NEEDS_REVIEW, "failed": EXIT_FAILED}


class Refused(Exception):
    """A precondition failed; nothing was produced. The message is safe to show."""


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def _encoding_safe_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


class Phases:
    """Elapsed time per phase, printed by every command.

    It lives in the scripts rather than in the skill instructions on purpose: the numbers then come from
    whatever machine actually runs the job, they cost nothing in the model's context, and a model is
    never asked to estimate its own elapsed time. Script time is usually a small fraction of a run; the
    rest is the model reading the listing and composing the plan.
    """

    def __init__(self) -> None:
        self.start = time.perf_counter()
        self.marks: list[tuple[str, float]] = []
        self._last = self.start

    def mark(self, name: str) -> None:
        now = time.perf_counter()
        self.marks.append((name, now - self._last))
        self._last = now

    def line(self) -> str:
        total = time.perf_counter() - self.start
        detail = "  ".join(f"{n} {d:.2f}s" for n, d in self.marks if d >= 0.005)
        return f"{total:.2f}s total" + (f"   ({detail})" if detail else "")


def new_job_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)


def new_attempt_id() -> str:
    """Microsecond resolution, so attempt directories sort chronologically even within one second."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + secrets.token_hex(2)


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# Windows resolves an ordinary path through an API limited to 260 characters including the terminating
# null, unless long paths are enabled machine-wide. Staying under that is not optional for a skill that
# runs wherever the caller puts it, so leave a little slack and treat it as the budget.
PATH_BUDGET = 250 if sys.platform == "win32" else 4000


def _temp_name(path: str, suffix: str = ".tmp") -> str:
    """A temporary name nothing else can be using, so two runs cannot corrupt one another's write.

    The temporary sits beside its destination and so shares the destination's path budget. Appending to
    the destination's name makes the temporary the longest path in the job, which on Windows can push it
    past the limit while the real file would have fitted: the write then fails with a bare "no such file
    or directory" naming a path the caller never asked for. So the readable part is trimmed to make room
    for the token rather than the other way round. The token is what keeps concurrent runs apart; the
    name it hangs off is only a convenience when someone inspects a directory mid-run.
    """
    token = f".{os.getpid()}-{secrets.token_hex(4)}{suffix}"
    head, tail = os.path.split(path)
    if not tail:
        return path + token
    room = PATH_BUDGET - len(os.path.join(os.path.abspath(head or "."), token))
    return os.path.join(head, tail[: max(0, min(len(tail), room))] + token)


def _io_failure(path: str, exc: OSError) -> OSError:
    """Path length is the one I/O failure whose message does not say what is wrong. Name it, because the
    remedy is to move the work directory and nothing in the error hints at that."""
    full = os.path.abspath(path)
    if sys.platform == "win32" and len(full) >= PATH_BUDGET:
        return OSError(
            f"{exc}: the path is {len(full)} characters, at or over the {PATH_BUDGET} this platform "
            f"allows for; run the job under a shorter --workdir"
        )
    return exc


def _write_bytes(path: str, data: bytes) -> None:
    tmp = _temp_name(path)
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except OSError as exc:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise _io_failure(path, exc) from exc


def _copy_atomic(src: str, dst: str) -> None:
    """Copy via a temporary name in the destination directory, then rename. An interrupted copy leaves
    the temporary file behind, never a half-written document under the real name."""
    tmp = _temp_name(dst, ".part")
    try:
        shutil.copyfile(src, tmp)
        os.replace(tmp, dst)
    except OSError as exc:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise _io_failure(dst, exc) from exc


def _write_text(path: str, text: str) -> None:
    _write_bytes(path, text.encode("utf-8"))


def _load_policy(path: str) -> tuple[dict[str, Any], str]:
    policy, sha, errs = models.load_policy(path)
    if errs:
        raise Refused("policy is not usable: " + "; ".join(errs[:3]))
    return policy, sha


def _load_profile(override_path: str | None) -> dict[str, Any]:
    with open(PROFILE_DEFAULT, "rb") as fh:
        default_raw = fh.read()
    override_raw = None
    if override_path:
        with open(override_path, "rb") as fh:
            override_raw = fh.read()
    profile, errs = models.parse_profile(default_raw, override_raw)
    if errs:
        raise Refused("profile is not usable: " + "; ".join(errs[:3]))
    return profile


def _load_document(path: str, cls: type, label: str) -> Any:
    if not os.path.exists(path):
        raise Refused(f"{label} is missing ({os.path.basename(path)})")
    try:
        data = _read_json(path)
    except (OSError, UnicodeError, ValueError) as exc:
        raise Refused(f"{label} could not be read as UTF-8 JSON ({exc.__class__.__name__})") from exc
    errs = models.validate_document(data, cls)
    if errs:
        raise Refused(f"{label} does not validate: " + "; ".join(errs[:5]))
    return models.from_dict(data, cls)


def _stem(source_name: str, policy: dict[str, Any]) -> str:
    delivery = policy.get("delivery", {})
    allowed = delivery.get("filename_allowed_chars", "A-Za-z0-9._-")
    stem = os.path.splitext(source_name)[0] or "document"
    stem = re.sub(f"[^{allowed}]+", "_", stem)
    stem = re.sub("_+", "_", stem).strip("._-") or "document"
    return stem[: int(delivery.get("filename_max_stem_chars", 60))].rstrip("._-") or "document"


class JobPaths:
    def __init__(self, job_dir: str):
        self.dir = os.path.abspath(job_dir)
        self.snapshot = os.path.join(self.dir, "snapshot.docx")
        self.manifest = os.path.join(self.dir, "manifest.json")
        self.plan_draft = os.path.join(self.dir, "plan.draft.json")
        self.plan = os.path.join(self.dir, "plan.json")
        self.values = os.path.join(self.dir, "values.json")
        self.report = os.path.join(self.dir, "report.json")
        self.output_dir = os.path.join(self.dir, "output")
        self.attempts_dir = os.path.join(self.dir, "attempts")


# --------------------------------------------------------------------------------------
# doctor
# --------------------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    import importlib
    import tempfile

    ok = True

    def row(status: str, name: str, detail: str = "") -> None:
        print(f"{status:<5} {name:<28} {detail}")

    v = sys.version_info
    if (v.major, v.minor) >= (3, 10):
        row("PASS", "python >= 3.10", f"{v.major}.{v.minor}.{v.micro}")
    else:
        ok = False
        row("FAIL", "python >= 3.10", f"{v.major}.{v.minor}.{v.micro}")
    for mod in ("zipfile", "hashlib", "json", "re", "dataclasses", "decimal", "xml.etree.ElementTree", "xml.parsers.expat"):
        try:
            importlib.import_module(mod)
            row("PASS", f"stdlib {mod}")
        except Exception as exc:  # pragma: no cover
            ok = False
            row("FAIL", f"stdlib {mod}", str(exc))
    if args.workdir:
        try:
            os.makedirs(args.workdir, exist_ok=True)
            fd, probe = tempfile.mkstemp(prefix=".doctor-", dir=args.workdir)
            os.close(fd)
            os.remove(probe)
            row("PASS", "workdir writable", args.workdir)
            if sys.platform == "win32":
                # The deepest path a job builds is attempts/<attempt id>/<document name>, and the document
                # name is the template stem plus the job id. Measure it with the real id generators rather
                # than a guessed length, so this cannot drift away from what execute goes on to write.
                deepest = os.path.join(os.path.abspath(args.workdir), new_job_id(), "attempts", new_attempt_id(), "")
                room = PATH_BUDGET - len(deepest) - len(f"__{new_job_id()}.docx")
                shape = f"{len(os.path.abspath(args.workdir))} characters leaves room for a template name of"
                if room < 1:
                    # Not a preference at this point: there is no document name short enough to work, so
                    # passing here would send the caller into a job that cannot be written.
                    ok = False
                    row("FAIL", "workdir path length",
                        f"{shape} {room} characters, so no job can be written under the {PATH_BUDGET}-character "
                        f"Windows path limit; use a shorter --workdir")
                elif room < 60:
                    row("WARN", "workdir path length",
                        f"{shape} {room} characters before the {PATH_BUDGET}-character Windows path limit; "
                        f"a longer template name will fail, so prefer a shorter --workdir")
                else:
                    row("PASS", "workdir path length", f"room for a {room}-character template name")
        except Exception as exc:
            ok = False
            row("FAIL", "workdir writable", f"{args.workdir}: {exc}")
    else:
        row("NOTE", "workdir writable", "pass --workdir to test the job directory")
    try:
        _load_policy(args.policy)
        row("PASS", "policy", os.path.basename(args.policy))
        _load_profile(None)
        row("PASS", "default profile", os.path.basename(PROFILE_DEFAULT))
    except (Refused, OSError) as exc:
        ok = False
        row("FAIL", "policy/profile", str(exc))
    row("PASS", "contract", f"skill {models.SKILL_VERSION}, contract {models.CONTRACT_VERSION}")
    print("doctor:", "OK" if ok else "FAILED")
    return EXIT_OK if ok else EXIT_FAILED


# --------------------------------------------------------------------------------------
# inspect
# --------------------------------------------------------------------------------------

def do_inspect(template_path: str, workdir: str, policy_path: str, profile_path: str | None, quiet: bool = False) -> tuple[int, str]:
    phases = Phases()
    """Returns (exit code, job directory). Exit 0 inspected (draft written), 1 blocked or unreadable."""
    import inspect_template as it
    import ooxml_common as oc

    def say(*a: Any) -> None:
        if not quiet:
            print(*a)

    try:
        policy, policy_sha = _load_policy(policy_path)
        profile = _load_profile(profile_path)
        with open(template_path, "rb") as fh:
            data = fh.read()
        job_dir = ""
        for _attempt in range(3):
            job_id = new_job_id()
            job_dir = os.path.join(workdir, job_id)
            try:
                os.makedirs(job_dir, exist_ok=False)
                break
            except FileExistsError:
                continue
        else:
            raise Refused("could not allocate a job directory")
        paths = JobPaths(job_dir)
        _write_bytes(paths.snapshot, data)
        source_name = it.sanitize_name(os.path.basename(template_path))
        try:
            manifest = it.inspect(data, policy, policy_sha, profile, job_id, source_name)
        except (oc.PackageError, UnicodeError) as exc:
            _write_text(os.path.join(job_dir, "inspect-failure.json"), json.dumps({"job_id": job_id, "error": str(exc), "skill_version": models.SKILL_VERSION}, indent=2) + "\n")
            print(f"inspect: cannot read the template as a Word package: {exc}", file=sys.stderr)
            say(f"job: {job_dir} (snapshot kept; see inspect-failure.json)")
            return EXIT_FAILED, job_dir
        _write_text(paths.manifest, models.pretty_json(manifest))
    except Refused as exc:
        print(f"inspect: refused: {exc}", file=sys.stderr)
        return EXIT_FAILED, ""
    except OSError as exc:
        print(f"inspect: failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        if sys.platform == "win32" and isinstance(exc, FileNotFoundError):
            print("inspect: on Windows this usually means the work directory path is too long; use a short path such as C:/w", file=sys.stderr)
        return EXIT_FAILED, ""

    say(f"job:        {job_dir}")
    say(f"template:   {source_name} sha256 {manifest.template.sha256[:16]}... ({manifest.template.size_bytes:,} bytes)")
    say(f"paragraphs: {len(manifest.paragraphs)} in {len(manifest.parts_in_scope)} part(s) in scope; rows: {len(manifest.rows)}")
    required = sum(1 for c in manifest.candidates if c.decision_required)
    say(f"candidates: {len(manifest.candidates)} ({required} need a decision; '!' below); ineligible: {sum(1 for c in manifest.candidates if not c.eligible)}")
    for f in manifest.findings:
        say(f"finding:    {f.code} [{f.severity}] {f.part or ''} {f.detail}")
    for n in manifest.coverage.notes:
        say(f"note:       {n}")
    if manifest.blocked:
        say("result:     blocked - the template cannot be filled (see findings); no plan draft written")
        say(f"elapsed:    {phases.line()}")
        return EXIT_FAILED, job_dir
    for line in it.listing(manifest):
        say(line)
    plan = it.draft_plan(manifest)
    _write_text(paths.plan_draft, models.sparse_json(plan))
    say(f"elapsed:    {phases.line()}")
    say("next:       copy plan.draft.json to plan.json, decide every candidate, map every field source, add operations;")
    say("            write values.json as {\"data\": ...}; then execute --dry-run, then execute")
    return EXIT_OK, job_dir


def cmd_inspect(args: argparse.Namespace) -> int:
    rc, _ = do_inspect(args.template, args.workdir, args.policy, args.profile)
    return rc


# --------------------------------------------------------------------------------------
# execute
# --------------------------------------------------------------------------------------

class Loaded:
    def __init__(self, paths: JobPaths, policy: dict[str, Any], policy_sha: str):
        import inspect_template
        import ooxml_common

        self.paths, self.policy, self.policy_sha = paths, policy, policy_sha
        if not os.path.exists(paths.snapshot):
            raise Refused("snapshot.docx is missing; run inspect first")
        with open(paths.snapshot, "rb") as fh:
            self.snapshot = fh.read()
        self.manifest = _load_document(paths.manifest, models.Manifest, "manifest.json")
        if models.sha256_bytes(self.snapshot) != self.manifest.template.sha256:
            raise Refused("snapshot.docx does not match manifest.json; the job directory has been altered")
        if self.manifest.policy_sha256 != policy_sha:
            raise Refused("the policy file differs from the one the template was inspected with; run inspect again")
        if self.manifest.skill_version != models.SKILL_VERSION:
            raise Refused("the job belongs to a different skill version; run inspect again")
        try:
            actual = inspect_template.inspect(self.snapshot, policy, policy_sha, self.manifest.profile, self.manifest.job_id, self.manifest.template.source_name)
        except ooxml_common.PackageError as exc:
            raise Refused("snapshot.docx is not a readable Word package; run inspect again") from exc
        actual.created_utc = self.manifest.created_utc
        if models.sha256_document(actual) != models.sha256_document(self.manifest):
            raise Refused("manifest.json does not describe snapshot.docx under the current policy and profile; run inspect again")
        if self.manifest.blocked:
            raise Refused("the manifest marks this template as blocked; nothing can be executed")
        self.plan = _load_document(paths.plan, models.Plan, "plan.json")
        self.values = _load_document(paths.values, models.Values, "values.json")


def _print_compiled(compiled: models.Compiled, changes: list[models.Change]) -> None:
    for c in changes:
        where = c.paragraph or c.part
        if c.op in ("replace_text", "fill_control"):
            print(f"  {c.op:<22} {where}: {c.before!r} -> {c.after!r}")
        elif c.op.startswith("delete"):
            print(f"  {c.op:<22} {where}: {c.before!r}{' (' + c.detail + ')' if c.detail else ''}")
        elif c.op == "repeat_row":
            print(f"  {c.op:<22} {where}: {c.before!r} x {c.detail}: {c.after!r}")
        else:
            print(f"  {c.op:<22} {where}: + {c.after!r}")
    for r in compiled.review:
        print(f"  review: {r.code:<24} {r.detail}")


def _record_refusal(paths: "JobPaths", policy_sha: str, reason: str, say: Any) -> None:
    """A run rejected before it began still happened.

    Without this, a malformed values.json returns failure while `report.json` still carries the previous
    run's `ok`, which is the worst of both: nothing was produced and the job still reads as successful.
    A full report needs the job's identity, so when that cannot be read the refusal is recorded on its
    own and `report.json` is left to the attempt that wrote it.
    """
    attempt_id = new_attempt_id()
    attempt_dir = os.path.join(paths.attempts_dir, attempt_id)
    try:
        os.makedirs(attempt_dir, exist_ok=True)
        _write_text(os.path.join(attempt_dir, "refused.json"), json.dumps(
            {"refused_utc": models.utc_now(), "reason": reason, "skill_version": models.SKILL_VERSION}, indent=2) + "\n")
        job_id = os.path.basename(paths.dir)
        template_sha = ""
        if os.path.exists(paths.snapshot):
            with open(paths.snapshot, "rb") as fh:
                template_sha = models.sha256_bytes(fh.read())
        if re.fullmatch(models.JOB_ID_PATTERN, job_id) and template_sha and re.fullmatch(models.SHA256_PATTERN, policy_sha or ""):
            report = models.Report(
                schema=models.SCHEMA_REPORT, skill_version=models.SKILL_VERSION, contract_version=models.CONTRACT_VERSION,
                job_id=job_id, created_utc=models.utc_now(), template_sha256=template_sha, policy_sha256=policy_sha,
                result="failed", checks=[models.Check(id="input.accepted", outcome="failed", detail=reason[:800])],
                notes=["this run was rejected before anything was produced; no document was written"])
            text = models.pretty_json(report)
            _write_text(os.path.join(attempt_dir, "report.json"), text)
            _write_text(paths.report, text)
        say(f"attempt:    {attempt_dir}")
    except OSError as exc:
        print(f"execute: could not record the refusal: {exc}", file=sys.stderr)


def do_execute(job_dir: str, policy_path: str, out_dir: str | None = None, dry_run: bool = False, quiet: bool = False) -> tuple[int, models.Report | None]:
    phases = Phases()
    import apply_plan as ap
    import ooxml_common as oc
    import verify_document as vd

    paths = JobPaths(job_dir)

    def say(*a: Any) -> None:
        if not quiet:
            print(*a)

    policy_sha = ""
    try:
        policy, policy_sha = _load_policy(policy_path)
        loaded = Loaded(paths, policy, policy_sha)
    except Refused as exc:
        print(f"execute: refused: {exc}", file=sys.stderr)
        _record_refusal(paths, policy_sha, str(exc), say)
        return EXIT_FAILED, None
    except OSError as exc:
        print(f"execute: failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        _record_refusal(paths, policy_sha, f"{exc.__class__.__name__}: {exc}", say)
        return EXIT_FAILED, None

    phases.mark("load")
    manifest, plan, values = loaded.manifest, loaded.plan, loaded.values
    limits = policy.get("limits", {})
    compiled = models.compile_plan(plan, manifest, values, policy)
    phases.mark("compile")
    checks: list[models.Check] = []
    notes: list[str] = ["ok means mechanically checked against the template and the plan; nobody has looked at the layout in Word"]
    if compiled.is_empty() and not compiled.errors:
        compiled.review.append(models.ReviewItem("no_operations", "the plan changes nothing; the output is a copy of the template"))

    bindings = dict(manifest_sha256=models.sha256_document(manifest), plan_sha256=models.sha256_document(plan), values_sha256=models.sha256_document(values))

    def build_report(result: str, review: list[models.ReviewItem], changes: list[models.Change], output: models.OutputInfo | None) -> models.Report:
        return models.Report(schema=models.SCHEMA_REPORT, skill_version=models.SKILL_VERSION, contract_version=models.CONTRACT_VERSION,
                             job_id=manifest.job_id, created_utc=models.utc_now(), template_sha256=manifest.template.sha256,
                             policy_sha256=policy_sha, result=result, checks=list(checks), review=list(review), changes=list(changes),
                             output=output, notes=list(notes), **bindings)

    attempt_id = new_attempt_id()
    attempt_dir = os.path.join(paths.attempts_dir, attempt_id)
    stem = _stem(manifest.template.source_name, policy)
    doc_name = f"{stem}__{manifest.job_id}.docx"
    report_name = f"{stem}__{manifest.job_id}.report.json"

    def record(report: models.Report) -> None:
        """Every attempt leaves a durable record, and <job>/report.json always describes the latest one.
        A previously produced document is never removed until a new one exists."""
        text = models.pretty_json(report)
        os.makedirs(attempt_dir, exist_ok=True)
        _write_text(os.path.join(attempt_dir, "report.json"), text)
        _write_text(paths.report, text)

    if compiled.errors:
        say(f"job:        {paths.dir}")
        for e in compiled.errors[:40]:
            say(f"invalid:    {e}")
        if len(compiled.errors) > 40:
            say(f"invalid:    ... {len(compiled.errors) - 40} more")
        say("result:     failed - fix plan.json / values.json and run again")
        if dry_run:
            return EXIT_FAILED, None
        for e in compiled.errors[:40]:
            checks.append(models.Check(id="input.plan", outcome="failed", detail=e[:800]))
        if os.path.isdir(paths.output_dir):
            notes.append(f"output/ still holds the document of an earlier attempt and does not correspond to this report; attempt {attempt_id} failed")
        try:
            report = build_report("failed", [], [], None)
            record(report)
        except OSError as exc:
            print(f"execute: failed: could not write the report: {exc}", file=sys.stderr)
            return EXIT_FAILED, None
        say(f"attempt:    {attempt_dir}")
        say(f"elapsed:    {phases.line()}")
        return EXIT_FAILED, report

    # ---- dry run: describe, do not write ------------------------------------------------------
    if dry_run:
        pkg = oc.read_package(loaded.snapshot, limits)
        roots = {part: oc.parse_xml(pkg.parts[part], limits, part) for part in compiled.parts if part in pkg.parts}
        changes = vd.describe_changes(roots, compiled, limits)
        say(f"job:        {paths.dir}")
        say(f"dry run:    {len(changes)} change(s), {len(compiled.review)} review item(s); nothing written")
        if not quiet:
            _print_compiled(compiled, changes)
        say("result:     " + ("would need review" if compiled.review else "would be ok") + " (subject to verification)")
        say(f"elapsed:    {phases.line()}")
        return EXIT_OK, None

    # ---- apply and verify -----------------------------------------------------------------------
    report: models.Report | None = None
    review: list[models.ReviewItem] = []
    changes: list[models.Change] = []
    try:
        candidate: bytes | None = None
        try:
            applied = ap.apply(loaded.snapshot, manifest, compiled, policy)
            candidate = applied.candidate
            checks.append(models.Check(id="fill.applied", outcome="passed", detail="; ".join(applied.notes)[:800]))
            notes += [n for n in applied.notes if "cleared" in n]
        except (ap.ApplyRefused, oc.PackageError, UnicodeError) as exc:
            checks.append(models.Check(id="fill.applied", outcome="failed", detail=str(exc)[:800]))
        phases.mark("apply")
        review = list(compiled.review)
        output: models.OutputInfo | None = None
        if candidate is not None:
            vr = vd.verify(loaded.snapshot, candidate, manifest, plan, compiled, policy)
            checks += vr.checks
            review += vr.review
            changes = vr.changes
            notes += vr.notes
        phases.mark("verify")
        result = models.derive_result(checks, review)
        if candidate is not None and result != "failed":
            output = models.OutputInfo(filename=doc_name, sha256=models.sha256_bytes(candidate), size_bytes=len(candidate))
        elif os.path.isdir(paths.output_dir):
            notes.append(f"output/ still holds the document of an earlier attempt and does not correspond to this report; attempt {attempt_id} failed")

        os.makedirs(attempt_dir, exist_ok=True)
        if candidate is not None:
            _write_bytes(os.path.join(attempt_dir, doc_name if output is not None else "failed-candidate.docx"), candidate)
        report = build_report(result, review, changes, output)
        record(report)
        report_text = models.pretty_json(report)
        delivered: list[str] = []
        if output is not None and candidate is not None:
            _write_text(os.path.join(attempt_dir, report_name), report_text)
            # Publish only now that a verified document exists, so a failed attempt can never clear
            # output/ and leave the job with nothing.
            staging = paths.output_dir + _temp_name("", ".new")
            os.makedirs(staging)
            _write_bytes(os.path.join(staging, doc_name), candidate)
            _write_text(os.path.join(staging, report_name), report_text)
            # The previous publication is moved aside, not destroyed, so a promotion that fails leaves a
            # published document rather than nothing. Only once the new one is in place is the old removed.
            retired = paths.output_dir + _temp_name("", ".previous") if os.path.isdir(paths.output_dir) else None
            if retired:
                os.replace(paths.output_dir, retired)
            try:
                os.replace(staging, paths.output_dir)
            except OSError:
                if retired:
                    os.replace(retired, paths.output_dir)
                raise
            if retired:
                shutil.rmtree(retired, ignore_errors=True)
            delivered.append(os.path.join(paths.output_dir, doc_name))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
                _copy_atomic(os.path.join(paths.output_dir, doc_name), os.path.join(out_dir, doc_name))
                _write_text(os.path.join(out_dir, report_name), report_text)
                delivered.append(os.path.join(out_dir, doc_name))
    except OSError as exc:
        print(f"execute: failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        # A report was written before publication was attempted. Leaving it saying ok would assert a
        # delivery that did not happen, so it is corrected to name the failure.
        if report is not None:
            checks.append(models.Check(id="delivery.published", outcome="failed", detail=f"{exc.__class__.__name__}: {exc}"[:800]))
            notes.append("the document was verified but could not be published; it is in the attempt directory")
            try:
                record(build_report("failed", review, changes, None))
            except OSError:
                print("execute: the report could not be corrected either", file=sys.stderr)
        return EXIT_FAILED, None

    say(f"job:        {paths.dir}")
    say(f"result:     {result}")
    for c in checks:
        if c.outcome != "passed":
            say(f"check:      {c.id} {c.outcome} {c.detail}")
    say(f"changes:    {len(changes)}")
    if not quiet:
        _print_compiled(models.Compiled(review=review), changes)
    for d in delivered:
        say(f"output:     {d}")
    if candidate is not None and result == "failed":
        say(f"candidate:  {os.path.join(attempt_dir, 'failed-candidate.docx')} (for diagnosis only; do not deliver)")
    say(f"attempt:    {attempt_dir}")
    say(f"report:     {paths.report}")
    phases.mark("publish")
    say(f"elapsed:    {phases.line()}")
    return RESULT_EXIT[result], report


def cmd_execute(args: argparse.Namespace) -> int:
    rc, _ = do_execute(args.job, args.policy, args.out, args.dry_run)
    return rc


# --------------------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------------------

def output_texts(docx: bytes, parts: list[str], limits: dict[str, Any]) -> dict[str, list[str]]:
    import ooxml_common as oc

    pkg = oc.read_package(docx, limits)
    out: dict[str, list[str]] = {}
    for part in parts:
        if part in pkg.parts:
            root = oc.parse_xml(pkg.parts[part], limits, part)
            out[part] = [oc.paragraph_text(p) for p in oc.paragraphs(root)]
    return out


def do_selftest(workdir: str, policy_path: str, quiet: bool = True) -> int:
    """Run every fixture that has an oracle file through inspect -> plan -> execute and compare."""
    import build_fixtures as bf

    root = os.path.normpath(os.path.join(HERE, ".."))
    expected_dir = os.path.join(root, "assets", "expected")
    run_dir = os.path.join(workdir, "selftest", new_job_id())
    templates, jobs = os.path.join(run_dir, "templates"), os.path.join(run_dir, "jobs")
    os.makedirs(templates)
    os.makedirs(jobs)
    policy, _sha = _load_policy(policy_path)
    limits = policy.get("limits", {})
    results: list[tuple[str, str, bool, str]] = []

    def record(fixture: str, case: str, ok: bool, detail: str = "") -> None:
        results.append((fixture, case, ok, detail))

    def prepare(job_dir: str, run: dict[str, Any]) -> None:
        paths = JobPaths(job_dir)
        plan = _read_json(paths.plan_draft)
        plan["notes"] = None
        for key in ("decisions", "fields", "operations", "locale", "allow_large_deletion", "review_flags"):
            if key in run.get("plan", {}):
                plan[key] = run["plan"][key]
        if "manifest_sha256" in run.get("plan", {}):
            plan["manifest_sha256"] = run["plan"]["manifest_sha256"]
        _write_text(paths.plan, json.dumps(plan, indent=2) + "\n")
        _write_text(paths.values, json.dumps({"schema": models.SCHEMA_VALUES, "data": run.get("values")}, indent=2) + "\n")

    for name, build in bf.FIXTURE_BUILDERS.items():
        exp_path = os.path.join(expected_dir, f"{name}.json")
        if not os.path.exists(exp_path):
            record(name, "oracle file present", False, "no assets/expected file")
            continue
        exp = _read_json(exp_path)
        template_path = os.path.join(templates, f"{name}.docx")
        _write_bytes(template_path, bf.package(build()))
        rc, job_dir = do_inspect(template_path, jobs, policy_path, exp.get("profile"), quiet=True)
        want_inspect = exp["inspect"]
        if want_inspect.get("blocked"):
            record(name, "inspect blocked", rc == EXIT_FAILED and os.path.exists(JobPaths(job_dir).manifest), f"rc={rc}")
            record(name, "no plan draft", not os.path.exists(JobPaths(job_dir).plan_draft))
            continue
        record(name, "inspect exits 0", rc == EXIT_OK, f"rc={rc}")
        if rc != EXIT_OK:
            continue
        manifest = _read_json(JobPaths(job_dir).manifest)
        got_texts: dict[str, list[str]] = {}
        for p in manifest["paragraphs"]:
            got_texts.setdefault(p["part"], []).append(p["text"])
        for part, texts in want_inspect.get("paragraph_texts", {}).items():
            record(name, f"paragraph texts {part}", got_texts.get(part) == texts, f"got {got_texts.get(part)}")
        keys = ("id", "kind", "pattern", "confidence", "eligible", "decision_required", "name_guess")
        got_c = sorted(tuple(c.get(k) for k in keys) for c in manifest["candidates"])
        want_c = sorted(tuple(c.get(k) for k in keys) for c in want_inspect.get("candidates", []))
        record(name, "candidates match oracle", got_c == want_c, "" if got_c == want_c else f"got {got_c}")
        record(name, "finding codes", sorted(f["code"] for f in manifest["findings"]) == sorted(want_inspect.get("findings", [])), str([f["code"] for f in manifest["findings"]]))
        for run in exp.get("runs", []):
            rc, job_dir = do_inspect(template_path, jobs, policy_path, exp.get("profile"), quiet=True)
            prepare(job_dir, run)
            want = run["expect"]
            paths = JobPaths(job_dir)
            before = sorted(os.listdir(job_dir))
            rc_dry, _ = do_execute(job_dir, policy_path, None, dry_run=True, quiet=True)
            record(name, f"{run['name']}: dry run writes nothing", sorted(os.listdir(job_dir)) == before)
            rc, report = do_execute(job_dir, policy_path, None, quiet=True)
            got_result = report.result if report else "refused"
            record(name, f"{run['name']}: result {want['result']}", got_result == want["result"], f"got {got_result} rc={rc}")
            if report is None:
                continue
            if want["result"] == "failed":
                details = " ".join(c.detail for c in report.checks if c.outcome != "passed")
                for needle in want.get("errors_contain", []):
                    record(name, f"{run['name']}: error mentions {needle!r}", needle in details, details[:160])
                record(name, f"{run['name']}: no output", not os.path.isdir(paths.output_dir))
                continue
            got_codes = sorted({r.code for r in report.review})
            record(name, f"{run['name']}: review codes {sorted(want.get('review_codes', []))}", got_codes == sorted(want.get("review_codes", [])), f"got {got_codes}")
            files = sorted(os.listdir(paths.output_dir)) if os.path.isdir(paths.output_dir) else []
            docs = [f for f in files if f.endswith(".docx")]
            record(name, f"{run['name']}: one output document", len(docs) == 1 and report.job_id in docs[0], ", ".join(files))
            if not docs:
                continue
            with open(os.path.join(paths.output_dir, docs[0]), "rb") as fh:
                out_bytes = fh.read()
            got_out = output_texts(out_bytes, list(want.get("output_texts", {})), limits)
            for part, texts in want.get("output_texts", {}).items():
                record(name, f"{run['name']}: output texts {part}", got_out.get(part) == texts, f"got {got_out.get(part)}")
            record(name, f"{run['name']}: report validates", models.validate_document(models.to_dict(report), models.Report) == [])
            if run.get("rerun", False):
                rc2, report2 = do_execute(job_dir, policy_path, None, quiet=True)
                with open(os.path.join(paths.output_dir, docs[0]), "rb") as fh:
                    again = fh.read()
                record(name, f"{run['name']}: rerun reproduces the output", rc2 == rc and again == out_bytes and report2 is not None)
                plan = _read_json(paths.plan)
                plan["manifest_sha256"] = "0" * 64
                _write_text(paths.plan, json.dumps(plan, indent=2) + "\n")
                rc3, report3 = do_execute(job_dir, policy_path, None, quiet=True)
                record(name, f"{run['name']}: stale plan fails, previous output kept",
                       rc3 == EXIT_FAILED and report3 is not None and report3.result == "failed"
                       and sorted(os.listdir(paths.output_dir)) == files
                       and len(os.listdir(paths.attempts_dir)) == 3)

    ok = all(r[2] for r in results)
    for fixture, case, passed, detail in results:
        if not passed or not quiet:
            print(f"{'PASS' if passed else 'FAIL':<5} {fixture:<22} {case:<48} {detail}")
    print(f"selftest: {sum(1 for r in results if r[2])}/{len(results)} checks passed; run directory {run_dir}")
    return EXIT_OK if ok else EXIT_FAILED


def cmd_selftest(args: argparse.Namespace) -> int:
    try:
        return do_selftest(args.workdir, args.policy, quiet=not args.verbose)
    except (Refused, OSError) as exc:
        print(f"selftest: failed: {exc}", file=sys.stderr)
        return EXIT_FAILED


def cmd_tests(_args: argparse.Namespace) -> int:
    import unittest

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    tests_dir = os.path.normpath(os.path.join(HERE, "..", "tests"))
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    missing = []
    for mod in ("contract_tests", "component_tests", "package_tests", "namespace_tests"):
        if not os.path.exists(os.path.join(tests_dir, f"{mod}.py")):
            missing.append(mod)
            continue
        suite.addTests(loader.loadTestsFromName(mod))
    if missing:
        # The unit tests are a development artifact and are not part of a distributed skill. `doctor`
        # and `selftest` are the checks that belong with a release, and both are always present. A gate
        # that did not run must not report success (verification.md, principle 4), so this is a failure.
        print(f"tests: failed: {len(missing)} of 4 test module(s) absent ({', '.join(missing)}); "
              f"the unit tests ship with the source tree, not the distributed skill. Run `selftest` instead.",
              file=sys.stderr)
        return EXIT_FAILED
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    print(f"tests: {result.testsRun} run, {len(result.failures)} failed, {len(result.errors)} errors (skill {models.SKILL_VERSION})")
    return EXIT_OK if result.wasSuccessful() else EXIT_FAILED


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    _encoding_safe_console()
    parser = argparse.ArgumentParser(prog="run_job.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="check the runtime")
    p.add_argument("--workdir")
    p.add_argument("--policy", default=POLICY_DEFAULT)
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("inspect", help="snapshot the template and write manifest.json + plan.draft.json")
    p.add_argument("--template", required=True)
    p.add_argument("--workdir", required=True)
    p.add_argument("--profile", help="per-template profile JSON merged over references/profile.default.json")
    p.add_argument("--policy", default=POLICY_DEFAULT)
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("execute", help="compile, apply, verify, report; rerunnable")
    p.add_argument("--job", required=True)
    p.add_argument("--dry-run", action="store_true", help="print the change list and review items; write nothing")
    p.add_argument("--out", help="also copy the output document and report here")
    p.add_argument("--policy", default=POLICY_DEFAULT)
    p.set_defaults(func=cmd_execute)

    p = sub.add_parser("selftest", help="run the bundled fixtures end to end under <workdir>/selftest/")
    p.add_argument("--workdir", required=True)
    p.add_argument("--policy", default=POLICY_DEFAULT)
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_selftest)

    p = sub.add_parser("tests", help="run the unit test modules (source tree only; fails when absent)")
    p.set_defaults(func=cmd_tests)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
