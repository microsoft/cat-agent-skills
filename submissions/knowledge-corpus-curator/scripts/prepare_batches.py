#!/usr/bin/env python3
"""Safely combine uploaded ZIP batches into one analysis corpus."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uploads", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Optional metadata JSON to exclude from the staged corpus.",
    )
    parser.add_argument("--max-entries", type=int, default=50000)
    parser.add_argument(
        "--max-extracted-bytes",
        type=int,
        default=2_000_000_000,
        help="Maximum total uncompressed bytes across all ZIP batches.",
    )
    parser.add_argument("--max-compression-ratio", type=float, default=200.0)
    return parser.parse_args()


def safe_name(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in value
    ).strip("-")
    return cleaned or "batch"


def validate_member(
    info: zipfile.ZipInfo,
    max_compression_ratio: float,
) -> PurePosixPath | None:
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if info.is_dir() or "__MACOSX" in path.parts:
        return None
    if not name or name.startswith("/") or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive path: {info.filename}")
    if ":" in path.parts[0]:
        raise ValueError(f"Drive-qualified archive path: {info.filename}")
    if info.flag_bits & 0x1:
        raise ValueError(f"Encrypted archive entry is unsupported: {info.filename}")
    mode = info.external_attr >> 16
    if mode and stat.S_ISLNK(mode):
        raise ValueError(f"Symbolic link archive entry is unsupported: {info.filename}")
    if info.file_size and not info.compress_size:
        raise ValueError(f"Invalid compressed size for archive entry: {info.filename}")
    if info.compress_size:
        ratio = info.file_size / info.compress_size
        if ratio > max_compression_ratio:
            raise ValueError(
                f"Compression ratio exceeds the safety limit: {info.filename}"
            )
    return path


def extract_batch(
    archive: Path,
    destination: Path,
    remaining_entries: int,
    remaining_bytes: int,
    max_compression_ratio: float,
) -> tuple[int, int, list[str]]:
    extracted: list[str] = []
    used_bytes = 0
    used_entries = 0
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            relative = validate_member(info, max_compression_ratio)
            if relative is None:
                continue
            used_entries += 1
            used_bytes += info.file_size
            if used_entries > remaining_entries:
                raise ValueError("ZIP batches exceed the maximum entry count.")
            if used_bytes > remaining_bytes:
                raise ValueError("ZIP batches exceed the maximum extracted size.")
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(info) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            extracted.append(str(target.relative_to(destination)).replace("\\", "/"))
    return used_entries, used_bytes, extracted


def main() -> int:
    args = parse_args()
    if not args.uploads.is_dir():
        raise SystemExit(f"Uploads directory does not exist: {args.uploads}")
    if args.output.exists():
        if not args.output.is_dir():
            raise SystemExit(
                f"Combined corpus output path is not a directory: {args.output}"
            )
        if any(args.output.iterdir()):
            raise SystemExit(
                f"Combined corpus directory must be empty before staging: {args.output}"
            )
    args.output.mkdir(parents=True, exist_ok=True)

    archives = sorted(
        path for path in args.uploads.iterdir() if path.is_file() and path.suffix.lower() == ".zip"
    )
    metadata_path = args.metadata.resolve() if args.metadata else None
    if metadata_path and not metadata_path.is_file():
        raise SystemExit(f"Metadata file does not exist: {args.metadata}")
    loose_files = sorted(
        path
        for path in args.uploads.iterdir()
        if path.is_file()
        and path.suffix.lower() != ".zip"
        and path.resolve() != metadata_path
    )
    if not archives and not loose_files:
        raise SystemExit(f"No uploaded ZIPs or files found under {args.uploads}")

    manifest: dict[str, Any] = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceDirectory": str(args.uploads),
        "combinedCorpus": str(args.output),
        "batches": [],
        "totalFiles": 0,
        "totalExtractedBytes": 0,
    }
    total_entries = 0
    total_bytes = 0

    for index, archive in enumerate(archives, start=1):
        batch_name = f"batch-{index:03d}-{safe_name(archive.stem)}"
        destination = args.output / batch_name
        destination.mkdir()
        try:
            entries, extracted_bytes, extracted = extract_batch(
                archive,
                destination,
                args.max_entries - total_entries,
                args.max_extracted_bytes - total_bytes,
                args.max_compression_ratio,
            )
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            try:
                shutil.rmtree(destination)
            except OSError as cleanup_exc:
                raise SystemExit(
                    f"Cannot prepare {archive.name}: {exc}. "
                    f"Also could not remove partial batch directory "
                    f"{destination}: {cleanup_exc}"
                ) from cleanup_exc
            raise SystemExit(f"Cannot prepare {archive.name}: {exc}") from exc
        total_entries += entries
        total_bytes += extracted_bytes
        manifest["batches"].append(
            {
                "batch": batch_name,
                "source": archive.name,
                "fileCount": entries,
                "extractedBytes": extracted_bytes,
                "files": extracted,
            }
        )

    if loose_files:
        loose_entries = len(loose_files)
        loose_bytes = sum(path.stat().st_size for path in loose_files)
        if total_entries + loose_entries > args.max_entries:
            raise SystemExit("Uploaded files exceed the maximum entry count.")
        if total_bytes + loose_bytes > args.max_extracted_bytes:
            raise SystemExit("Uploaded files exceed the maximum staged size.")
        destination = args.output / "loose-files"
        destination.mkdir()
        copied: list[str] = []
        try:
            for source in loose_files:
                target = destination / source.name
                shutil.copy2(source, target)
                copied.append(source.name)
        except OSError as exc:
            try:
                shutil.rmtree(destination)
            except OSError as cleanup_exc:
                raise SystemExit(
                    f"Cannot stage loose upload {source.name}: {exc}. "
                    f"Also could not remove partial loose-file directory "
                    f"{destination}: {cleanup_exc}"
                ) from cleanup_exc
            raise SystemExit(f"Cannot stage loose upload {source.name}: {exc}") from exc
        total_entries += loose_entries
        total_bytes += loose_bytes
        manifest["batches"].append(
            {
                "batch": "loose-files",
                "source": "individual uploads",
                "fileCount": loose_entries,
                "extractedBytes": loose_bytes,
                "files": copied,
            }
        )

    manifest["totalFiles"] = total_entries
    manifest["totalExtractedBytes"] = total_bytes
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
