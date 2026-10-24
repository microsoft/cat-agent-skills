#!/usr/bin/env python3
"""Normalize VTT, SRT, or plain-text meeting content into timestamped segments."""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
from typing import Any


TIMING = re.compile(
    r"^\s*(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{3})\s*-->\s*"
    r"(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{3})"
)
VOICE = re.compile(r"<v(?:\.[^ >]+)?\s+([^>]+)>", re.IGNORECASE)
TAGS = re.compile(r"<[^>]+>")
SPACES = re.compile(r"\s+")


def parse_time(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Invalid transcript timestamp: {value}")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def clean_text(lines: list[str]) -> tuple[str, str]:
    joined = " ".join(line.strip() for line in lines if line.strip())
    voice = VOICE.search(joined)
    speaker = html.unescape(voice.group(1)).strip() if voice else ""
    text = TAGS.sub("", joined)
    text = SPACES.sub(" ", html.unescape(text)).strip()
    return text, speaker


def parse_timed(text: str) -> list[dict[str, Any]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    segments: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        match = TIMING.match(lines[index])
        if not match:
            index += 1
            continue
        start = parse_time(match.group("start"))
        end = parse_time(match.group("end"))
        index += 1
        body: list[str] = []
        while index < len(lines) and lines[index].strip():
            if TIMING.match(lines[index]):
                break
            body.append(lines[index])
            index += 1
        value, speaker = clean_text(body)
        if value:
            segments.append(
                {
                    "index": len(segments) + 1,
                    "startSeconds": round(start, 3),
                    "endSeconds": round(end, 3),
                    "speaker": speaker,
                    "text": value,
                    "timed": True,
                }
            )
    return segments


def parse_plain(text: str) -> list[dict[str, Any]]:
    paragraphs = [
        SPACES.sub(" ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]
    return [
        {
            "index": index,
            "startSeconds": None,
            "endSeconds": None,
            "speaker": "",
            "text": paragraph,
            "timed": False,
        }
        for index, paragraph in enumerate(paragraphs, 1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--source-label", default="")
    args = parser.parse_args()

    source = args.input.read_text(encoding="utf-8-sig", errors="replace")
    suffix = args.input.suffix.lower()
    segments = parse_timed(source) if suffix in {".vtt", ".srt"} else parse_plain(source)
    timed = sum(1 for segment in segments if segment["timed"])
    speakers = sorted(
        {segment["speaker"] for segment in segments if segment["speaker"]}
    )
    payload = {
        "schemaVersion": "1.0",
        "sourceLabel": args.source_label or args.input.stem,
        "format": suffix.lstrip(".") or "text",
        "segmentCount": len(segments),
        "timedSegmentCount": timed,
        "speakers": speakers,
        "segments": segments,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "success",
                "output": str(args.output),
                "segments": len(segments),
                "timedSegments": timed,
                "speakers": len(speakers),
            }
        )
    )


if __name__ == "__main__":
    main()
