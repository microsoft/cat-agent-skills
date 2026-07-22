#!/usr/bin/env python3
"""Run the installed Classic Text Adventure smoke suite and report actionable issues."""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

# An installed skill must not create files beneath its own immutable bundle.
sys.dont_write_bytecode = True

import checkpoint
import render
import runner
import runtime_adapter


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
CASES_PATH = SCRIPT_DIR / "smoke_cases.json"


class SmokeFailure(AssertionError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_cases(path: Path = CASES_PATH) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    _assert(document.get("schema") == 1, "unsupported smoke-case schema")
    _assert(isinstance(document.get("suite"), str), "suite must be a string")
    _assert(isinstance(document.get("version"), str), "version must be a string")
    cases = document.get("cases")
    _assert(isinstance(cases, list) and cases, "cases must be a non-empty array")
    ids = []
    for case in cases:
        _assert(isinstance(case, dict), "every case must be an object")
        _assert(isinstance(case.get("id"), str), "every case needs an id")
        _assert(isinstance(case.get("title"), str), "every case needs a title")
        _assert(isinstance(case.get("timeout_seconds"), (int, float)), "every case needs a timeout")
        _assert(isinstance(case.get("prerequisites"), list), "every case needs prerequisites")
        _assert(isinstance(case.get("expected_result"), str), "every case needs an expected result")
        ids.append(case["id"])
    _assert(len(ids) == len(set(ids)), "case ids must be unique")
    return document


def case_bundle_manifests(_: Path, __: dict[str, Any]) -> dict[str, Any]:
    license_dir = SKILL_ROOT / "references" / "licenses"
    checked = 0
    bundle_paths: set[str] = set()
    third_party_paths: set[str] = set()
    for name in ("THIRD_PARTY_MANIFEST.json", "BUNDLE_MANIFEST.json"):
        manifest = json.loads((license_dir / name).read_text(encoding="utf-8"))
        _assert(manifest.get("schema") == 1, f"{name} schema mismatch")
        for item in manifest.get("files", []):
            path = SKILL_ROOT / item["path"]
            _assert(path.is_file(), f"manifest file missing: {item['path']}")
            _assert(_sha256(path) == item["sha256"], f"manifest hash mismatch: {item['path']}")
            checked += 1
            if name == "BUNDLE_MANIFEST.json":
                bundle_paths.add(item["path"])
            else:
                third_party_paths.add(item["path"])
    actual_bundle = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in SKILL_ROOT.rglob("*")
        if path.is_file()
        and path.relative_to(SKILL_ROOT).as_posix()
        not in {"metadata.json", "README.md", "references/licenses/BUNDLE_MANIFEST.json"}
    }
    missing = sorted(bundle_paths - actual_bundle)
    unexpected = sorted(actual_bundle - bundle_paths)
    _assert(
        not missing and not unexpected,
        f"bundle inventory mismatch; missing={missing!r}; unexpected={unexpected!r}",
    )
    expected_third_party = {
        relative for relative in actual_bundle if relative.startswith("scripts/runtime/adventure/")
    } | {"assets/fonts/JetBrainsMono-Regular.ttf"}
    third_missing = sorted(expected_third_party - third_party_paths)
    third_unexpected = sorted(third_party_paths - expected_third_party)
    _assert(
        not third_missing and not third_unexpected,
        f"third-party inventory mismatch; missing={third_missing!r}; unexpected={third_unexpected!r}",
    )
    return {"files_checked": checked}


def case_runtime_imports(_: Path, __: dict[str, Any]) -> dict[str, Any]:
    from PIL import __version__ as pillow_version

    font = SKILL_ROOT / "assets" / "fonts" / "JetBrainsMono-Regular.ttf"
    _assert(font.is_file(), "bundled font is missing")
    _assert(font.stat().st_size > 100_000, "bundled font is unexpectedly small")
    _assert(runtime_adapter.RUNTIME_ID == "adventure-1.7", "unexpected runtime version")
    return {"pillow": pillow_version, "font_sha256": _sha256(font)}


