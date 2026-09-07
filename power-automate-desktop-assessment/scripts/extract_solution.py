from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
from uuid import uuid4
import zipfile


DEFAULT_MAX_MEMBERS = 50_000
DEFAULT_MAX_UNCOMPRESSED_BYTES = 1024**3
DEFAULT_MAX_MEMBER_BYTES = 256 * 1024**2
COPY_CHUNK_BYTES = 1024**2


def extract_solution(
    zip_path: Path,
    output_dir: Path,
    *,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
) -> dict[str, object]:
    zip_path = zip_path.resolve()
    output_dir = output_dir.resolve()

    if not zip_path.is_file():
        raise FileNotFoundError(f"Solution ZIP not found: {zip_path}")
    if output_dir == Path(output_dir.anchor):
        raise ValueError("Refusing to use a filesystem root as the extraction directory")
    if output_dir == zip_path or output_dir in zip_path.parents:
        raise ValueError("Extraction directory must not contain the source ZIP")
    if output_dir.exists():
        raise FileExistsError(
            f"Extraction directory already exists; use a new run path: {output_dir}"
        )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = output_dir.with_name(
        f".{output_dir.name}.tmp-{uuid4().hex}"
    )
    staging_dir.mkdir()

    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = archive.infolist()
            if len(members) > max_members:
                raise ValueError(
                    f"Archive has {len(members)} entries; limit is {max_members}"
                )

            planned_bytes = sum(member.file_size for member in members)
            if planned_bytes > max_uncompressed_bytes:
                raise ValueError(
                    "Archive expands beyond the configured safety limit "
                    f"({planned_bytes} > {max_uncompressed_bytes} bytes)"
                )

            validated_members: list[tuple[zipfile.ZipInfo, PurePosixPath]] = []
            staging_root = staging_dir.resolve()
            for member in members:
                relative = PurePosixPath(member.filename.replace("\\", "/"))
                if not relative.parts:
                    continue
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError(
                        f"Unsafe archive member: {member.filename!r}"
                    )
                if any(":" in part for part in relative.parts):
                    raise ValueError(
                        f"Unsafe drive-qualified archive member: "
                        f"{member.filename!r}"
                    )
                destination = staging_root.joinpath(*relative.parts).resolve()
                if (
                    destination != staging_root
                    and staging_root not in destination.parents
                ):
                    raise ValueError(
                        f"Archive member escapes the extraction directory: "
                        f"{member.filename!r}"
                    )
                if member.file_size > max_member_bytes:
                    raise ValueError(
                        f"Archive member exceeds the per-file safety limit: "
                        f"{member.filename!r}"
                    )
                validated_members.append((member, relative))

            extracted_bytes = 0
            for member, relative in validated_members:
                destination = staging_dir.joinpath(*relative.parts)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                member_bytes = 0
                with archive.open(member) as source, destination.open("xb") as target:
                    while chunk := source.read(COPY_CHUNK_BYTES):
                        member_bytes += len(chunk)
                        extracted_bytes += len(chunk)
                        if member_bytes > max_member_bytes:
                            raise ValueError(
                                f"Archive member exceeds the per-file safety limit: "
                                f"{member.filename!r}"
                            )
                        if extracted_bytes > max_uncompressed_bytes:
                            raise ValueError(
                                "Archive exceeds the total extraction safety limit"
                            )
                        target.write(chunk)

        staging_dir.replace(output_dir)
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise

    files = [path for path in output_dir.rglob("*") if path.is_file()]
    return {
        "extractPath": str(output_dir),
        "fileCount": len(files),
        "uncompressedBytes": sum(path.stat().st_size for path in files),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely extract an exported Power Platform solution ZIP."
    )
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--max-members", type=int, default=DEFAULT_MAX_MEMBERS)
    parser.add_argument(
        "--max-uncompressed-bytes",
        type=int,
        default=DEFAULT_MAX_UNCOMPRESSED_BYTES,
    )
    parser.add_argument(
        "--max-member-bytes",
        type=int,
        default=DEFAULT_MAX_MEMBER_BYTES,
    )
    args = parser.parse_args()

    result = extract_solution(
        args.zip_path,
        args.output_dir,
        max_members=args.max_members,
        max_uncompressed_bytes=args.max_uncompressed_bytes,
        max_member_bytes=args.max_member_bytes,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
