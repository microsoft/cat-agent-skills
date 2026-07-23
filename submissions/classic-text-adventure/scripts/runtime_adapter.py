#!/usr/bin/env python3
"""Deterministic, filesystem-confined adapter for the bundled Adventure runtime."""

from __future__ import annotations

import io
import json
import re
import secrets
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = SCRIPT_DIR / "runtime"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from adventure import load_advent_dat  # noqa: E402
from adventure.game import Game  # noqa: E402


MAX_COMMAND_BYTES = 16_384
RUNTIME_ID = "adventure-1.7"
SCHEMA_VERSION = 1


class AdapterError(ValueError):
    """Raised for invalid state or player input."""


class EmptyInput(AdapterError):
    pass


class InputTooLarge(AdapterError):
    pass


@dataclass(frozen=True)
class RuntimeResult:
    text: str
    finished: bool
    scene_key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_state(seed: int, transcript: Iterable[str] = ()) -> bytes:
    """Return the only persisted runtime representation accepted by this adapter."""
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**64:
        raise AdapterError("seed must be an unsigned 64-bit integer")
    commands = list(transcript)
    for command in commands:
        validate_command(command)
    document = {
        "schema": SCHEMA_VERSION,
        "runtime": RUNTIME_ID,
        "seed": seed,
        "transcript": commands,
    }
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decode_state(state: bytes) -> dict[str, Any]:
    if not isinstance(state, bytes):
        raise AdapterError("state must be canonical UTF-8 JSON bytes")
    try:
        document = json.loads(state.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterError("state is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise AdapterError("state must contain an object")
    if document.get("schema") != SCHEMA_VERSION or document.get("runtime") != RUNTIME_ID:
        raise AdapterError("unsupported runtime state")
    expected = canonical_state(document.get("seed"), document.get("transcript", ()))
    if state != expected:
        raise AdapterError("state is not canonical")
    return document


def validate_command(command: str) -> None:
    if not isinstance(command, str):
        raise AdapterError("command must be a string")
    if not command.strip():
        raise EmptyInput("command must not be blank")
    if len(command.encode("utf-8")) > MAX_COMMAND_BYTES:
        raise InputTooLarge(f"command exceeds {MAX_COMMAND_BYTES} UTF-8 bytes")


def tokenize(command: str) -> list[str]:
    """Match the traditional upstream command-line parser exactly."""
    validate_command(command)
    return re.findall(r"\w+", command.lower())


def _new_game(seed: int) -> Game:
    game = Game(seed)
    load_advent_dat(game)
    game.start()
    return game


def _scene_key(game: Game) -> str:
    if game.is_finished or getattr(game, "is_closing", False) or getattr(game, "is_closed", False):
        return "endgame"
    location = getattr(game, "loc", None)
    if location is None:
        return "surface"
    dwarves = getattr(game, "dwarves", ())
    pirate = getattr(game, "pirate", None)
    active_threat = any(
        getattr(dwarf, "room", None) is location and getattr(dwarf, "has_seen_adventurer", False)
        for dwarf in dwarves
    ) or (pirate is not None and getattr(pirate, "room", None) is location)
    if getattr(game, "is_dead", False) or active_threat or getattr(game, "could_fall_in_pit", False):
        return "danger"
    if getattr(game, "is_dark", False):
        return "darkness"
    return "surface" if getattr(location, "is_aboveground", False) else "cave"


def _execute(game: Game, command: str) -> str:
    words = tokenize(command)
    if not words:
        return ""
    if words[0] == "save" and len(words) > 1:
        sink = io.BytesIO()
        game.output = ""
        game.t_suspend(words[0], sink)
        return game.output
    return game.do_command(words)


def _replay(state: bytes) -> tuple[Game, dict[str, Any]]:
    document = decode_state(state)
    game = _new_game(document["seed"])
    for command in document["transcript"]:
        _execute(game, command)
    return game, document


def start(seed: int | None = None) -> tuple[bytes, RuntimeResult]:
    if seed is None:
        seed = secrets.randbits(64)
    state = canonical_state(seed)
    game = _new_game(seed)
    return state, RuntimeResult(game.output, game.is_finished, _scene_key(game))


def step(state: bytes, raw_input: str) -> tuple[bytes, RuntimeResult]:
    validate_command(raw_input)
    game, document = _replay(state)
    text = _execute(game, raw_input)
    next_state = canonical_state(document["seed"], [*document["transcript"], raw_input])
    return next_state, RuntimeResult(text, game.is_finished, _scene_key(game))


def inspect_state(state: bytes) -> dict[str, Any]:
    game, _ = _replay(state)
    location = getattr(game, "loc", None)
    return {
        "finished": game.is_finished,
        "scene_key": _scene_key(game),
        "turns": getattr(game, "turns", 0),
        "location": getattr(location, "n", None),
    }