def case_startup_gameplay(_: Path, case: dict[str, Any]) -> dict[str, Any]:
    seed = 424242
    outputs = {
        "start": runtime_adapter.start(seed)[1].text,
        "no": runtime_adapter.step(runtime_adapter.canonical_state(seed), "no")[1].text,
        "yes": runtime_adapter.step(runtime_adapter.canonical_state(seed), "yes")[1].text,
        "enter": runtime_adapter.step(runtime_adapter.canonical_state(seed, ["no"]), "enter")[1].text,
        "inventory": runtime_adapter.step(runtime_adapter.canonical_state(seed, ["no", "enter"]), "inventory")[1].text,
        "invalid": runtime_adapter.step(runtime_adapter.canonical_state(seed, ["no", "enter"]), "xyzzyz")[1].text,
        "quit": runtime_adapter.step(runtime_adapter.canonical_state(seed, ["no", "enter"]), "quit")[1].text,
    }
    actual = {name: hashlib.sha256(text.encode("utf-8")).hexdigest() for name, text in outputs.items()}
    _assert(actual == case["output_sha256"], "one or more golden gameplay outputs changed")
    return {"output_sha256": actual}


def _invoke_runner(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT_DIR / "runner.py"), "--state-root", str(root)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        timeout=5,
        env=environment,
        check=False,
    )
    response = json.loads(completed.stdout)
    _assert(completed.returncode == 0 and response.get("ok"), f"runner invocation failed: {response.get('error')}")
    return response


def case_deterministic_replay(root: Path, __: dict[str, Any]) -> dict[str, Any]:
    final = {}
    for session in ("replay-a", "replay-b"):
        sequence = _invoke_runner(
            root,
            {"protocol": 1, "action": "start", "session_id": session, "request_id": "start", "seed": 99},
        )["sequence"]
        for index, raw_input in enumerate(("no", "enter", "get lamp", "out"), start=1):
            final[session] = _invoke_runner(
                root,
                {
                    "protocol": 1,
                    "action": "step",
                    "session_id": session,
                    "request_id": f"turn-{index}",
                    "base_sequence": sequence,
                    "raw_input": raw_input,
                },
            )
            sequence = final[session]["sequence"]
        status = _invoke_runner(
            root,
            {"protocol": 1, "action": "status", "session_id": session, "request_id": "status"},
        )
        _assert(status["runtime"]["location"] == 1, "separate runner invocation restored the wrong room")
    comparable = ("sequence", "text", "finished", "scene_key")
    _assert(
        all(final["replay-a"][key] == final["replay-b"][key] for key in comparable),
        "separate runner invocations did not replay deterministically",
    )
    return {"sequence": final["replay-a"]["sequence"], "scene_key": final["replay-a"]["scene_key"]}


def case_idempotency_conflict(root: Path, _: dict[str, Any]) -> dict[str, Any]:
    first = runner.handle_request(
        {"protocol": 1, "action": "start", "session_id": "idem", "request_id": "start", "seed": 7}, root
    )
    request = {
        "action": "step",
        "protocol": 1,
        "session_id": "idem",
        "request_id": "turn-1",
        "base_sequence": first["sequence"],
        "raw_input": "no",
    }
    committed = runner.handle_request(request, root)
    replayed = runner.handle_request(request, root)
    _assert(committed["sequence"] == 1 and replayed["replayed"], "duplicate request was not replayed")
    stale = dict(request, request_id="turn-2", raw_input="look")
    try:
        runner.handle_request(stale, root)
    except checkpoint.SequenceConflict:
        pass
    else:
        raise SmokeFailure("stale base_sequence was accepted")
    return {"sequence": committed["sequence"]}


def case_session_isolation(root: Path, _: dict[str, Any]) -> dict[str, Any]:
    for session, seed in (("alpha", 1), ("beta", 2)):
        runner.handle_request(
            {"protocol": 1, "action": "start", "session_id": session, "request_id": "start", "seed": seed}, root
        )
    beta_path = runner._session_paths(root, "beta")["checkpoint"]
    beta_before = _sha256(beta_path)
    alpha = runner.handle_request(
        {"protocol": 1, "action": "step", "session_id": "alpha", "request_id": "a1", "base_sequence": 0, "raw_input": "no"},
        root,
    )
    beta = runner.handle_request({"protocol": 1, "action": "status", "session_id": "beta", "request_id": "status"}, root)
    _assert(alpha["sequence"] == 1 and beta["sequence"] == 0, "sessions influenced one another")
    _assert(_sha256(beta_path) == beta_before, "advancing alpha altered beta's checkpoint")
    alpha_checkpoint = checkpoint.load_checkpoint(runner._session_paths(root, "alpha")["checkpoint"])
    beta_checkpoint = checkpoint.load_checkpoint(beta_path)
    _assert(alpha_checkpoint["transcript"] == ["no"] and beta_checkpoint["transcript"] == [], "transcripts crossed sessions")
    _assert(
        all("alpha" in path for path in alpha.get("image_paths", []))
        and all("beta" in path for path in beta.get("image_paths", [])),
        "rendered image paths crossed sessions",
    )
    return {"alpha_sequence": 1, "beta_sequence": 0, "isolated_images": True}


