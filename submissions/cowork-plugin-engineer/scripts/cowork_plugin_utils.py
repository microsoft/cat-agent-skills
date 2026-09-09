"""Shared validation and file-handling helpers for Cowork plugin scripts."""

from __future__ import annotations

import binascii
import json
import math
import re
import shutil
import stat
import struct
import subprocess
import tempfile
import uuid
import zipfile
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import urlparse


ATK_VERSION = "1.1.15"
MAX_PNG_BYTES = 5 * 1024 * 1024
MAX_OUTLINE_COMPRESSED_BYTES = 1024 * 1024
PLACEHOLDER_PATTERN = re.compile(
    r"(REPLACE|PLACEHOLDER|YOUR[_-]|<[^>]+>|\{\{.+\}\})", re.IGNORECASE
)
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
FRONTMATTER_PATTERN = re.compile(
    r"\A---\r?\n(?P<frontmatter>.*?)\r?\n---(?:\r?\n|$)", re.DOTALL
)
YAML_NUMBER_PATTERN = re.compile(
    r"""
    [+-]?(?:
        0b[01_]+
        |0o[0-7_]+
        |0x[0-9a-f_]+
        |[0-9][0-9_]*
        |[0-9][0-9_]*\.[0-9_]*(?:e[+-]?[0-9]+)?
        |\.[0-9][0-9_]*(?:e[+-]?[0-9]+)?
        |[0-9][0-9_]*e[+-]?[0-9]+
        |\.inf
        |\.nan
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
YAML_DATE_PATTERN = re.compile(
    r"\d{4}-\d{1,2}-\d{1,2}"
    r"(?:[Tt ]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?"
    r"(?:[ \t]*(?:Z|[+-]\d{1,2}(?::?\d{2})?))?)?"
)


class CoworkPluginError(ValueError):
    """Raised when a Cowork plugin violates a required invariant."""


@dataclass(frozen=True)
class ValidationResult:
    project_path: str
    manifest_path: str
    manifest_version: str
    version: str
    skills: int
    connectors: int
    package_checked: bool
    status: str = "Passed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2))


def read_json(path: Path, label: str | None = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CoworkPluginError(
            f"{label or path.name} is not valid JSON: {exc}"
        ) from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def get_property(obj: Any, name: str) -> Any:
    return obj.get(name) if isinstance(obj, dict) else None


def required_text(obj: Any, name: str, label: str) -> str:
    value = get_property(obj, name)
    if not isinstance(value, str) or not value.strip():
        raise CoworkPluginError(f"{label} is required.")
    return value


def as_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CoworkPluginError(f"{label} must be an object.")
    return value


def as_list(value: Any, label: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise CoworkPluginError(f"{label} must be an array.")
    return value


def validate_https(value: str, label: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise CoworkPluginError(f"{label} must use HTTPS: {value}")


def normalize_manifest_path(relative_path: str, label: str) -> PurePosixPath:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise CoworkPluginError(f"{label} is required.")
    normalized = relative_path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if (
        normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or "\x00" in normalized
    ):
        raise CoworkPluginError(
            f"{label} must be package-relative: {relative_path}"
        )
    parts = normalized.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise CoworkPluginError(
            f"{label} escapes or ambiguously addresses the package root: "
            f"{relative_path}"
        )
    return PurePosixPath(*parts)


def resolve_in_root(root: Path, relative_path: str, label: str) -> Path:
    posix_path = normalize_manifest_path(relative_path, label)
    resolved_root = root.resolve(strict=True)
    candidate = resolved_root.joinpath(*posix_path.parts).resolve(strict=False)
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise CoworkPluginError(
            f"{label} escapes the package root: {relative_path}"
        ) from exc
    return candidate


def is_oauth_placeholder(value: str, connector_id: str | None = None) -> bool:
    if not isinstance(value, str) or not value.strip():
        return True
    return bool(PLACEHOLDER_PATTERN.search(value)) or bool(
        connector_id
        and value.lower().endswith(f"-{connector_id}-auth".lower())
    )


def _frontmatter_field(
    frontmatter: str, name: str, skill_file: Path
) -> str:
    lines = frontmatter.splitlines()
    matches: list[tuple[int, str]] = []
    pattern = re.compile(rf"^{re.escape(name)}:\s*(.*)$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            matches.append((index, match.group(1).strip()))
    if len(matches) != 1:
        raise CoworkPluginError(
            f"SKILL.md must define exactly one {name} field: {skill_file}"
        )

    index, raw_value = matches[0]
    block_match = re.fullmatch(r"([|>])[-+]?", raw_value)
    if block_match:
        block_lines: list[str] = []
        for line in lines[index + 1 :]:
            if line and not line[0].isspace():
                break
            block_lines.append(line)
        nonempty_indents = [
            len(line) - len(line.lstrip())
            for line in block_lines
            if line.strip()
        ]
        if not nonempty_indents:
            raise CoworkPluginError(
                f"SKILL.md {name} block is empty: {skill_file}"
            )
        indent = min(nonempty_indents)
        values = [
            line[indent:] if len(line) >= indent else "" for line in block_lines
        ]
        if block_match.group(1) == "|":
            return "\n".join(values).strip()
        paragraphs: list[str] = []
        current: list[str] = []
        for line in values:
            if line.strip():
                current.append(line.strip())
            elif current:
                paragraphs.append(" ".join(current))
                current = []
        if current:
            paragraphs.append(" ".join(current))
        return "\n".join(paragraphs).strip()
    if raw_value.startswith(("|", ">")):
        raise CoworkPluginError(
            f"SKILL.md {name} has unsupported block YAML: {skill_file}"
        )

    if raw_value.startswith('"') or raw_value.endswith('"'):
        if not (raw_value.startswith('"') and raw_value.endswith('"')):
            raise CoworkPluginError(
                f"SKILL.md {name} has invalid double-quoted YAML: {skill_file}"
            )
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise CoworkPluginError(
                f"SKILL.md {name} has invalid double-quoted YAML: {skill_file}"
            ) from exc
        if not isinstance(value, str):
            raise CoworkPluginError(
                f"SKILL.md {name} must be text: {skill_file}"
            )
        return value

    if raw_value.startswith("'") or raw_value.endswith("'"):
        if not (raw_value.startswith("'") and raw_value.endswith("'")):
            raise CoworkPluginError(
                f"SKILL.md {name} has invalid single-quoted YAML: {skill_file}"
            )
        inner = raw_value[1:-1]
        index = 0
        while index < len(inner):
            if inner[index] != "'":
                index += 1
                continue
            if index + 1 >= len(inner) or inner[index + 1] != "'":
                raise CoworkPluginError(
                    f"SKILL.md {name} has invalid single-quoted YAML: "
                    f"{skill_file}"
                )
            index += 2
        return inner.replace("''", "'")

    value = re.sub(r"\s+#.*$", "", raw_value).strip()
    if (
        value.startswith(
            ("[", "]", "{", "}", "!", "&", "*", "#", "%", ",", "@", "`")
        )
        or re.match(r"^[-?:](?:\s|$)", value)
        or re.search(r":(?:\s|$)", value)
    ):
        raise CoworkPluginError(
            f"SKILL.md {name} must be a plain or quoted string: {skill_file}"
        )
    if (
        value.casefold() in {"true", "false", "null", "~"}
        or YAML_NUMBER_PATTERN.fullmatch(value)
        or YAML_DATE_PATTERN.fullmatch(value)
    ):
        raise CoworkPluginError(
            f"SKILL.md {name} must be a string, not a typed YAML scalar: "
            f"{skill_file}"
        )
    return value


def read_skill_metadata(skill_file: Path) -> tuple[str, str]:
    try:
        content = skill_file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise CoworkPluginError(f"Cannot read skill: {skill_file}: {exc}") from exc
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        raise CoworkPluginError(
            f"SKILL.md must start with YAML frontmatter: {skill_file}"
        )
    frontmatter = match.group("frontmatter")
    name = _frontmatter_field(frontmatter, "name", skill_file)
    description = _frontmatter_field(frontmatter, "description", skill_file)
    if not name.strip() or not description.strip():
        raise CoworkPluginError(
            f"Skill must define non-empty name and description: {skill_file}"
        )
    return name, description


def _read_png_chunks(path: Path) -> tuple[dict[str, int], bytes, bytes, bytes]:
    try:
        size = path.stat().st_size
        if size > MAX_PNG_BYTES:
            raise CoworkPluginError(
                f"PNG exceeds the {MAX_PNG_BYTES} byte safety limit: {path}"
            )
        data = path.read_bytes()
    except OSError as exc:
        raise CoworkPluginError(f"Cannot read PNG: {path}: {exc}") from exc
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        raise CoworkPluginError(f"File is not a PNG: {path}")

    offset = len(signature)
    ihdr: dict[str, int] | None = None
    palette = b""
    transparency = b""
    compressed = bytearray()
    found_iend = False
    seen_idat = False
    idat_ended = False
    while offset < len(data):
        if len(data) - offset < 12:
            raise CoworkPluginError(f"PNG contains a truncated chunk: {path}")
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        chunk_end = data_end + 4
        if chunk_end > len(data):
            raise CoworkPluginError(f"PNG contains an invalid chunk: {path}")
        chunk_data = data[data_start:data_end]
        expected_crc = struct.unpack_from(">I", data, data_end)[0]
        actual_crc = binascii.crc32(chunk_type)
        actual_crc = binascii.crc32(chunk_data, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            type_name = chunk_type.decode("ascii", errors="replace")
            raise CoworkPluginError(
                f"PNG chunk {type_name} has an invalid CRC: {path}"
            )
        if any(
            not (65 <= byte <= 90 or 97 <= byte <= 122)
            for byte in chunk_type
        ) or not 65 <= chunk_type[2] <= 90:
            raise CoworkPluginError(f"PNG contains an invalid chunk type: {path}")
        try:
            type_name = chunk_type.decode("ascii")
        except UnicodeDecodeError as exc:
            raise CoworkPluginError(
                f"PNG contains an invalid chunk type: {path}"
            ) from exc

        if ihdr is None and type_name != "IHDR":
            raise CoworkPluginError(f"PNG must begin with an IHDR chunk: {path}")
        if type_name == "IHDR":
            if ihdr is not None or offset != 8 or length != 13:
                raise CoworkPluginError(f"PNG has an invalid IHDR chunk: {path}")
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filtering,
                interlace,
            ) = struct.unpack(">IIBBBBB", chunk_data)
            if width == 0 or height == 0:
                raise CoworkPluginError(f"PNG dimensions must be non-zero: {path}")
            if compression != 0 or filtering != 0:
                raise CoworkPluginError(
                    f"PNG uses unsupported compression or filtering: {path}"
                )
            ihdr = {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "interlace": interlace,
            }
        elif type_name == "PLTE":
            if (
                seen_idat
                or palette
                or length == 0
                or length % 3
                or length > 768
                or ihdr["color_type"] in (0, 4)
            ):
                raise CoworkPluginError(f"PNG has an invalid PLTE chunk: {path}")
            palette = chunk_data
        elif type_name == "tRNS":
            if (
                seen_idat
                or transparency
                or (ihdr["color_type"] == 3 and not palette)
            ):
                raise CoworkPluginError(f"PNG has an invalid tRNS chunk: {path}")
            transparency = chunk_data
        elif type_name == "IDAT":
            if idat_ended:
                raise CoworkPluginError(
                    f"PNG has non-consecutive IDAT chunks: {path}"
                )
            seen_idat = True
            compressed.extend(chunk_data)
            if len(compressed) > MAX_OUTLINE_COMPRESSED_BYTES:
                raise CoworkPluginError(
                    "outline.png IDAT data exceeds the compressed-size "
                    f"safety limit: {path}"
                )
        elif type_name == "IEND":
            if length != 0 or not seen_idat:
                raise CoworkPluginError(f"PNG has an invalid IEND chunk: {path}")
            found_iend = True
        elif 65 <= chunk_type[0] <= 90:
            raise CoworkPluginError(
                f"PNG contains unsupported critical chunk {type_name}: {path}"
            )
        elif seen_idat:
            idat_ended = True

        offset = chunk_end
        if found_iend:
            if offset != len(data):
                raise CoworkPluginError(
                    f"PNG contains data after its IEND chunk: {path}"
                )
            break

    if ihdr is None:
        raise CoworkPluginError(f"PNG is missing its IHDR chunk: {path}")
    if not found_iend:
        raise CoworkPluginError(f"PNG is missing its IEND chunk: {path}")
    return ihdr, palette, transparency, bytes(compressed)


def get_png_dimensions(path: Path) -> tuple[int, int]:
    ihdr, _, _, _ = _read_png_chunks(path)
    return ihdr["width"], ihdr["height"]


def _png_sample(row: bytes | bytearray, index: int, bit_depth: int) -> int:
    if bit_depth == 8:
        return row[index]
    if bit_depth == 16:
        return (row[index * 2] << 8) | row[index * 2 + 1]
    if bit_depth in (1, 2, 4):
        samples_per_byte = 8 // bit_depth
        byte_index = index // samples_per_byte
        sample_in_byte = index % samples_per_byte
        shift = 8 - bit_depth - sample_in_byte * bit_depth
        return (row[byte_index] >> shift) & ((1 << bit_depth) - 1)
    raise CoworkPluginError(f"Unsupported PNG bit depth: {bit_depth}")


def _paeth(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    distances = (
        abs(estimate - left),
        abs(estimate - up),
        abs(estimate - upper_left),
    )
    if distances[0] <= distances[1] and distances[0] <= distances[2]:
        return left
    if distances[1] <= distances[2]:
        return up
    return upper_left


def _bounded_zlib_decompress(compressed: bytes, expected_bytes: int) -> bytes:
    decompressor = zlib.decompressobj()
    try:
        output = decompressor.decompress(compressed, expected_bytes + 1)
        if len(output) <= expected_bytes:
            output += decompressor.flush(expected_bytes + 1 - len(output))
    except zlib.error as exc:
        raise CoworkPluginError(
            f"outline.png has invalid zlib data: {exc}"
        ) from exc
    if len(output) != expected_bytes:
        raise CoworkPluginError(
            "outline.png has unexpected decompressed pixel data."
        )
    if (
        not decompressor.eof
        or decompressor.unconsumed_tail
        or decompressor.unused_data
    ):
        raise CoworkPluginError(
            "outline.png IDAT contains an incomplete or trailing zlib stream."
        )
    return output


def assert_outline_png_pixels(path: Path) -> None:
    ihdr, palette, transparency, compressed = _read_png_chunks(path)
    width = ihdr["width"]
    height = ihdr["height"]
    bit_depth = ihdr["bit_depth"]
    color_type = ihdr["color_type"]
    interlace = ihdr["interlace"]
    if (width, height) != (32, 32):
        raise CoworkPluginError(
            f"outline.png must be 32x32; found {width}x{height}."
        )
    if interlace != 0:
        raise CoworkPluginError(
            "outline.png must use a non-interlaced PNG encoding for pixel "
            "validation."
        )

    channels_by_type = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    depths_by_type = {
        0: (1, 2, 4, 8, 16),
        2: (8, 16),
        3: (1, 2, 4, 8),
        4: (8, 16),
        6: (8, 16),
    }
    if color_type not in channels_by_type:
        raise CoworkPluginError(
            f"outline.png uses unsupported PNG color type {color_type}."
        )
    if bit_depth not in depths_by_type[color_type]:
        raise CoworkPluginError(
            "outline.png uses unsupported bit depth "
            f"{bit_depth} for color type {color_type}."
        )
    if color_type == 3 and (
        not palette or len(palette) % 3 or len(palette) > 768
    ):
        raise CoworkPluginError(
            "outline.png has an invalid or missing PNG palette."
        )
    if color_type == 3 and len(transparency) > len(palette) // 3:
        raise CoworkPluginError(
            "outline.png transparency exceeds its PNG palette."
        )
    if color_type == 0 and len(transparency) not in (0, 2):
        raise CoworkPluginError("outline.png has invalid grayscale transparency.")
    if color_type == 2 and len(transparency) not in (0, 6):
        raise CoworkPluginError("outline.png has invalid truecolor transparency.")
    if color_type in (4, 6) and transparency:
        raise CoworkPluginError(
            "outline.png cannot use tRNS with an alpha color type."
        )

    channels = channels_by_type[color_type]
    row_bytes = math.ceil(width * channels * bit_depth / 8)
    filter_bytes_per_pixel = max(1, math.ceil(channels * bit_depth / 8))
    expected_bytes = (row_bytes + 1) * height
    scanlines = _bounded_zlib_decompress(compressed, expected_bytes)

    reconstructed = bytearray(row_bytes * height)
    for y in range(height):
        source_offset = y * (row_bytes + 1)
        filter_type = scanlines[source_offset]
        for x in range(row_bytes):
            raw = scanlines[source_offset + 1 + x]
            target_offset = y * row_bytes + x
            left = (
                reconstructed[target_offset - filter_bytes_per_pixel]
                if x >= filter_bytes_per_pixel
                else 0
            )
            up = (
                reconstructed[target_offset - row_bytes] if y > 0 else 0
            )
            upper_left = (
                reconstructed[
                    target_offset - row_bytes - filter_bytes_per_pixel
                ]
                if y > 0 and x >= filter_bytes_per_pixel
                else 0
            )
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                predictor = _paeth(left, up, upper_left)
            else:
                raise CoworkPluginError(
                    f"outline.png uses invalid PNG filter {filter_type}."
                )
            reconstructed[target_offset] = (raw + predictor) & 0xFF

    channel_max = 65535 if bit_depth == 16 else (1 << bit_depth) - 1
    transparent_pixels = 0
    visible_pixels = 0
    for y in range(height):
        row = reconstructed[y * row_bytes : (y + 1) * row_bytes]
        for x in range(width):
            sample_index = x * channels
            alpha = channel_max
            pixel_max = channel_max
            if color_type == 0:
                gray = _png_sample(row, sample_index, bit_depth)
                red = green = blue = gray
                if transparency:
                    transparent_gray = (transparency[0] << 8) | transparency[1]
                    if gray == transparent_gray:
                        alpha = 0
            elif color_type == 2:
                red = _png_sample(row, sample_index, bit_depth)
                green = _png_sample(row, sample_index + 1, bit_depth)
                blue = _png_sample(row, sample_index + 2, bit_depth)
                if transparency:
                    transparent_rgb = (
                        (transparency[0] << 8) | transparency[1],
                        (transparency[2] << 8) | transparency[3],
                        (transparency[4] << 8) | transparency[5],
                    )
                    if (red, green, blue) == transparent_rgb:
                        alpha = 0
            elif color_type == 3:
                palette_index = _png_sample(row, sample_index, bit_depth)
                palette_offset = palette_index * 3
                if palette_offset + 2 >= len(palette):
                    raise CoworkPluginError(
                        "outline.png references missing palette index "
                        f"{palette_index}."
                    )
                pixel_max = 255
                red, green, blue = palette[
                    palette_offset : palette_offset + 3
                ]
                alpha = (
                    transparency[palette_index]
                    if palette_index < len(transparency)
                    else 255
                )
            elif color_type == 4:
                gray = _png_sample(row, sample_index, bit_depth)
                alpha = _png_sample(row, sample_index + 1, bit_depth)
                red = green = blue = gray
            else:
                red = _png_sample(row, sample_index, bit_depth)
                green = _png_sample(row, sample_index + 1, bit_depth)
                blue = _png_sample(row, sample_index + 2, bit_depth)
                alpha = _png_sample(row, sample_index + 3, bit_depth)

            if alpha == 0:
                transparent_pixels += 1
            else:
                visible_pixels += 1
                if (red, green, blue) != (pixel_max, pixel_max, pixel_max):
                    rgba = tuple(
                        round(sample * 255 / pixel_max)
                        for sample in (red, green, blue)
                    ) + (round(alpha * 255 / pixel_max),)
                    raise CoworkPluginError(
                        "outline.png contains a non-white visible pixel at "
                        f"({x},{y}): RGBA{rgba}."
                    )
    if not transparent_pixels or not visible_pixels:
        raise CoworkPluginError(
            "outline.png must contain both transparent and visible white pixels."
        )


def _iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def validate_project(
    project_path: str | Path,
    package_path: str | Path | None = None,
    allow_oauth_placeholder: bool = False,
    *,
    package_root_only: bool = False,
) -> ValidationResult:
    project = Path(project_path).expanduser().resolve(strict=True)
    if not project.is_dir():
        raise CoworkPluginError(f"Project path is not a directory: {project}")
    app_package = project / "appPackage"
    package_root = (
        app_package
        if not package_root_only and app_package.is_dir()
        else project
    )
    manifest_path = package_root / "manifest.json"
    if not manifest_path.is_file():
        raise CoworkPluginError(f"manifest.json was not found at {manifest_path}")
    manifest = as_object(read_json(manifest_path, "manifest.json"), "manifest")

    manifest_version = required_text(
        manifest, "manifestVersion", "manifestVersion"
    )
    schema = required_text(manifest, "$schema", "$schema")
    if not re.search(rf"/v{re.escape(manifest_version)}/", schema):
        raise CoworkPluginError(
            f"$schema and manifestVersion do not match: {schema} / "
            f"{manifest_version}"
        )
    version = required_text(manifest, "version", "version")
    if not SEMVER_PATTERN.fullmatch(version):
        raise CoworkPluginError(
            f"version must use three numeric parts: {version}"
        )
    manifest_id = required_text(manifest, "id", "id")
    try:
        parsed_id = uuid.UUID(manifest_id)
    except ValueError as exc:
        raise CoworkPluginError(
            f"id must be a non-empty GUID: {manifest_id}"
        ) from exc
    if parsed_id.int == 0:
        raise CoworkPluginError(f"id must be a non-empty GUID: {manifest_id}")

    developer = as_object(get_property(manifest, "developer"), "developer")
    required_text(developer, "name", "developer.name")
    for url_name in ("websiteUrl", "privacyUrl", "termsOfUseUrl"):
        value = required_text(developer, url_name, f"developer.{url_name}")
        validate_https(value, f"developer.{url_name}")

    icons = as_object(get_property(manifest, "icons"), "icons")
    color_reference = required_text(icons, "color", "icons.color")
    outline_reference = required_text(icons, "outline", "icons.outline")
    color_path = resolve_in_root(package_root, color_reference, "icons.color")
    outline_path = resolve_in_root(
        package_root, outline_reference, "icons.outline"
    )
    for icon_path in (color_path, outline_path):
        if not icon_path.is_file():
            raise CoworkPluginError(f"Icon is missing: {icon_path}")
    color_size = get_png_dimensions(color_path)
    outline_size = get_png_dimensions(outline_path)
    if color_size != (192, 192):
        raise CoworkPluginError(
            f"color.png must be 192x192; found {color_size[0]}x{color_size[1]}."
        )
    if outline_size != (32, 32):
        raise CoworkPluginError(
            "outline.png must be 32x32; found "
            f"{outline_size[0]}x{outline_size[1]}."
        )
    assert_outline_png_pixels(outline_path)

    skills = as_list(get_property(manifest, "agentSkills"), "agentSkills")
    connectors = as_list(
        get_property(manifest, "agentConnectors"), "agentConnectors"
    )
    if not skills and not connectors:
        raise CoworkPluginError(
            "At least one agentSkills or agentConnectors entry is required."
        )
    if len(skills) > 20:
        raise CoworkPluginError(
            f"A maximum of 20 registered skills is supported; found {len(skills)}."
        )

    skill_names: set[str] = set()
    for skill_value in skills:
        skill = as_object(skill_value, "agentSkills entry")
        folder = required_text(skill, "folder", "agentSkills.folder")
        skill_folder = resolve_in_root(
            package_root, folder, "agentSkills.folder"
        )
        if not skill_folder.is_dir():
            raise CoworkPluginError(f"Skill folder is missing: {folder}")
        skill_file = skill_folder / "SKILL.md"
        if not skill_file.is_file():
            raise CoworkPluginError(
                f"Registered skill is missing SKILL.md: {folder}"
            )
        nested_skills = [
            path
            for path in skill_folder.rglob("SKILL.md")
            if path.resolve() != skill_file.resolve()
        ]
        if nested_skills:
            raise CoworkPluginError(
                "Nested SKILL.md files are not valid companion documents: "
                + ", ".join(str(path) for path in nested_skills)
            )
        skill_name, skill_description = read_skill_metadata(skill_file)
        if not skill_description.strip():
            raise CoworkPluginError(
                f"Skill description is required: {skill_file}"
            )
        if not SKILL_NAME_PATTERN.fullmatch(skill_name):
            raise CoworkPluginError(
                f"Skill name must be lowercase kebab-case: {skill_name}"
            )
        if skill_name != skill_folder.name:
            raise CoworkPluginError(
                f"Skill name '{skill_name}' must match folder "
                f"'{skill_folder.name}'."
            )
        normalized_name = skill_name.casefold()
        if normalized_name in skill_names:
            raise CoworkPluginError(f"Duplicate skill name: {skill_name}")
        skill_names.add(normalized_name)

        companions = [
            path
            for path in _iter_files(skill_folder)
            if path.resolve() != skill_file.resolve()
        ]
        if len(companions) > 20:
            raise CoworkPluginError(
                f"Skill '{skill_name}' has {len(companions)} companion files; "
                "maximum is 20."
            )
        companion_bytes = 0
        for companion in companions:
            size = companion.stat().st_size
            if size > 5 * 1024 * 1024:
                raise CoworkPluginError(
                    f"Companion file exceeds 5 MB: {companion}"
                )
            companion_bytes += size
        if companion_bytes > 10 * 1024 * 1024:
            raise CoworkPluginError(
                f"Skill '{skill_name}' companion files exceed 10 MB total."
            )

    connector_ids: set[str] = set()
    for connector_value in connectors:
        connector = as_object(connector_value, "agentConnectors entry")
        connector_id = required_text(connector, "id", "agentConnectors.id")
        normalized_id = connector_id.casefold()
        if normalized_id in connector_ids:
            raise CoworkPluginError(f"Duplicate connector ID: {connector_id}")
        connector_ids.add(normalized_id)
        required_text(
            connector, "displayName", f"connector '{connector_id}' displayName"
        )
        tool_source = as_object(
            get_property(connector, "toolSource"),
            f"connector '{connector_id}' toolSource",
        )
        remote = as_object(
            get_property(tool_source, "remoteMcpServer"),
            f"Connector '{connector_id}' remoteMcpServer",
        )
        server_url = required_text(
            remote, "mcpServerUrl", f"connector '{connector_id}' URL"
        )
        validate_https(server_url, f"Connector '{connector_id}'")

        tool_description = as_object(
            get_property(remote, "mcpToolDescription"),
            f"Connector '{connector_id}' mcpToolDescription",
        )
        tool_file = required_text(
            tool_description,
            "file",
            f"connector '{connector_id}' tool file",
        )
        tool_path = resolve_in_root(
            package_root,
            tool_file,
            f"connector '{connector_id}' tool file",
        )
        if not tool_path.is_file():
            raise CoworkPluginError(
                f"Connector '{connector_id}' tool file is missing: {tool_file}"
            )
        tool_document = as_object(
            read_json(
                tool_path, f"Connector '{connector_id}' tool description"
            ),
            f"Connector '{connector_id}' tool description",
        )
        tools = as_list(get_property(tool_document, "tools"), "tools")
        if not tools:
            raise CoworkPluginError(
                f"Connector '{connector_id}' tool description has no tools."
            )
        tool_names: set[str] = set()
        for tool_value in tools:
            tool = as_object(tool_value, "tool")
            tool_name = required_text(
                tool, "name", f"connector '{connector_id}' tool name"
            )
            required_text(tool, "description", f"tool '{tool_name}' description")
            if get_property(tool, "inputSchema") is None:
                raise CoworkPluginError(
                    f"Tool '{tool_name}' is missing inputSchema."
                )
            normalized_tool_name = tool_name.casefold()
            if normalized_tool_name in tool_names:
                raise CoworkPluginError(
                    f"Duplicate tool name in connector '{connector_id}': "
                    f"{tool_name}"
                )
            tool_names.add(normalized_tool_name)

        authorization = get_property(remote, "authorization")
        if authorization is not None:
            authorization = as_object(
                authorization, f"connector '{connector_id}' authorization"
            )
            auth_type = required_text(
                authorization,
                "type",
                f"connector '{connector_id}' auth type",
            )
            reference_id = get_property(authorization, "referenceId")
            if reference_id is not None and not isinstance(reference_id, str):
                raise CoworkPluginError(
                    f"Connector '{connector_id}' referenceId must be text."
                )
            reference_id = reference_id or ""
            if auth_type == "None":
                if reference_id.strip():
                    raise CoworkPluginError(
                        f"Connector '{connector_id}' uses None and must omit "
                        "referenceId."
                    )
            elif auth_type == "OAuthPluginVault":
                if not reference_id.strip():
                    raise CoworkPluginError(
                        f"Connector '{connector_id}' requires an OAuth "
                        "referenceId."
                    )
                if not allow_oauth_placeholder and is_oauth_placeholder(
                    reference_id, connector_id
                ):
                    raise CoworkPluginError(
                        f"Connector '{connector_id}' has unresolved OAuth "
                        f"placeholder '{reference_id}'."
                    )
            elif auth_type == "ApiKeyPluginVault":
                raise CoworkPluginError(
                    "ApiKeyPluginVault is not currently a deployable Cowork "
                    "connector authentication type."
                )
            elif auth_type == "DynamicClientRegistration":
                raise CoworkPluginError(
                    f"Connector '{connector_id}' must omit authorization to "
                    "use Dynamic Client Registration."
                )
            else:
                raise CoworkPluginError(
                    f"Connector '{connector_id}' uses unsupported auth type "
                    f"'{auth_type}'."
                )

    if package_path is not None:
        package = Path(package_path).expanduser().resolve(strict=True)
        with temporary_workspace(".cowork-plugin-package-") as workspace:
            extraction_root = Path(workspace) / "package"
            inspect_zip(package, extraction_root)
            package_result = validate_project(
                extraction_root,
                allow_oauth_placeholder=allow_oauth_placeholder,
                package_root_only=True,
            )
            packaged_manifest = as_object(
                read_json(
                    extraction_root / "manifest.json",
                    "packaged manifest.json",
                ),
                "packaged manifest",
            )
            for field in ("id", "version", "agentSkills", "agentConnectors"):
                if get_property(packaged_manifest, field) != get_property(
                    manifest, field
                ):
                    raise CoworkPluginError(
                        f"Packaged manifest {field} does not match the "
                        "source project."
                    )
        return ValidationResult(
            project_path=str(project),
            manifest_path=f"{package}!/manifest.json",
            manifest_version=package_result.manifest_version,
            version=package_result.version,
            skills=package_result.skills,
            connectors=package_result.connectors,
            package_checked=True,
        )

    return ValidationResult(
        project_path=str(project),
        manifest_path=str(manifest_path),
        manifest_version=manifest_version,
        version=version,
        skills=len(skills),
        connectors=len(connectors),
        package_checked=False,
    )


def _validate_zip_entry_name(name: str, seen: set[str]) -> str:
    normalized = name.replace("\\", "/")
    if not normalized.strip() or "\x00" in normalized:
        raise CoworkPluginError("ZIP contains an entry with an empty path.")
    if normalized.startswith("/") or ":" in normalized:
        raise CoworkPluginError(f"ZIP contains an absolute path: {normalized}")
    is_directory = normalized.endswith("/")
    path_without_slash = normalized[:-1] if is_directory else normalized
    segments = path_without_slash.split("/")
    if not path_without_slash or any(
        segment in ("", ".", "..") for segment in segments
    ):
        raise CoworkPluginError(
            f"ZIP entry escapes or ambiguously addresses the package root: "
            f"{normalized}"
        )
    if any(segment.endswith((".", " ")) for segment in segments):
        raise CoworkPluginError(
            f"ZIP entry has a Windows-ambiguous path: {normalized}"
        )
    if any(ord(character) < 32 for character in normalized):
        raise CoworkPluginError(
            f"ZIP entry contains a control character: {normalized!r}"
        )
    duplicate_key = path_without_slash.casefold()
    if duplicate_key in seen:
        raise CoworkPluginError(f"ZIP contains a duplicate path: {normalized}")
    seen.add(duplicate_key)
    return normalized


def inspect_zip(
    package_path: str | Path,
    extraction_root: Path,
    max_entries: int = 1000,
    max_extracted_bytes: int = 250 * 1024 * 1024,
) -> tuple[int, int]:
    package = Path(package_path).expanduser().resolve(strict=True)
    if package.suffix.lower() != ".zip":
        raise CoworkPluginError(f"Package must be a ZIP file: {package}")
    if max_entries < 1 or max_entries > 5000:
        raise CoworkPluginError("max_entries must be between 1 and 5000.")
    if (
        max_extracted_bytes < 1024 * 1024
        or max_extracted_bytes > 1024 * 1024 * 1024
    ):
        raise CoworkPluginError(
            "max_extracted_bytes must be between 1 MB and 1 GB."
        )

    seen: set[str] = set()
    validated: list[tuple[zipfile.ZipInfo, str]] = []
    declared_total = 0
    try:
        archive = zipfile.ZipFile(package)
    except (OSError, zipfile.BadZipFile) as exc:
        raise CoworkPluginError(f"Package is not a valid ZIP: {package}") from exc
    with archive:
        entries = archive.infolist()
        if len(entries) > max_entries:
            raise CoworkPluginError(
                f"ZIP contains {len(entries)} entries; maximum is {max_entries}."
            )
        for info in entries:
            normalized = _validate_zip_entry_name(info.filename, seen)
            if info.compress_type not in (
                zipfile.ZIP_STORED,
                zipfile.ZIP_DEFLATED,
            ):
                raise CoworkPluginError(
                    "ZIP entry uses unsupported compression "
                    f"{info.compress_type}: {normalized}"
                )
            unix_mode = (info.external_attr >> 16) & 0xFFFF
            file_type = stat.S_IFMT(unix_mode)
            if file_type == stat.S_IFLNK:
                raise CoworkPluginError(
                    "ZIP contains a symbolic link, which is not allowed: "
                    f"{normalized}"
                )
            if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise CoworkPluginError(
                    f"ZIP contains an unsupported special file: {normalized}"
                )
            declared_total += info.file_size
            if declared_total > max_extracted_bytes:
                raise CoworkPluginError(
                    f"ZIP expands beyond the {max_extracted_bytes} byte "
                    "safety limit."
                )
            validated.append((info, normalized))
        if "manifest.json" not in seen:
            raise CoworkPluginError(
                "ZIP must contain manifest.json at its root; wrapper "
                "directories are not supported."
            )

        extraction_root.mkdir(parents=True, exist_ok=False)
        resolved_root = extraction_root.resolve(strict=True)
        actual_total = 0
        for info, normalized in validated:
            posix_path = PurePosixPath(normalized.rstrip("/"))
            target = resolved_root.joinpath(*posix_path.parts).resolve(strict=False)
            try:
                target.relative_to(resolved_root)
            except ValueError as exc:
                raise CoworkPluginError(
                    f"ZIP entry escapes the extraction directory: {normalized}"
                ) from exc
            if info.is_dir() or normalized.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with archive.open(info) as source, target.open("xb") as output:
                    while chunk := source.read(64 * 1024):
                        actual_total += len(chunk)
                        if (
                            actual_total > max_extracted_bytes
                            or actual_total > declared_total
                        ):
                            raise CoworkPluginError(
                                "ZIP expands beyond its declared or configured "
                                "byte safety limit."
                            )
                        output.write(chunk)
            except (
                OSError,
                EOFError,
                RuntimeError,
                NotImplementedError,
                zlib.error,
                zipfile.BadZipFile,
            ) as exc:
                raise CoworkPluginError(
                    f"ZIP entry cannot be safely extracted: {normalized}: {exc}"
                ) from exc
        if actual_total != declared_total:
            raise CoworkPluginError(
                "ZIP extracted size does not match its declared size."
            )
    return len(validated), actual_total


def find_npx_command() -> list[str]:
    npx = shutil.which("npx")
    if not npx:
        raise CoworkPluginError(
            "npx is required to run Microsoft 365 Agents Toolkit."
        )
    npx_path = Path(npx).resolve()
    if npx_path.suffix.lower() not in (".cmd", ".bat"):
        return [str(npx_path)]

    node = shutil.which("node")
    if not node:
        raise CoworkPluginError(
            "node is required to run Microsoft 365 Agents Toolkit."
        )
    node_path = Path(node).resolve()
    if node_path.suffix.lower() in (".cmd", ".bat"):
        raise CoworkPluginError(
            "A native node executable is required; Windows batch launchers "
            "are not safe for untrusted package paths."
        )
    candidates = (
        npx_path.parent / "node_modules" / "npm" / "bin" / "npx-cli.js",
        node_path.parent
        / "node_modules"
        / "npm"
        / "bin"
        / "npx-cli.js",
    )
    npx_cli = next((path for path in candidates if path.is_file()), None)
    if npx_cli is None:
        raise CoworkPluginError(
            "Cannot locate npx-cli.js without using the unsafe Windows "
            "command wrapper."
        )
    return [str(node_path), str(npx_cli)]


def run_atk(arguments: list[str], atk_version: str, cwd: Path | None = None) -> None:
    package_name = f"@microsoft/m365agentstoolkit-cli@{atk_version}"
    command = [*find_npx_command(), "--yes", package_name, *arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            shell=False,
        )
    except OSError as exc:
        raise CoworkPluginError(f"Cannot start npx: {exc}") from exc
    if completed.returncode:
        operation = arguments[0] if arguments else "command"
        raise CoworkPluginError(
            f"atk {operation} failed with exit code {completed.returncode}."
        )


def temporary_workspace(prefix: str) -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix=prefix)
