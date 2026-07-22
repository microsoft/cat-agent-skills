#!/usr/bin/env python3
"""One-shot JSON runner for deterministic, resumable Adventure turns."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from checkpoint import (
    CHECKPOINT_SCHEMA,
    JOURNAL_SCHEMA,
    CheckpointError,
    SequenceConflict,
    load_checkpoint,
    load_journal,
    remove_file,
    session_lock,
    sha256_json,
    write_checkpoint,
    write_journal,
)
from runtime_adapter import (
    RUNTIME_ID,
    AdapterError,
    EmptyInput,
    InputTooLarge,
    canonical_state,
    decode_state,
    inspect_state,
    start,
    step,
    validate_command,
)


PROTOCOL = 1
SESSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
REQUEST_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
class RequestError(ValueError):
    pass


class GameFinished(RequestError):
    pass


def _require_string(request: dict[str, Any], key: str, pattern: re.Pattern[str]) -> str:
    value = request.get(key)
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise RequestError(f"invalid {key}")
    return value


def _session_paths(state_root: Path, session_id: str) -> dict[str, Path]:
    root = state_root.resolve()
    session = (root / session_id).resolve()
    if session.parent != root:
        raise RequestError("session_id escapes state root")
    return {
        "session": session,
        "checkpoint": session / "checkpoint.json",
        "journal": session / "pending-turn.json",
        "lock": session / ".lock",
    }


def _request_hash(action: str, request: dict[str, Any]) -> str:
    material = {key: value for key, value in request.items() if key != "request_id"}
    material["action"] = action
    return sha256_json(material)


def _state_bytes(checkpoint: dict[str, Any]) -> bytes:
    if checkpoint.get("runtime") != RUNTIME_ID:
        raise CheckpointError("unsupported checkpoint runtime")
    if not isinstance(checkpoint.get("transcript"), list):
        raise CheckpointError("checkpoint transcript must be an array")
    return canonical_state(checkpoint["seed"], checkpoint["transcript"])


def _response(checkpoint: dict[str, Any], request_id: str, *, replayed: bool = False) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL,
        "ok": True,
        "session_id": checkpoint["session_id"],
        "request_id": request_id,
        "sequence": checkpoint["sequence"],
        "text": checkpoint["text"],
        "finished": checkpoint["finished"],
        "scene_key": checkpoint["scene_key"],
        "replayed": replayed,
    }


def _commit_step(checkpoint: dict[str, Any], journal: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    if checkpoint["sequence"] != journal["base_sequence"]:
        raise SequenceConflict("pending turn no longer matches checkpoint")
    if (
        journal.get("protocol") != PROTOCOL
        or journal.get("runtime") != RUNTIME_ID
        or journal.get("session_id") != checkpoint["session_id"]
        or journal.get("pre_turn_transcript") != checkpoint["transcript"]
    ):
        raise CheckpointError("pending journal does not match checkpoint")
    next_state, result = step(_state_bytes(checkpoint), journal["raw_input"])
    state_document = decode_state(next_state)
    next_checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "protocol": PROTOCOL,
        "runtime": RUNTIME_ID,
        "session_id": checkpoint["session_id"],
        "sequence": checkpoint["sequence"] + 1,
        "seed": state_document["seed"],
        "transcript": state_document["transcript"],
        "text": result.text,
        "finished": result.finished,
        "scene_key": result.scene_key,
        "last_request": {
            "request_id": journal["request_id"],
            "input_hash": journal["input_hash"],
        },
    }
    write_checkpoint(paths["checkpoint"], next_checkpoint)
    remove_file(paths["journal"])
    return next_checkpoint


def _recover(checkpoint: dict[str, Any] | None, paths: dict[str, Path]) -> dict[str, Any] | None:
    if checkpoint is not None:
        if checkpoint.get("protocol") != PROTOCOL or checkpoint.get("session_id") != paths["session"].name:
            raise CheckpointError("checkpoint identity mismatch")
        _state_bytes(checkpoint)
    journal = load_journal(paths["journal"])
    if journal is None:
        return checkpoint
    if checkpoint is None:
        raise CheckpointError("pending turn exists without a checkpoint")
    last = checkpoint.get("last_request") or {}
    if last.get("request_id") == journal.get("request_id"):
        if last.get("input_hash") != journal.get("input_hash"):
            raise CheckpointError("committed request hash conflicts with journal")
        remove_file(paths["journal"])
        return checkpoint
    return _commit_step(checkpoint, journal, paths)


def _handle_start(
    request: dict[str, Any], paths: dict[str, Path], request_id: str
) -> dict[str, Any]:
    checkpoint = _recover(load_checkpoint(paths["checkpoint"]), paths)
    input_hash = _request_hash("start", request)
    if checkpoint is not None:
        last = checkpoint.get("last_request") or {}
        if last.get("request_id") == request_id and last.get("input_hash") != input_hash:
            raise RequestError("request_id was already used with different input")
        if checkpoint.get("finished"):
            raise GameFinished("session is finished; reset before starting a new game")
        return _response(checkpoint, request_id, replayed=True)
    seed = request.get("seed")
    state, result = start(seed)
    state_document = decode_state(state)
    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "protocol": PROTOCOL,
        "runtime": RUNTIME_ID,
        "session_id": request["session_id"],
        "sequence": 0,
        "seed": state_document["seed"],
        "transcript": [],
        "text": result.text,
        "finished": result.finished,
        "scene_key": result.scene_key,
        "last_request": {"request_id": request_id, "input_hash": input_hash},
    }
    write_checkpoint(paths["checkpoint"], checkpoint)
    return _response(checkpoint, request_id)


def _handle_step(request: dict[str, Any], paths: dict[str, Path], request_id: str) -> dict[str, Any]:
    checkpoint = _recover(load_checkpoint(paths["checkpoint"]), paths)
    if checkpoint is None:
        raise RequestError("session does not exist; start it first")
    if checkpoint.get("finished"):
        raise GameFinished("session is finished; reset before sending another command")
    input_hash = _request_hash("step", request)
    last = checkpoint.get("last_request") or {}
    if last.get("request_id") == request_id:
        if last.get("input_hash") != input_hash:
            raise RequestError("request_id was already used with different input")
        return _response(checkpoint, request_id, replayed=True)
    base_sequence = request.get("base_sequence")
    if isinstance(base_sequence, bool) or not isinstance(base_sequence, int):
        raise RequestError("base_sequence must be an integer")
    if base_sequence != checkpoint["sequence"]:
        raise SequenceConflict(
            f"base_sequence {base_sequence} does not match current sequence {checkpoint['sequence']}"
        )
    raw_input = request.get("raw_input")
    if not isinstance(raw_input, str):
        raise RequestError("raw_input must be a string")
    validate_command(raw_input)
    journal = {
        "schema": JOURNAL_SCHEMA,
        "protocol": PROTOCOL,
        "runtime": RUNTIME_ID,
        "session_id": request["session_id"],
        "base_sequence": base_sequence,
        "pre_turn_transcript": checkpoint["transcript"],
        "request_id": request_id,
        "input_hash": input_hash,
        "raw_input": raw_input,
    }
    write_journal(paths["journal"], journal)
    return _response(_commit_step(checkpoint, journal, paths), request_id)


def _handle_status(paths: dict[str, Path], request_id: str) -> dict[str, Any]:
    checkpoint = _recover(load_checkpoint(paths["checkpoint"]), paths)
    if checkpoint is None:
        return {"protocol": PROTOCOL, "ok": True, "request_id": request_id, "exists": False}
    runtime = inspect_state(_state_bytes(checkpoint))
    return {**_response(checkpoint, request_id), "exists": True, "runtime": runtime}


def _handle_reset(paths: dict[str, Path], request_id: str) -> dict[str, Any]:
    existed = load_checkpoint(paths["checkpoint"]) is not None
    remove_file(paths["checkpoint"])
    remove_file(paths["journal"])
    return {"protocol": PROTOCOL, "ok": True, "request_id": request_id, "reset": existed}


def handle_request(request: dict[str, Any], state_root: Path) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise RequestError("request must be a JSON object")
    if request.get("protocol") != PROTOCOL:
        raise RequestError("protocol must be 1")
    action = request.get("action")
    if action not in {"start", "step", "status", "reset"}:
        raise RequestError("action must be start, step, status, or reset")
    session_id = _require_string(request, "session_id", SESSION_PATTERN)
    request_id = _require_string(request, "request_id", REQUEST_PATTERN)
    paths = _session_paths(state_root, session_id)
    paths["session"].mkdir(parents=True, exist_ok=True, mode=0o700)
    with session_lock(paths["lock"]):
        if action == "status":
            return _handle_status(paths, request_id)
        if action == "reset":
            return _handle_reset(paths, request_id)
        if action == "start":
            return _handle_start(request, paths, request_id)
        return _handle_step(request, paths, request_id)


def _error_response(exc: Exception, request_id: str | None = None) -> dict[str, Any]:
    if isinstance(exc, EmptyInput):
        code = "empty_input"
    elif isinstance(exc, InputTooLarge):
        code = "input_too_large"
    elif isinstance(exc, json.JSONDecodeError):
        code = "malformed_json"
    elif isinstance(exc, SequenceConflict):
        code = "sequence_conflict"
    elif isinstance(exc, GameFinished):
        code = "game_finished"
    elif isinstance(exc, (RequestError, AdapterError)):
        code = "invalid_request"
    elif isinstance(exc, CheckpointError):
        code = "state_error"
    else:
        code = "internal_error"
    message = str(exc).replace("\r", " ").replace("\n", " ")[:512]
    if code == "internal_error":
        message = "unexpected runner failure"
    response: dict[str, Any] = {"protocol": PROTOCOL, "ok": False, "error": {"code": code, "message": message}}
    if request_id is not None and REQUEST_PATTERN.fullmatch(request_id):
        response["request_id"] = request_id
    return response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-root",
        type=Path,
        default=Path(os.environ.get("CLASSIC_TEXT_ADVENTURE_STATE_ROOT", ".classic-text-adventure-state")),
    )
    args = parser.parse_args(argv)
    request: Any = None
    try:
        request = json.load(sys.stdin)
        response = handle_request(request, args.state_root)
        code = 0
    except Exception as exc:
        request_id = request.get("request_id") if isinstance(request, dict) else None
        response = _error_response(exc, request_id)
        code = 1
    json.dump(response, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