def case_save_confinement(root: Path, _: dict[str, Any]) -> dict[str, Any]:
    state = runtime_adapter.canonical_state(12, ["no"])
    traversal_target = (root / ".." / ".." / "must-not-exist.sav").resolve()
    absolute_target = (root.parent / "absolute-save-target.sav").resolve()
    _assert(not traversal_target.exists() and not absolute_target.exists(), "save sentinel path already exists")
    previous_cwd = Path.cwd()
    try:
        os.chdir(root)
        traversal = runtime_adapter.step(state, "save ../../must-not-exist.sav")[1]
        absolute = runtime_adapter.step(state, f"save {absolute_target}")[1]
    finally:
        os.chdir(previous_cwd)
    _assert(traversal.text == "GAME SAVED\n" and absolute.text == "GAME SAVED\n", "save output changed")
    created = [str(path) for path in (traversal_target, absolute_target) if path.exists()]
    for path in (traversal_target, absolute_target):
        if path.exists():
            path.unlink()
    _assert(not created, f"save command wrote requested path(s): {created!r}")
    return {"confined": True}


def case_render_determinism(root: Path, _: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    font = SKILL_ROOT / "assets" / "fonts" / "JetBrainsMono-Regular.ttf"
    one, meta_one = render.render_png("A deterministic cave.\n", "cave", font)
    two, meta_two = render.render_png("A deterministic cave.\n", "cave", font)
    _assert(one == two, "PNG file bytes differ across renders")
    _assert(meta_one["pixel_sha256"] == meta_two["pixel_sha256"], "rendered pixels differ")
    output = root / "render.png"
    output.write_bytes(one)
    with Image.open(output) as image:
        _assert(image.size == (1280, 960), "render dimensions changed")
        _assert(image.mode == "RGB", "render mode changed")
    return {"file_sha256": meta_one["file_sha256"], "pixel_sha256": meta_one["pixel_sha256"]}


def case_journal_recovery(root: Path, _: dict[str, Any]) -> dict[str, Any]:
    started = runner.handle_request(
        {"protocol": 1, "action": "start", "session_id": "recover", "request_id": "start", "seed": 33}, root
    )
    paths = runner._session_paths(root, "recover")
    committed = checkpoint.load_checkpoint(paths["checkpoint"])
    journal = {
        "schema": checkpoint.JOURNAL_SCHEMA,
        "protocol": 1,
        "runtime": runtime_adapter.RUNTIME_ID,
        "session_id": "recover",
        "base_sequence": started["sequence"],
        "pre_turn_transcript": committed["transcript"],
        "request_id": "interrupted-turn",
        "input_hash": "simulated-interruption",
        "raw_input": "no",
    }
    checkpoint.write_journal(paths["journal"], journal)
    recovered = runner.handle_request({"protocol": 1, "action": "status", "session_id": "recover", "request_id": "status"}, root)
    _assert(recovered["sequence"] == 1, "pending turn was not committed")
    _assert(not paths["journal"].exists(), "pending journal was not cleared")
    return {"sequence": recovered["sequence"]}


CASE_RUNNERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "CTA-SMOKE-BUNDLE-001": case_bundle_manifests,
    "CTA-SMOKE-RUNTIME-002": case_runtime_imports,
    "CTA-SMOKE-GAMEPLAY-003": case_startup_gameplay,
    "CTA-SMOKE-REPLAY-004": case_deterministic_replay,
    "CTA-SMOKE-IDEMPOTENCY-005": case_idempotency_conflict,
    "CTA-SMOKE-ISOLATION-006": case_session_isolation,
    "CTA-SMOKE-SAVE-007": case_save_confinement,
    "CTA-SMOKE-RENDER-008": case_render_determinism,
    "CTA-SMOKE-RECOVERY-009": case_journal_recovery,
}


def _case_worker(case_id: str, case_root: str, case: dict[str, Any], queue: Any) -> None:
    try:
        details = CASE_RUNNERS[case_id](Path(case_root), case)
        queue.put({"ok": True, "details": details})
    except BaseException as exc:
        queue.put(
            {
                "ok": False,
                "message": (str(exc) or exc.__class__.__name__).replace("\r", " ").replace("\n", " ")[:512],
                "type": exc.__class__.__name__,
            }
        )


