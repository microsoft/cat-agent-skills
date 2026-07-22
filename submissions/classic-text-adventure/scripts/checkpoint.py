#!/usr/bin/env python3
"""Hashed checkpoints, atomic writes, locking, and pending-turn recovery data."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator


CHECKPOINT_SCHEMA = 1
JOURNAL_SCHEMA = 1


class CheckpointError(RuntimeError):
    """Raised when persisted state is invalid or cannot be recovered safely."""


class SequenceConflict(CheckpointError):
    """Raised when a turn is based on a stale sequence number."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _with_hash(payload: dict[str, Any]) -> dict[str, Any]:
    document = dict(payload)
    document["document_hash"] = sha256_json(payload)
    return document


def verify_document(document: dict[str, Any], *, kind: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise CheckpointError(f"{kind} must be a JSON object")
    payload = dict(document)
    actual = payload.pop("document_hash", None)
    expected = sha256_json(payload)
    if actual != expected:
        raise CheckpointError(f"{kind} hash mismatch")
    return payload


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointError(f"cannot read {path.name}: {exc}") from exc


def atomic_write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical_json_bytes(document))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        os.chmod(path, 0o600)
        if hasattr(os, "O_DIRECTORY"):
            directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp_name)
        raise


def write_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    if payload.get("schema") != CHECKPOINT_SCHEMA:
        raise CheckpointError("unsupported checkpoint schema")
    atomic_write_json(path, _with_hash(payload))


def load_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = verify_document(read_json(path), kind="checkpoint")
    if payload.get("schema") != CHECKPOINT_SCHEMA:
        raise CheckpointError("unsupported checkpoint schema")
    return payload


def write_journal(path: Path, payload: dict[str, Any]) -> None:
    if payload.get("schema") != JOURNAL_SCHEMA:
        raise CheckpointError("unsupported journal schema")
    atomic_write_json(path, _with_hash(payload))


def load_journal(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = verify_document(read_json(path), kind="journal")
    if payload.get("schema") != JOURNAL_SCHEMA:
        raise CheckpointError("unsupported journal schema")
    return payload


def remove_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


@contextlib.contextmanager
def session_lock(path: Path, timeout_seconds: float = 10.0) -> Iterator[None]:
    """Acquire an advisory cross-platform lock without external dependencies."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    os.chmod(path, 0o600)
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            try:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0, os.SEEK_END)
                    if handle.tell() == 0:
                        handle.write(b"0")
                        handle.flush()
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (BlockingIOError, OSError):
                if time.monotonic() >= deadline:
                    raise CheckpointError("timed out acquiring session lock")
                time.sleep(0.05)
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