def run_suite(
    state_root: Path,
    selected: set[str] | None = None,
    keep_temp: bool = False,
    timeout_seconds: float = 30.0,
    isolate_cases: bool = True,
) -> tuple[dict[str, Any], int]:
    definition = load_cases()
    state_root.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix="classic-adventure-smoke-", dir=state_root))
    results = []
    issues = []
    started_at = time.time()
    try:
        for index, case in enumerate(definition["cases"]):
            case_id = case["id"]
            if selected is not None and case_id not in selected:
                continue
            print(f"[{index + 1}/{len(definition['cases'])}] {case_id}", file=sys.stderr)
            case_root = temp / case_id
            case_root.mkdir()
            case_started = time.perf_counter()
            try:
                remaining = timeout_seconds - (time.time() - started_at)
                if remaining <= 0:
                    raise SmokeFailure(f"suite exceeded {timeout_seconds:g}-second timeout")
                budget = min(float(case["timeout_seconds"]), remaining)
                if isolate_cases:
                    context = multiprocessing.get_context("spawn")
                    queue = context.Queue()
                    process = context.Process(target=_case_worker, args=(case_id, str(case_root), case, queue))
                    process.start()
                    process.join(budget)
                    if process.is_alive():
                        process.terminate()
                        process.join(2)
                        raise SmokeFailure(f"case exceeded {budget:g}-second timeout and was terminated")
                    if queue.empty():
                        raise SmokeFailure(f"case process exited with code {process.exitcode} without a result")
                    outcome = queue.get()
                    queue.close()
                    if not outcome["ok"]:
                        raise SmokeFailure(f"{outcome['type']}: {outcome['message']}")
                    details = outcome["details"]
                else:
                    details = CASE_RUNNERS[case_id](case_root, case)
                    if time.perf_counter() - case_started > budget:
                        raise SmokeFailure(f"case exceeded {budget:g}-second timeout")
                status = "passed"
            except Exception as exc:
                status = "failed"
                details = {}
                issues.append(
                    {
                        "code": case_id,
                        "case": case_id,
                        "message": str(exc) or exc.__class__.__name__,
                        "type": exc.__class__.__name__,
                    }
                )
            results.append(
                {
                    "id": case_id,
                    "title": case["title"],
                    "status": status,
                    "duration_ms": round((time.perf_counter() - case_started) * 1000, 3),
                    "details": details,
                }
            )
    finally:
        if not keep_temp:
            shutil.rmtree(temp, ignore_errors=True)
    failed = sum(result["status"] == "failed" for result in results)
    try:
        from PIL import __version__ as pillow_version
    except ImportError:
        pillow_version = "unavailable"
    report = {
        "schema_version": 1,
        "suite": definition["suite"],
        "suite_version": definition["version"],
        "overall_status": "pass" if failed == 0 else "fail",
        "summary": {"total": len(results), "passed": len(results) - failed, "failed": failed, "skipped": 0},
        "environment": {
            "python": platform.python_version(),
            "pillow": pillow_version,
            "platform": platform.platform(),
        },
        "duration_ms": round((time.time() - started_at) * 1000, 3),
        "cases": results,
        "issues": issues,
    }
    return report, 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--case", action="append", dest="cases", help="run only this case id (repeatable)")
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json-summary", action="store_true", help="emit the compact JSON summary (default behavior)")
    args = parser.parse_args(argv)
    try:
        definition = load_cases()
        known = {case["id"] for case in definition["cases"]}
        selected = set(args.cases) if args.cases else None
        unknown = sorted((selected or set()) - known)
        if unknown:
            raise SmokeFailure(f"unknown case id(s): {', '.join(unknown)}")
        report, code = run_suite(args.state_root.resolve(), selected, args.keep_temp, args.timeout)
        checkpoint.atomic_write_json(args.report.resolve(), report)
        print(json.dumps({"status": report["overall_status"], **report["summary"], "report": str(args.report)}))
        return code
    except Exception as exc:
        issue = {
            "code": "CTA-SMOKE-HARNESS-000",
            "case": None,
            "message": (str(exc) or exc.__class__.__name__).replace("\r", " ").replace("\n", " ")[:512],
            "type": exc.__class__.__name__,
        }
        error_report = {
            "schema_version": 1,
            "suite": "classic-text-adventure-smoke",
            "suite_version": "1.0.0",
            "overall_status": "error",
            "environment": {"python": platform.python_version(), "pillow": "unknown", "platform": platform.platform()},
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
            "duration_ms": 0,
            "cases": [],
            "issues": [issue],
        }
        try:
            checkpoint.atomic_write_json(args.report.resolve(), error_report)
        except Exception:
            pass
        print(json.dumps({"status": "error", "error": issue["message"], "report": str(args.report)}))
        return 2


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
