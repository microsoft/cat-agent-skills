#!/usr/bin/env python3
"""Deterministic file operations for the Semantic PDF Image Extractor skill."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import stat
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "semantic-pdf-image-manifest/1.0"
REGION_VERSION = "semantic-pdf-image-regions/1.0"
CROP_RESULT_VERSION = "semantic-pdf-image-crops/1.0"
DUPLICATE_RESULT_VERSION = "semantic-pdf-image-duplicates/1.0"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
PERCEPTUAL_HASH_PATTERN = re.compile(r"^[a-f0-9]{16}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DATE_TIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
VALID_STATUSES = {"verified", "best-effort", "review-required"}
VALID_ASSET_TYPES = {
    "photo", "diagram", "chart", "map", "screenshot", "illustration",
    "table-image", "logo", "icon", "composite", "other"
}
VALID_ROLES = {"informational", "decorative", "branding", "navigation", "uncertain"}
VALID_METHODS = {
    "native-vision", "ocr-and-vision", "text-layer-and-vision",
    "embedded-object-and-vision", "manual"
}
VALID_RESOLUTION_STATUSES = {"sufficient", "low-resolution", "unreadable", "unknown"}


class ValidationError(Exception):
    """Raised when an artifact violates the extraction contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_keys(
    value: dict[str, Any],
    required: set[str],
    allowed: set[str],
    field: str,
) -> None:
    require(isinstance(value, dict), f"{field} must be an object")
    missing = sorted(required - value.keys())
    require(not missing, f"{field} is missing required properties: {', '.join(missing)}")
    unknown = sorted(str(key) for key in value if key not in allowed)
    require(not unknown, f"{field} contains unknown properties: {', '.join(unknown)}")


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot read valid JSON from {path}: {exc}") from exc


def require_no_symlink_components(path: Path, field: str) -> None:
    absolute_path = path.absolute()
    for component in (absolute_path, *absolute_path.parents):
        require(not component.is_symlink(), f"{field} cannot traverse a symlink: {component}")


def resolve_user_path(value: str, field: str) -> Path:
    path = Path(value)
    require_no_symlink_components(path, field)
    return path.resolve()


def write_json(path: Path, value: Any) -> None:
    require_no_symlink_components(path, str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    require_no_symlink_components(path, str(path))
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def safe_unlink(path: Path, field: str) -> None:
    require_no_symlink_components(path, field)
    require(path.is_file(), f"{field} must be a regular file")
    path.unlink()


def clear_current_run_metadata(output_dir: Path) -> None:
    stale_paths = (
        output_dir / "summary.md",
        output_dir / "diagnostics" / "region-proposals.json",
        output_dir / "diagnostics" / "crop-results.json",
        output_dir / "diagnostics" / "duplicate-suggestions.json",
        output_dir / "diagnostics" / "validation-report.json",
    )
    for stale_path in stale_paths:
        require_no_symlink_components(stale_path, str(stale_path))
        if stale_path.exists():
            safe_unlink(stale_path, str(stale_path))


def prepare_page_directory(output_dir: Path, document_id: str) -> Path:
    pages_dir = output_dir / "pages" / document_id
    require_no_symlink_components(pages_dir, str(pages_dir))
    pages_dir.mkdir(parents=True, exist_ok=True)
    require_no_symlink_components(pages_dir, str(pages_dir))
    for old_page in pages_dir.glob("page-*.png"):
        safe_unlink(old_page, str(old_page))
    return pages_dir


def safe_relative_path(value: Any, field: str) -> PurePosixPath:
    require(isinstance(value, str) and bool(value), f"{field} must be a non-empty relative path")
    require("\\" not in value and not any(unicodedata.category(character) == "Cc" for character in value),
            f"{field} must use a safe path with forward slashes")
    path = PurePosixPath(value)
    require(value != "." and not path.is_absolute() and ".." not in path.parts,
            f"{field} must stay inside the output directory: {value}")
    require(re.match(r"^[A-Za-z]:", value) is None,
            f"{field} must stay inside the output directory: {value}")
    return path


def resolve_output_path(
    output_dir: Path,
    relative_path: str,
    field: str,
    *,
    must_exist: bool = True,
) -> Path:
    path = safe_relative_path(relative_path, field)
    root = output_dir.resolve()
    candidate = root.joinpath(*path.parts)
    resolved = candidate.resolve(strict=False)
    require(resolved.is_relative_to(root), f"{field} must stay inside the output directory")
    if must_exist:
        require(candidate.is_file(), f"Referenced file is missing: {relative_path}")
    return candidate


def require_id(value: Any, field: str) -> str:
    require(isinstance(value, str) and ID_PATTERN.fullmatch(value) is not None,
            f"{field} must use lowercase letters, digits, and hyphens")
    return value


def parse_page_range(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([1-9]\d*)-([1-9]\d*)", value)
    if match is None:
        raise argparse.ArgumentTypeError("page range must use FROM-TO positive integers")
    start, end = (int(item) for item in match.groups())
    if start > end:
        raise argparse.ArgumentTypeError("page range FROM must be less than or equal to TO")
    return start, end


def selected_render_pages(
    total_page_count: int,
    page_ranges: list[tuple[int, int]] | None,
) -> tuple[list[tuple[int, int]], list[int]]:
    require(total_page_count > 0, "PDF contains no pages")
    requested_ranges = page_ranges or [(1, total_page_count)]
    require(all(end <= total_page_count for _, end in requested_ranges),
            "Render page range cannot exceed the PDF page count")
    selected_page_numbers = sorted({
        page_number
        for start, end in requested_ranges
        for page_number in range(start, end + 1)
    })
    return requested_ranges, selected_page_numbers


def require_string_array(value: Any, field: str, unique: bool = False) -> list[str]:
    require(isinstance(value, list) and all(isinstance(item, str) for item in value),
            f"{field} must be an array of strings")
    if unique:
        require(len(value) == len(set(value)), f"{field} must contain unique values")
    return value


def validate_box(value: Any, field: str, nullable: bool = False) -> list[float] | None:
    if value is None:
        require(nullable, f"{field} must contain a normalized region")
        return None
    require(isinstance(value, list) and len(value) == 4, f"{field} must contain four coordinates")
    require(all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value),
            f"{field} coordinates must be numbers")
    left, top, right, bottom = value
    require(all(0 <= item <= 1 for item in value), f"{field} coordinates must be between 0 and 1")
    require(left < right and top < bottom, f"{field} must have positive width and height")
    return [float(item) for item in value]


def contains_box(outer: list[float], inner: list[float]) -> bool:
    tolerance = 0.000001
    return (outer[0] <= inner[0] + tolerance and outer[1] <= inner[1] + tolerance
            and outer[2] + tolerance >= inner[2] and outer[3] + tolerance >= inner[3])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_png_signature(path: Path, field: str) -> None:
    try:
        with path.open("rb") as handle:
            signature = handle.read(len(PNG_SIGNATURE))
    except OSError as exc:
        raise ValidationError(f"Cannot read {field}: {exc}") from exc
    require(signature == PNG_SIGNATURE, f"{field} must be a PNG file")


def normalized_pixel_box(box: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    left = max(0, min(width - 1, math.floor(box[0] * width)))
    top = max(0, min(height - 1, math.floor(box[1] * height)))
    right = max(left + 1, min(width, math.ceil(box[2] * width)))
    bottom = max(top + 1, min(height, math.ceil(box[3] * height)))
    return left, top, right, bottom


def average_hash(image: Any) -> str:
    try:
        from PIL import Image
        resampling = Image.Resampling.LANCZOS
    except AttributeError:
        from PIL import Image
        resampling = Image.LANCZOS
    pixels = list(image.convert("L").resize((8, 8), resampling).getdata())
    average = sum(pixels) / len(pixels)
    bits = 0
    for pixel in pixels:
        bits = (bits << 1) | int(pixel >= average)
    return f"{bits:016x}"


def crop_quality(path: Path, image: Any) -> dict[str, Any]:
    width, height = image.size
    resolution_status = "sufficient" if width >= 256 and height >= 256 else "low-resolution"
    return {
        "width": width,
        "height": height,
        "fileBytes": path.stat().st_size,
        "sha256": file_sha256(path),
        "perceptualHash": average_hash(image),
        "resolutionStatus": resolution_status
    }


def validate_quality(value: Any, field: str, image_path: Path | None = None) -> None:
    required = {"width", "height", "fileBytes", "sha256", "perceptualHash", "resolutionStatus"}
    require_keys(value, required, required, field)
    for key in ("width", "height"):
        item = value.get(key)
        require(item is None or (isinstance(item, int) and not isinstance(item, bool) and item >= 1),
                f"{field}.{key} must be null or a positive integer")
    file_bytes = value.get("fileBytes")
    require(file_bytes is None or (isinstance(file_bytes, int) and not isinstance(file_bytes, bool)
                                   and file_bytes >= 0),
            f"{field}.fileBytes must be null or a non-negative integer")
    sha256 = value.get("sha256")
    require(sha256 is None or (isinstance(sha256, str) and HASH_PATTERN.fullmatch(sha256) is not None),
            f"{field}.sha256 must be null or a lowercase SHA-256")
    perceptual_hash = value.get("perceptualHash")
    require(perceptual_hash is None or (isinstance(perceptual_hash, str)
                                        and PERCEPTUAL_HASH_PATTERN.fullmatch(perceptual_hash) is not None),
            f"{field}.perceptualHash must be null or a 64-bit lowercase hex value")
    require(value.get("resolutionStatus") in VALID_RESOLUTION_STATUSES,
            f"{field}.resolutionStatus is invalid")
    if image_path is not None:
        require(image_path.is_file(), f"Referenced asset is missing: {image_path}")
        if file_bytes is not None:
            require(image_path.stat().st_size == file_bytes, f"{field}.fileBytes does not match the asset")
        if sha256 is not None:
            require(file_sha256(image_path) == sha256, f"{field}.sha256 does not match the asset")


def validate_manifest_data(manifest: Any, output_dir: Path | None = None) -> dict[str, Any]:
    root_keys = {
        "schemaVersion", "generatedAt", "request", "documents", "assets",
        "duplicateGroups", "exclusions", "review", "limitations"
    }
    require_keys(manifest, root_keys, root_keys, "Manifest root")
    require(manifest["schemaVersion"] == SCHEMA_VERSION, f"schemaVersion must be {SCHEMA_VERSION}")
    generated_at = manifest["generatedAt"]
    if generated_at is not None:
        require(isinstance(generated_at, str) and DATE_TIME_PATTERN.fullmatch(generated_at) is not None,
                "generatedAt must be null or an RFC 3339 date-time")
        try:
            datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("generatedAt must be null or an RFC 3339 date-time") from exc

    request_keys = {
        "mode", "includeTypes", "excludeTypes", "includeDecorative", "preserveContext", "pageRanges"
    }
    request = manifest["request"]
    require_keys(request, request_keys, request_keys, "request")
    require(request["mode"] in {"meaningful", "all-visuals", "photos", "diagrams", "charts", "custom"},
            "request.mode is invalid")
    include_types = request["includeTypes"]
    exclude_types = request["excludeTypes"]
    require(isinstance(include_types, list)
            and all(isinstance(item, str) and item in VALID_ASSET_TYPES for item in include_types)
            and len(include_types) == len(set(include_types)), "request.includeTypes is invalid")
    require(isinstance(exclude_types, list)
            and all(isinstance(item, str) and item in VALID_ASSET_TYPES for item in exclude_types)
            and len(exclude_types) == len(set(exclude_types)), "request.excludeTypes is invalid")
    require(set(include_types).isdisjoint(exclude_types), "A type cannot be both included and excluded")
    require(isinstance(request["includeDecorative"], bool), "request.includeDecorative must be boolean")
    require(isinstance(request["preserveContext"], bool), "request.preserveContext must be boolean")
    require(isinstance(request["pageRanges"], list), "request.pageRanges must be an array")

    documents = manifest["documents"]
    require(isinstance(documents, list) and bool(documents), "documents must contain at least one document")
    document_ids: set[str] = set()
    document_page_counts: dict[str, int] = {}
    document_page_numbers: dict[str, set[int]] = {}
    page_lookup: dict[tuple[str, int], str] = {}
    referenced_paths: set[str] = set()
    page_count = 0
    page_review_required = False
    document_keys = {"id", "sourceFile", "sha256", "title", "languages", "pageCount", "pages"}
    page_keys = {"pageNumber", "image", "width", "height", "status", "reviewReasons"}
    for document_index, document in enumerate(documents):
        field = f"documents[{document_index}]"
        require_keys(document, document_keys, document_keys, field)
        document_id = require_id(document["id"], f"{field}.id")
        require(document_id not in document_ids, f"Duplicate document id: {document_id}")
        document_ids.add(document_id)
        require(isinstance(document["sourceFile"], str) and bool(document["sourceFile"]),
                f"{field}.sourceFile is required")
        sha256 = document["sha256"]
        require(sha256 is None or (isinstance(sha256, str) and HASH_PATTERN.fullmatch(sha256) is not None),
                f"{field}.sha256 must be null or a lowercase SHA-256")
        require(document["title"] is None or isinstance(document["title"], str),
                f"{field}.title must be null or a string")
        require_string_array(document["languages"], f"{field}.languages", unique=True)
        declared_page_count = document["pageCount"]
        require(isinstance(declared_page_count, int) and not isinstance(declared_page_count, bool)
                and declared_page_count >= 1, f"{field}.pageCount must be a positive integer")
        document_page_counts[document_id] = declared_page_count
        pages = document["pages"]
        require(isinstance(pages, list) and bool(pages), f"{field}.pages must contain at least one page")
        require(len(pages) <= declared_page_count, f"{field}.pages exceeds the declared page count")
        numbers: set[int] = set()
        for page_index, page in enumerate(pages):
            page_field = f"{field}.pages[{page_index}]"
            require_keys(page, page_keys, page_keys, page_field)
            number = page["pageNumber"]
            require(isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= declared_page_count,
                    f"{page_field}.pageNumber is invalid")
            require(number not in numbers, f"Duplicate page number {number} in {document_id}")
            numbers.add(number)
            image = str(safe_relative_path(page["image"], f"{page_field}.image"))
            expected_image = f"pages/{document_id}/page-{number:04d}.png"
            require(image == expected_image, f"{page_field}.image must be {expected_image}")
            require(page["status"] in VALID_STATUSES, f"{page_field}.status is invalid")
            reasons = require_string_array(page["reviewReasons"], f"{page_field}.reviewReasons")
            if page["status"] != "verified":
                require(bool(reasons), f"{page_field} needs at least one review reason")
            if page["status"] == "review-required":
                page_review_required = True
            for dimension in ("width", "height"):
                value = page[dimension]
                require(value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 1),
                        f"{page_field}.{dimension} must be null or a positive integer")
            page_lookup[(document_id, number)] = image
            referenced_paths.add(image)
            page_count += 1
        document_page_numbers[document_id] = numbers

    requested_pages: dict[str, set[int]] = {document_id: set() for document_id in document_ids}
    for range_index, page_range in enumerate(request["pageRanges"]):
        field = f"request.pageRanges[{range_index}]"
        range_keys = {"documentId", "from", "to"}
        require_keys(page_range, range_keys, range_keys, field)
        document_id = require_id(page_range["documentId"], f"{field}.documentId")
        require(document_id in document_ids, f"{field}.documentId is unknown")
        start, end = page_range["from"], page_range["to"]
        require(isinstance(start, int) and not isinstance(start, bool) and start >= 1,
                f"{field}.from is invalid")
        require(isinstance(end, int) and not isinstance(end, bool) and end >= 1,
                f"{field}.to is invalid")
        require(start <= end, f"{field}.from must be less than or equal to to")
        require(end <= document_page_counts[document_id],
                f"{field}.to exceeds the declared page count")
        requested_pages[document_id].update(range(start, end + 1))
    if request["pageRanges"]:
        for document_id, selected_pages in requested_pages.items():
            require(bool(selected_pages),
                    f"Document {document_id} must have a selected page range")
            actual_pages = document_page_numbers[document_id]
            missing_pages = selected_pages - actual_pages
            extra_pages = actual_pages - selected_pages
            require(not missing_pages and not extra_pages,
                    f"Document {document_id} page records must exactly match its requested pages; "
                    f"missing: {', '.join(str(number) for number in sorted(missing_pages)) or 'none'}; "
                    f"extra: {', '.join(str(number) for number in sorted(extra_pages)) or 'none'}")
    else:
        for document_id, declared_page_count in document_page_counts.items():
            expected_pages = set(range(1, declared_page_count + 1))
            missing_pages = expected_pages - document_page_numbers[document_id]
            require(not missing_pages,
                    f"Document {document_id} is missing page records: "
                    + ", ".join(str(number) for number in sorted(missing_pages)))

    assets = manifest["assets"]
    require(isinstance(assets, list), "assets must be an array")
    asset_ids: set[str] = set()
    occurrence_ids: set[str] = set()
    occurrence_output_paths: set[str] = set()
    occurrence_asset: dict[str, str] = {}
    review_required_occurrences: set[str] = set()
    asset_group_ids: dict[str, str | None] = {}
    asset_keys = {
        "id", "assetType", "semanticRole", "description", "labels", "keywords",
        "occurrences", "duplicateGroupId"
    }
    occurrence_keys = {
        "id", "documentId", "pageNumber", "sourceRegion", "contextRegion", "assetImage",
        "contextImage", "fullPageFallback", "caption", "nearbyText", "quality",
        "extractionMethod", "confidence", "status", "reviewReasons"
    }
    for asset_index, asset in enumerate(assets):
        field = f"assets[{asset_index}]"
        require_keys(asset, asset_keys, asset_keys, field)
        asset_id = require_id(asset["id"], f"{field}.id")
        require(asset_id not in asset_ids, f"Duplicate asset id: {asset_id}")
        asset_ids.add(asset_id)
        require(asset["assetType"] in VALID_ASSET_TYPES, f"{field}.assetType is invalid")
        require(asset["semanticRole"] in VALID_ROLES, f"{field}.semanticRole is invalid")
        require(asset["description"] is None or isinstance(asset["description"], str),
                f"{field}.description must be null or a string")
        require_string_array(asset["labels"], f"{field}.labels", unique=True)
        require_string_array(asset["keywords"], f"{field}.keywords", unique=True)
        duplicate_group_id = asset["duplicateGroupId"]
        if duplicate_group_id is not None:
            require_id(duplicate_group_id, f"{field}.duplicateGroupId")
        asset_group_ids[asset_id] = duplicate_group_id
        occurrences = asset["occurrences"]
        require(isinstance(occurrences, list) and bool(occurrences), f"{field}.occurrences cannot be empty")
        for occurrence_index, occurrence in enumerate(occurrences):
            occurrence_field = f"{field}.occurrences[{occurrence_index}]"
            require_keys(occurrence, occurrence_keys, occurrence_keys, occurrence_field)
            occurrence_id = require_id(occurrence["id"], f"{occurrence_field}.id")
            require(occurrence_id not in occurrence_ids, f"Duplicate occurrence id: {occurrence_id}")
            occurrence_ids.add(occurrence_id)
            occurrence_asset[occurrence_id] = asset_id
            document_id = require_id(occurrence["documentId"], f"{occurrence_field}.documentId")
            page_number = occurrence["pageNumber"]
            require(isinstance(page_number, int) and not isinstance(page_number, bool) and page_number >= 1,
                    f"{occurrence_field}.pageNumber must be a positive integer")
            require((document_id, page_number) in page_lookup,
                    f"{occurrence_field} does not identify a rendered source page")
            source_region = validate_box(occurrence["sourceRegion"], f"{occurrence_field}.sourceRegion")
            context_region = validate_box(occurrence["contextRegion"],
                                          f"{occurrence_field}.contextRegion", nullable=True)
            if context_region is not None:
                require(contains_box(context_region, source_region),
                        f"{occurrence_field}.contextRegion must contain sourceRegion")
            asset_image = str(safe_relative_path(occurrence["assetImage"],
                                                 f"{occurrence_field}.assetImage"))
            require(asset_image.startswith(f"assets/{document_id}/") and asset_image.lower().endswith(".png"),
                    f"{occurrence_field}.assetImage must be a PNG below assets/{document_id}/")
            require(asset_image not in occurrence_output_paths,
                    f"{occurrence_field}.assetImage duplicates another occurrence output")
            occurrence_output_paths.add(asset_image)
            context_image_value = occurrence["contextImage"]
            require((context_region is None) == (context_image_value is None),
                    f"{occurrence_field}.contextImage and contextRegion must be provided together")
            context_image: str | None = None
            if context_image_value is not None:
                context_image = str(safe_relative_path(context_image_value,
                                                       f"{occurrence_field}.contextImage"))
                require(context_image.startswith(f"context/{document_id}/")
                        and context_image.lower().endswith(".png"),
                        f"{occurrence_field}.contextImage must be a PNG below context/{document_id}/")
                require(context_image not in occurrence_output_paths,
                        f"{occurrence_field}.contextImage duplicates another occurrence output")
                occurrence_output_paths.add(context_image)
            fallback = str(safe_relative_path(occurrence["fullPageFallback"],
                                              f"{occurrence_field}.fullPageFallback"))
            require(fallback == page_lookup[(document_id, page_number)],
                    f"{occurrence_field}.fullPageFallback must identify its source page")
            for text_field in ("caption", "nearbyText"):
                value = occurrence[text_field]
                require(value is None or isinstance(value, str),
                        f"{occurrence_field}.{text_field} must be null or a string")
            require(occurrence["extractionMethod"] in VALID_METHODS,
                    f"{occurrence_field}.extractionMethod is invalid")
            confidence = occurrence["confidence"]
            require(isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
                    and 0 <= confidence <= 1, f"{occurrence_field}.confidence must be between 0 and 1")
            status = occurrence["status"]
            require(status in VALID_STATUSES, f"{occurrence_field}.status is invalid")
            reasons = require_string_array(occurrence["reviewReasons"],
                                           f"{occurrence_field}.reviewReasons")
            if status != "verified":
                require(bool(reasons), f"{occurrence_field} needs at least one review reason")
            if status == "review-required":
                review_required_occurrences.add(occurrence_id)
            referenced_paths.update({asset_image, fallback})
            if context_image is not None:
                referenced_paths.add(context_image)
            resolved_asset = (resolve_output_path(output_dir, asset_image, f"{occurrence_field}.assetImage")
                              if output_dir is not None else None)
            validate_quality(occurrence["quality"], f"{occurrence_field}.quality", resolved_asset)

    duplicate_groups = manifest["duplicateGroups"]
    require(isinstance(duplicate_groups, list), "duplicateGroups must be an array")
    group_ids: set[str] = set()
    group_members: dict[str, set[str]] = {}
    group_keys = {"id", "canonicalAssetId", "memberAssetIds", "matchType", "confidence", "reviewed"}
    for group_index, group in enumerate(duplicate_groups):
        field = f"duplicateGroups[{group_index}]"
        require_keys(group, group_keys, group_keys, field)
        group_id = require_id(group["id"], f"{field}.id")
        require(group_id not in group_ids, f"Duplicate duplicate-group id: {group_id}")
        group_ids.add(group_id)
        canonical = require_id(group["canonicalAssetId"], f"{field}.canonicalAssetId")
        members = group["memberAssetIds"]
        require(isinstance(members, list) and len(members) >= 2,
                f"{field}.memberAssetIds must contain at least two assets")
        require(all(isinstance(item, str) and ID_PATTERN.fullmatch(item) is not None for item in members)
                and len(members) == len(set(members)),
                f"{field}.memberAssetIds must contain unique asset IDs")
        require(set(members).issubset(asset_ids) and canonical in members,
                f"{field} references unknown assets or omits its canonical asset")
        require(group["matchType"] in {"exact", "near-duplicate", "semantic-variant"},
                f"{field}.matchType is invalid")
        confidence = group["confidence"]
        require(isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
                and 0 <= confidence <= 1, f"{field}.confidence must be between 0 and 1")
        require(isinstance(group["reviewed"], bool), f"{field}.reviewed must be boolean")
        group_members[group_id] = set(members)
    for asset_id, group_id in asset_group_ids.items():
        if group_id is not None:
            require(group_id in group_members and asset_id in group_members[group_id],
                    f"Asset {asset_id} has an inconsistent duplicateGroupId")
    for group_id, members in group_members.items():
        require(all(asset_group_ids[member] == group_id for member in members),
                f"Every member of {group_id} must reference that duplicate group")

    exclusions = manifest["exclusions"]
    exclusion_keys = {"totalCandidates", "byReason"}
    require_keys(exclusions, exclusion_keys, exclusion_keys, "exclusions")
    total_candidates = exclusions["totalCandidates"]
    by_reason = exclusions["byReason"]
    require(isinstance(total_candidates, int) and not isinstance(total_candidates, bool)
            and total_candidates >= 0, "exclusions.totalCandidates must be a non-negative integer")
    require(isinstance(by_reason, dict) and all(isinstance(key, str) and bool(key) for key in by_reason),
            "exclusions.byReason must be an object with non-empty reason keys")
    require(all(isinstance(value, int) and not isinstance(value, bool) and value >= 0
                for value in by_reason.values()), "exclusions.byReason counts must be non-negative integers")
    require(total_candidates == sum(by_reason.values()),
            "exclusions.totalCandidates must equal the sum of exclusions.byReason")

    review = manifest["review"]
    review_keys = {"required", "assetIds", "occurrenceIds", "notes"}
    require_keys(review, review_keys, review_keys, "review")
    require(isinstance(review["required"], bool), "review.required must be boolean")
    review_asset_ids = review["assetIds"]
    review_occurrence_ids = review["occurrenceIds"]
    require(isinstance(review_asset_ids, list)
            and all(isinstance(item, str) and ID_PATTERN.fullmatch(item) is not None
                    for item in review_asset_ids)
            and len(review_asset_ids) == len(set(review_asset_ids))
            and set(review_asset_ids).issubset(asset_ids), "review.assetIds contains duplicates or unknown assets")
    require(isinstance(review_occurrence_ids, list)
            and all(isinstance(item, str) and ID_PATTERN.fullmatch(item) is not None
                    for item in review_occurrence_ids)
            and len(review_occurrence_ids) == len(set(review_occurrence_ids))
            and set(review_occurrence_ids).issubset(occurrence_ids),
            "review.occurrenceIds contains duplicates or unknown occurrences")
    notes = require_string_array(review["notes"], "review.notes")
    require(review_required_occurrences.issubset(set(review_occurrence_ids)),
            "Every review-required occurrence must appear in review.occurrenceIds")
    required_assets = {occurrence_asset[item] for item in review_required_occurrences}
    require(required_assets.issubset(set(review_asset_ids)),
            "Assets with review-required occurrences must appear in review.assetIds")
    expected_review = page_review_required or bool(review_asset_ids or review_occurrence_ids or notes)
    require(review["required"] is expected_review,
            "review.required must reflect the review IDs and notes")
    require_string_array(manifest["limitations"], "limitations")

    if output_dir is not None:
        for path in sorted(referenced_paths):
            resolved_path = resolve_output_path(output_dir, path, path)
            require_png_signature(resolved_path, path)
    return {
        "documentCount": len(documents),
        "pageCount": page_count,
        "assetCount": len(assets),
        "occurrenceCount": len(occurrence_ids),
        "duplicateGroupCount": len(duplicate_groups),
        "reviewRequiredOccurrenceCount": len(review_required_occurrences),
        "referencedFileCount": len(referenced_paths)
    }


def validate_region_proposals(proposal: Any, output_dir: Path | None = None) -> list[dict[str, Any]]:
    require(isinstance(proposal, dict) and proposal.get("schemaVersion") == REGION_VERSION,
            f"Region schemaVersion must be {REGION_VERSION}")
    documents = proposal.get("documents")
    require(isinstance(documents, list) and bool(documents), "Region documents cannot be empty")
    flattened: list[dict[str, Any]] = []
    document_ids: set[str] = set()
    occurrence_ids: set[str] = set()
    outputs: set[str] = set()
    for document_index, document in enumerate(documents):
        field = f"documents[{document_index}]"
        require(isinstance(document, dict), f"{field} must be an object")
        document_id = require_id(document.get("documentId"), f"{field}.documentId")
        require(document_id not in document_ids, f"Duplicate region document id: {document_id}")
        document_ids.add(document_id)
        pages = document.get("pages")
        require(isinstance(pages, list) and bool(pages), f"{field}.pages cannot be empty")
        page_numbers: set[int] = set()
        for page_index, page in enumerate(pages):
            page_field = f"{field}.pages[{page_index}]"
            require(isinstance(page, dict), f"{page_field} must be an object")
            page_number = page.get("pageNumber")
            require(isinstance(page_number, int) and not isinstance(page_number, bool) and page_number >= 1,
                    f"{page_field}.pageNumber is invalid")
            require(page_number not in page_numbers, f"Duplicate page {page_number} in {document_id}")
            page_numbers.add(page_number)
            image = str(safe_relative_path(page.get("image"), f"{page_field}.image"))
            expected_image = f"pages/{document_id}/page-{page_number:04d}.png"
            require(image == expected_image, f"{page_field}.image must be {expected_image}")
            if output_dir is not None:
                resolve_output_path(output_dir, image, f"{page_field}.image")
            regions = page.get("regions")
            require(isinstance(regions, list), f"{page_field}.regions must be an array")
            for region_index, region in enumerate(regions):
                region_field = f"{page_field}.regions[{region_index}]"
                require(isinstance(region, dict), f"{region_field} must be an object")
                asset_id = require_id(region.get("assetId"), f"{region_field}.assetId")
                occurrence_id = require_id(region.get("occurrenceId"), f"{region_field}.occurrenceId")
                require(occurrence_id not in occurrence_ids, f"Duplicate occurrence id: {occurrence_id}")
                occurrence_ids.add(occurrence_id)
                require(region.get("assetType") in VALID_ASSET_TYPES,
                        f"{region_field}.assetType is invalid")
                asset_box = validate_box(region.get("assetBox"), f"{region_field}.assetBox")
                context_box = validate_box(region.get("contextBox"), f"{region_field}.contextBox", nullable=True)
                if context_box is not None:
                    require(contains_box(context_box, asset_box),
                            f"{region_field}.contextBox must contain assetBox")
                asset_output = str(safe_relative_path(region.get("assetOutput"),
                                                      f"{region_field}.assetOutput"))
                require(asset_output.startswith(f"assets/{document_id}/")
                        and asset_output.lower().endswith(".png"),
                        f"{region_field}.assetOutput must be a PNG below assets/{document_id}/")
                require(asset_output not in outputs, f"Duplicate crop output: {asset_output}")
                outputs.add(asset_output)
                context_output_value = region.get("contextOutput")
                require((context_box is None) == (context_output_value is None),
                        f"{region_field}.contextOutput and contextBox must be provided together")
                context_output: str | None = None
                if context_output_value is not None:
                    context_output = str(safe_relative_path(context_output_value,
                                                            f"{region_field}.contextOutput"))
                    require(context_output.startswith(f"context/{document_id}/")
                            and context_output.lower().endswith(".png"),
                            f"{region_field}.contextOutput must be a PNG below context/{document_id}/")
                    require(context_output not in outputs, f"Duplicate crop output: {context_output}")
                    outputs.add(context_output)
                reason = region.get("reason")
                require(reason is None or isinstance(reason, str), f"{region_field}.reason must be a string or null")
                flattened.append({
                    "assetId": asset_id,
                    "occurrenceId": occurrence_id,
                    "documentId": document_id,
                    "pageNumber": page_number,
                    "assetType": region["assetType"],
                    "sourcePage": image,
                    "sourceRegion": asset_box,
                    "contextRegion": context_box,
                    "assetImage": asset_output,
                    "contextImage": context_output
                })
    return flattened


def command_render(args: argparse.Namespace) -> None:
    try:
        import pypdfium2 as pdfium
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise ValidationError(
            "PDF rendering needs pypdfium2 and Pillow; use native runtime rendering or install them"
        ) from exc
    input_path = Path(args.input).resolve()
    require(input_path.is_file() and input_path.suffix.lower() == ".pdf",
            "Input must be an existing PDF")
    document_id = require_id(args.document_id, "document-id")
    output_dir = resolve_user_path(args.output_dir, "output-dir")
    try:
        document = pdfium.PdfDocument(str(input_path))
    except Exception as exc:
        raise ValidationError(f"Cannot open PDF; it may be corrupt or encrypted: {exc}") from exc
    try:
        total_page_count = len(document)
        requested_ranges, selected_page_numbers = selected_render_pages(
            total_page_count, args.page_ranges
        )
        clear_current_run_metadata(output_dir)
        pages_dir = prepare_page_directory(output_dir, document_id)
        scale = args.dpi / 72
        rendered_pages: list[dict[str, Any]] = []
        for page_number in selected_page_numbers:
            page_index = page_number - 1
            page = document[page_index]
            try:
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil()
                destination = pages_dir / f"page-{page_index + 1:04d}.png"
                require_no_symlink_components(destination, str(destination))
                image.save(destination, format="PNG", optimize=True)
                rendered_pages.append({
                    "pageNumber": page_index + 1,
                    "image": destination.relative_to(output_dir).as_posix(),
                    "width": image.width,
                    "height": image.height,
                    "fileBytes": destination.stat().st_size,
                    "sha256": file_sha256(destination)
                })
            finally:
                page.close()
    finally:
        document.close()
    result = {
        "documentId": document_id,
        "sourceFile": input_path.name,
        "sourceSha256": file_sha256(input_path),
        "pageCount": total_page_count,
        "renderedPageCount": len(rendered_pages),
        "pageRanges": [{"from": start, "to": end} for start, end in requested_ranges],
        "dpi": args.dpi,
        "pages": rendered_pages
    }
    write_json(output_dir / "diagnostics" / f"render-results-{document_id}.json", result)
    print(f"Rendered {len(rendered_pages)} page(s) to {pages_dir}")


def command_crop(args: argparse.Namespace) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValidationError("Cropping needs Pillow; use native runtime cropping or install it") from exc
    output_dir = resolve_user_path(args.output_dir, "output-dir")
    require(output_dir.is_dir(), "Output directory does not exist")
    proposal = load_json(Path(args.regions).resolve())
    regions = validate_region_proposals(proposal, output_dir)
    results: list[dict[str, Any]] = []
    skipped = 0
    current_source: str | None = None
    image: Any = None
    try:
        for region in regions:
            if current_source != region["sourcePage"]:
                if image is not None:
                    image.close()
                current_source = region["sourcePage"]
                image = Image.open(output_dir / Path(current_source))
                image.load()
            asset_pixel_box = normalized_pixel_box(region["sourceRegion"], image.width, image.height)
            asset_width = asset_pixel_box[2] - asset_pixel_box[0]
            asset_height = asset_pixel_box[3] - asset_pixel_box[1]
            asset_path = resolve_output_path(
                output_dir, region["assetImage"], f"{region['occurrenceId']}.assetImage",
                must_exist=False
            )
            require(not asset_path.is_symlink(), f"{region['occurrenceId']}.assetImage cannot be a symlink")
            if asset_path.exists():
                require(asset_path.is_file(), f"{region['occurrenceId']}.assetImage must be a regular file")
                asset_path.unlink()
            if region["contextImage"] is not None:
                stale_context_path = resolve_output_path(
                    output_dir, region["contextImage"], f"{region['occurrenceId']}.contextImage",
                    must_exist=False
                )
                require(not stale_context_path.is_symlink(),
                        f"{region['occurrenceId']}.contextImage cannot be a symlink")
                if stale_context_path.exists():
                    require(stale_context_path.is_file(),
                            f"{region['occurrenceId']}.contextImage must be a regular file")
                    stale_context_path.unlink()
            if asset_width < args.minimum_pixels or asset_height < args.minimum_pixels:
                results.append({
                    "assetId": region["assetId"],
                    "occurrenceId": region["occurrenceId"],
                    "documentId": region["documentId"],
                    "pageNumber": region["pageNumber"],
                    "sourcePage": region["sourcePage"],
                    "assetImage": region["assetImage"],
                    "assetPixelBox": list(asset_pixel_box),
                    "status": "rejected",
                    "reason": f"Asset crop is smaller than {args.minimum_pixels} pixels"
                })
                skipped += 1
                continue
            asset_crop = image.crop(asset_pixel_box)
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_crop.save(asset_path, format="PNG", optimize=True)
            result = dict(region)
            result["status"] = "created"
            result["assetPixelBox"] = list(asset_pixel_box)
            result["assetQuality"] = crop_quality(asset_path, asset_crop)
            result["contextPixelBox"] = None
            result["contextQuality"] = None
            if region["contextRegion"] is not None:
                context_pixel_box = normalized_pixel_box(region["contextRegion"], image.width, image.height)
                context_crop = image.crop(context_pixel_box)
                context_path = resolve_output_path(
                    output_dir, region["contextImage"], f"{region['occurrenceId']}.contextImage",
                    must_exist=False
                )
                require(not context_path.is_symlink(),
                        f"{region['occurrenceId']}.contextImage cannot be a symlink")
                if context_path.exists():
                    require(context_path.is_file(),
                            f"{region['occurrenceId']}.contextImage must be a regular file")
                    context_path.unlink()
                context_path.parent.mkdir(parents=True, exist_ok=True)
                context_crop.save(context_path, format="PNG", optimize=True)
                result["contextPixelBox"] = list(context_pixel_box)
                result["contextQuality"] = crop_quality(context_path, context_crop)
                context_crop.close()
            asset_crop.close()
            results.append(result)
    finally:
        if image is not None:
            image.close()
    write_json(output_dir / "diagnostics" / "crop-results.json", {
        "schemaVersion": CROP_RESULT_VERSION,
        "crops": results
    })
    created = len(results) - skipped
    print(f"Created {created} asset crop(s) and "
          f"{sum(item.get('status') == 'created' and item['contextImage'] is not None for item in results)} "
          f"context crop(s); skipped {skipped} undersized region(s)")


def hamming_distance(first: str, second: str) -> int:
    return (int(first, 16) ^ int(second, 16)).bit_count()


def command_duplicates(args: argparse.Namespace) -> None:
    output_dir = resolve_user_path(args.output_dir, "output-dir")
    crop_results_path = Path(args.crop_results).resolve()
    crop_results = load_json(crop_results_path)
    require(isinstance(crop_results, dict) and crop_results.get("schemaVersion") == CROP_RESULT_VERSION,
            f"Crop result schemaVersion must be {CROP_RESULT_VERSION}")
    records = crop_results.get("crops")
    require(isinstance(records, list), "Crop results must contain a crops array")
    crops: list[dict[str, Any]] = []
    for index, crop in enumerate(records):
        require(isinstance(crop, dict), f"crops[{index}] must be an object")
        require_id(crop.get("assetId"), f"crops[{index}].assetId")
        require_id(crop.get("occurrenceId"), f"crops[{index}].occurrenceId")
        status_value = crop.get("status", "created")
        require(status_value in {"created", "rejected", "skipped"}, f"crops[{index}].status is invalid")
        if status_value == "created":
            validate_quality(crop.get("assetQuality"), f"crops[{index}].assetQuality")
            crops.append(crop)
    parent = list(range(len(crops)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    for first_index in range(len(crops)):
        first_quality = crops[first_index]["assetQuality"]
        for second_index in range(first_index + 1, len(crops)):
            if crops[first_index]["assetId"] == crops[second_index]["assetId"]:
                continue
            second_quality = crops[second_index]["assetQuality"]
            if first_quality["sha256"] == second_quality["sha256"] and first_quality["sha256"] is not None:
                union(first_index, second_index)
                continue
            first_hash = first_quality["perceptualHash"]
            second_hash = second_quality["perceptualHash"]
            if first_hash is None or second_hash is None:
                continue
            if None in (first_quality["width"], first_quality["height"],
                        second_quality["width"], second_quality["height"]):
                continue
            first_ratio = first_quality["width"] / first_quality["height"]
            second_ratio = second_quality["width"] / second_quality["height"]
            ratio_difference = abs(first_ratio - second_ratio) / max(first_ratio, second_ratio)
            if ratio_difference <= 0.08 and hamming_distance(first_hash, second_hash) <= args.threshold:
                union(first_index, second_index)
    components: dict[int, list[int]] = {}
    for index in range(len(crops)):
        components.setdefault(find(index), []).append(index)
    suggestions: list[dict[str, Any]] = []
    for members in components.values():
        if len(members) < 2:
            continue
        asset_ids = sorted({crops[index]["assetId"] for index in members})
        if len(asset_ids) < 2:
            continue
        hashes = {crops[index]["assetQuality"]["sha256"] for index in members}
        exact = len(hashes) == 1 and None not in hashes
        distances = []
        for first_position, first_index in enumerate(members):
            for second_index in members[first_position + 1:]:
                first_hash = crops[first_index]["assetQuality"]["perceptualHash"]
                second_hash = crops[second_index]["assetQuality"]["perceptualHash"]
                if first_hash is not None and second_hash is not None:
                    distances.append(hamming_distance(first_hash, second_hash))
        maximum_distance = max(distances, default=0)
        suggestions.append({
            "suggestionId": f"duplicate-suggestion-{len(suggestions) + 1:04d}",
            "matchType": "exact" if exact else "near-duplicate",
            "assetIds": asset_ids,
            "occurrenceIds": sorted({crops[index]["occurrenceId"] for index in members}),
            "confidence": 1.0 if exact else round(max(0.5, 1 - maximum_distance / 64), 3),
            "maximumPerceptualDistance": maximum_distance,
            "requiresSemanticReview": not exact
        })
    result = {
        "schemaVersion": DUPLICATE_RESULT_VERSION,
        "cropResultsSha256": file_sha256(crop_results_path),
        "threshold": args.threshold,
        "suggestions": suggestions,
        "note": "Near-duplicate suggestions are candidates and require semantic review before merging assets."
    }
    destination = output_dir / "diagnostics" / "duplicate-suggestions.json"
    write_json(destination, result)
    print(f"Created {len(suggestions)} duplicate suggestion(s) in {destination}")


def write_validation_report(output_dir: Path, manifest_path: Path, counts: dict[str, Any]) -> Path:
    report_path = output_dir / "diagnostics" / "validation-report.json"
    write_json(report_path, {
        "schemaVersion": "semantic-pdf-image-validation/1.0",
        "validatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest": manifest_path.relative_to(output_dir).as_posix(),
        "valid": True,
        "counts": counts,
        "errors": []
    })
    return report_path


def command_validate(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest).resolve()
    output_dir = resolve_user_path(args.output_dir, "output-dir") if args.output_dir else None
    counts = validate_manifest_data(load_json(manifest_path), output_dir)
    if output_dir is not None:
        require(manifest_path.is_relative_to(output_dir), "Manifest must be inside the output directory")
        write_validation_report(output_dir, manifest_path, counts)
    print("Manifest is valid: " + ", ".join(f"{key}={value}" for key, value in counts.items()))


def manifest_artifact_paths(manifest: dict[str, Any]) -> set[str]:
    paths = {
        page["image"]
        for document in manifest["documents"]
        for page in document["pages"]
    }
    for asset in manifest["assets"]:
        for occurrence in asset["occurrences"]:
            paths.add(occurrence["assetImage"])
            paths.add(occurrence["fullPageFallback"])
            if occurrence["contextImage"] is not None:
                paths.add(occurrence["contextImage"])
    return paths


def require_archive_file(output_dir: Path, relative_path: str) -> tuple[Path, str]:
    archive_name = str(safe_relative_path(relative_path, f"Archive entry {relative_path}"))
    source = resolve_output_path(output_dir, archive_name, f"Archive entry {archive_name}")
    current = output_dir.resolve()
    for part in PurePosixPath(archive_name).parts:
        current /= part
        require(not current.is_symlink(), f"Archive entry cannot traverse a symlink: {archive_name}")
    require(stat.S_ISREG(source.stat(follow_symlinks=False).st_mode),
            f"Archive entry must be a regular file: {archive_name}")
    require(source.resolve().is_relative_to(output_dir.resolve()),
            f"Archive entry must stay inside the output directory: {archive_name}")
    return source, archive_name


def command_package(args: argparse.Namespace) -> None:
    output_dir = resolve_user_path(args.output_dir, "output-dir")
    manifest_argument = Path(args.manifest)
    manifest_path = manifest_argument.resolve()
    require(output_dir.is_dir(), "Output directory does not exist")
    require(manifest_argument.name == "manifest.json" and manifest_path == output_dir / "manifest.json",
            "Manifest must be exactly <output-dir>/manifest.json")
    require(not manifest_argument.is_symlink(), "manifest.json cannot be a symlink")
    require((output_dir / "summary.md").is_file(), "summary.md is required")
    manifest = load_json(manifest_path)
    manifest["generatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_json(manifest_path, manifest)
    counts = validate_manifest_data(manifest, output_dir)
    write_validation_report(output_dir, manifest_path, counts)
    archive = resolve_user_path(args.archive, "archive")
    require(not archive.is_relative_to(output_dir), "Archive must be outside the output directory")
    required_files = {
        "manifest.json",
        "summary.md",
        "diagnostics/region-proposals.json",
        "diagnostics/crop-results.json",
        "diagnostics/validation-report.json"
    }
    included_paths = required_files | manifest_artifact_paths(manifest)
    duplicate_suggestions = output_dir / "diagnostics" / "duplicate-suggestions.json"
    if duplicate_suggestions.is_file() and not duplicate_suggestions.is_symlink():
        duplicate_data = load_json(duplicate_suggestions)
        require(isinstance(duplicate_data, dict),
                "diagnostics/duplicate-suggestions.json must be an object")
        require(duplicate_data.get("schemaVersion") == DUPLICATE_RESULT_VERSION,
                f"Duplicate result schemaVersion must be {DUPLICATE_RESULT_VERSION}")
        crop_results_path = output_dir / "diagnostics" / "crop-results.json"
        if duplicate_data.get("cropResultsSha256") == file_sha256(crop_results_path):
            included_paths.add("diagnostics/duplicate-suggestions.json")
        else:
            print("Omitting stale diagnostics/duplicate-suggestions.json")
    archive_files = [require_archive_file(output_dir, path) for path in sorted(included_paths)]
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source, archive_name in archive_files:
            bundle.write(source, archive_name)
    print(f"Packaged {len(archive_files)} file(s) in {archive}")


def command_self_test(_: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        root = temporary_path / "output"
        page_path = root / "pages" / "test-document" / "page-0001.png"
        first_asset_path = root / "assets" / "test-document" / "asset-0001.png"
        second_asset_path = root / "assets" / "test-document" / "asset-0002.png"
        for path, content in (
            (page_path, PNG_SIGNATURE + b"test-page"),
            (first_asset_path, PNG_SIGNATURE + b"same-asset"),
            (second_asset_path, PNG_SIGNATURE + b"same-asset"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (root / "summary.md").write_text("# Self-test\n", encoding="utf-8")
        quality = {
            "width": 400,
            "height": 300,
            "fileBytes": first_asset_path.stat().st_size,
            "sha256": file_sha256(first_asset_path),
            "perceptualHash": "0123456789abcdef",
            "resolutionStatus": "sufficient"
        }

        def occurrence(number: int) -> dict[str, Any]:
            return {
                "id": f"test-occurrence-{number:04d}",
                "documentId": "test-document",
                "pageNumber": 1,
                "sourceRegion": [0.1, 0.1, 0.5, 0.5],
                "contextRegion": None,
                "assetImage": f"assets/test-document/asset-{number:04d}.png",
                "contextImage": None,
                "fullPageFallback": "pages/test-document/page-0001.png",
                "caption": None,
                "nearbyText": None,
                "quality": dict(quality),
                "extractionMethod": "native-vision",
                "confidence": 1.0,
                "status": "verified",
                "reviewReasons": []
            }

        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "generatedAt": None,
            "request": {
                "mode": "meaningful", "includeTypes": [], "excludeTypes": ["logo", "icon"],
                "includeDecorative": False, "preserveContext": True, "pageRanges": []
            },
            "documents": [{
                "id": "test-document", "sourceFile": "test.pdf", "sha256": None,
                "title": "Test", "languages": ["en"], "pageCount": 1,
                "pages": [{
                    "pageNumber": 1, "image": "pages/test-document/page-0001.png",
                    "width": None, "height": None, "status": "verified", "reviewReasons": []
                }]
            }],
            "assets": [
                {"id": "test-asset-0001", "assetType": "photo", "semanticRole": "informational",
                 "description": "Test asset", "labels": [], "keywords": ["test"],
                 "occurrences": [occurrence(1)], "duplicateGroupId": "duplicate-group-0001"},
                {"id": "test-asset-0002", "assetType": "photo", "semanticRole": "informational",
                 "description": "Test duplicate", "labels": [], "keywords": ["test"],
                 "occurrences": [occurrence(2)], "duplicateGroupId": "duplicate-group-0001"}
            ],
            "duplicateGroups": [{
                "id": "duplicate-group-0001", "canonicalAssetId": "test-asset-0001",
                "memberAssetIds": ["test-asset-0001", "test-asset-0002"],
                "matchType": "exact", "confidence": 1.0, "reviewed": True
            }],
            "exclusions": {"totalCandidates": 1, "byReason": {"decorative": 1}},
            "review": {"required": False, "assetIds": [], "occurrenceIds": [], "notes": []},
            "limitations": []
        }
        manifest_path = root / "manifest.json"
        write_json(manifest_path, manifest)
        validate_manifest_data(manifest, root)

        def expect_validation_error(callback: Any, label: str) -> None:
            try:
                callback()
            except ValidationError:
                return
            raise ValidationError(f"Self-test did not reject {label}")

        def expect_manifest_error(label: str, mutation: Any) -> None:
            candidate = copy.deepcopy(manifest)
            mutation(candidate)
            expect_validation_error(lambda: validate_manifest_data(candidate), label)

        expect_manifest_error("missing generatedAt", lambda value: value.pop("generatedAt"))
        expect_manifest_error("missing page width",
                              lambda value: value["documents"][0]["pages"][0].pop("width"))
        expect_manifest_error("missing page height",
                              lambda value: value["documents"][0]["pages"][0].pop("height"))
        expect_manifest_error("missing duplicateGroupId",
                              lambda value: value["assets"][0].pop("duplicateGroupId"))
        for quality_field in ("width", "height", "fileBytes", "sha256", "perceptualHash",
                              "resolutionStatus"):
            expect_manifest_error(
                f"missing quality {quality_field}",
                lambda value, key=quality_field: value["assets"][0]["occurrences"][0]["quality"].pop(key)
            )
        expect_manifest_error("unknown root property", lambda value: value.update({"unexpected": True}))
        expect_manifest_error(
            "unknown nested property",
            lambda value: value["assets"][0]["occurrences"][0]["quality"].update({"unexpected": True})
        )
        expect_manifest_error(
            "backslash path",
            lambda value: value["assets"][0]["occurrences"][0].update(
                {"assetImage": r"assets\test-document\asset-0001.png"}
            )
        )
        expect_manifest_error(
            "traversal path",
            lambda value: value["assets"][0]["occurrences"][0].update(
                {"assetImage": "assets/test-document/../asset-0001.png"}
            )
        )
        for label, page_range in (
            ("page range from zero", {"documentId": "test-document", "from": 0, "to": 1}),
            ("boolean page range", {"documentId": "test-document", "from": True, "to": 1}),
            ("reversed page range", {"documentId": "test-document", "from": 2, "to": 1}),
            ("page range past page count", {"documentId": "test-document", "from": 1, "to": 2}),
            ("unknown page-range document", {"documentId": "missing-document", "from": 1, "to": 1}),
        ):
            expect_manifest_error(
                label,
                lambda value, selected=page_range: value["request"].update({"pageRanges": [selected]})
            )
        bounded_manifest = copy.deepcopy(manifest)
        bounded_manifest["request"]["pageRanges"] = [
            {"documentId": "test-document", "from": 1, "to": 1}
        ]
        validate_manifest_data(bounded_manifest)
        expect_manifest_error(
            "incomplete full-document page coverage",
            lambda value: value["documents"][0].update({"pageCount": 2})
        )
        expect_manifest_error(
            "missing requested page record",
            lambda value: (
                value["documents"][0].update({"pageCount": 2}),
                value["request"].update({"pageRanges": [
                    {"documentId": "test-document", "from": 1, "to": 2}
                ]})
            )
        )
        expect_manifest_error(
            "extra page outside requested range",
            lambda value: (
                value["documents"][0].update({
                    "pageCount": 2,
                    "pages": value["documents"][0]["pages"] + [{
                        "pageNumber": 2,
                        "image": "pages/test-document/page-0002.png",
                        "width": None,
                        "height": None,
                        "status": "verified",
                        "reviewReasons": []
                    }]
                }),
                value["request"].update({"pageRanges": [
                    {"documentId": "test-document", "from": 1, "to": 1}
                ]})
            )
        )
        expect_manifest_error(
            "boolean occurrence page number",
            lambda value: value["assets"][0]["occurrences"][0].update({"pageNumber": True})
        )
        expect_manifest_error(
            "duplicate occurrence asset output",
            lambda value: value["assets"][1]["occurrences"][0].update(
                {"assetImage": "assets/test-document/asset-0001.png"}
            )
        )
        expect_manifest_error(
            "duplicate occurrence context output",
            lambda value: [
                occurrence_value.update({
                    "contextRegion": [0.1, 0.1, 0.5, 0.5],
                    "contextImage": "context/test-document/shared.png"
                })
                for asset_value in value["assets"]
                for occurrence_value in asset_value["occurrences"]
            ]
        )
        expect_manifest_error(
            "unreported page review state",
            lambda value: value["documents"][0]["pages"][0].update(
                {"status": "review-required", "reviewReasons": ["Check rendered page"]}
            )
        )
        page_review_manifest = copy.deepcopy(manifest)
        page_review_manifest["documents"][0]["pages"][0].update(
            {"status": "review-required", "reviewReasons": ["Check rendered page"]}
        )
        page_review_manifest["review"]["required"] = True
        validate_manifest_data(page_review_manifest)
        require(parse_page_range("2-4") == (2, 4), "Self-test page-range parser changed values")
        ranges, selected_pages = selected_render_pages(5, [(2, 3), (5, 5)])
        require(ranges == [(2, 3), (5, 5)] and selected_pages == [2, 3, 5],
                "Self-test render page selection changed values")
        expect_validation_error(
            lambda: selected_render_pages(0, None),
            "empty PDF before workspace cleanup"
        )
        expect_validation_error(
            lambda: selected_render_pages(2, [(1, 3)]),
            "out-of-range selection before workspace cleanup"
        )
        for invalid_range in ("0-1", "3-2", "1", "true-2"):
            try:
                parse_page_range(invalid_range)
            except argparse.ArgumentTypeError:
                pass
            else:
                raise ValidationError(f"Self-test accepted invalid render page range: {invalid_range}")

        cleanup_root = temporary_path / "cleanup-output"
        cleanup_files = (
            cleanup_root / "summary.md",
            cleanup_root / "diagnostics" / "region-proposals.json",
            cleanup_root / "diagnostics" / "crop-results.json",
            cleanup_root / "diagnostics" / "duplicate-suggestions.json",
            cleanup_root / "diagnostics" / "validation-report.json",
        )
        for cleanup_file in cleanup_files:
            cleanup_file.parent.mkdir(parents=True, exist_ok=True)
            cleanup_file.write_text("stale", encoding="utf-8")
        clear_current_run_metadata(cleanup_root)
        require(not any(path.exists() for path in cleanup_files),
                "Self-test did not clear stale current-run metadata")

        write_target = temporary_path / "write-target.json"
        write_target.write_text("unchanged", encoding="utf-8")
        write_link = temporary_path / "write-link.json"
        try:
            write_link.symlink_to(write_target)
        except OSError:
            pass
        else:
            expect_validation_error(
                lambda: write_json(write_link, {"unsafe": True}),
                "JSON destination symlink"
            )
            require(write_target.read_text(encoding="utf-8") == "unchanged",
                    "Self-test JSON symlink target was overwritten")

        page_target = temporary_path / "page-target"
        page_target.mkdir()
        outside_page = page_target / "page-0001.png"
        outside_page.write_bytes(PNG_SIGNATURE + b"outside")
        linked_pages_root = temporary_path / "linked-pages-output"
        (linked_pages_root / "pages").mkdir(parents=True)
        linked_page_dir = linked_pages_root / "pages" / "test-document"
        try:
            linked_page_dir.symlink_to(page_target, target_is_directory=True)
        except OSError:
            pass
        else:
            expect_validation_error(
                lambda: prepare_page_directory(linked_pages_root, "test-document"),
                "render page-directory symlink"
            )
            require(outside_page.is_file(), "Self-test render cleanup deleted an external page")

        output_target = temporary_path / "output-target"
        output_target.mkdir()
        output_link = temporary_path / "output-link"
        archive_parent_target = temporary_path / "archive-parent-target"
        archive_parent_target.mkdir()
        archive_parent_link = temporary_path / "archive-parent-link"
        try:
            output_link.symlink_to(output_target, target_is_directory=True)
            archive_parent_link.symlink_to(archive_parent_target, target_is_directory=True)
        except OSError:
            pass
        else:
            expect_validation_error(
                lambda: resolve_user_path(str(output_link), "output-dir"),
                "output-directory symlink"
            )
            expect_validation_error(
                lambda: resolve_user_path(str(archive_parent_link / "result.zip"), "archive"),
                "archive parent symlink"
            )
        expect_manifest_error(
            "non-canonical manifest page image",
            lambda value: value["documents"][0]["pages"][0].update(
                {"image": "pages/test-document/other.png"}
            )
        )
        mismatched_regions = {
            "schemaVersion": REGION_VERSION,
            "documents": [{
                "documentId": "test-document",
                "pages": [{"pageNumber": 1, "image": "pages/test-document/other.png", "regions": []}]
            }]
        }
        expect_validation_error(
            lambda: validate_region_proposals(mismatched_regions),
            "non-canonical region proposal page image"
        )
        first_asset_path.write_bytes(b"not-a-png")
        expect_validation_error(
            lambda: validate_manifest_data(manifest, root),
            "invalid PNG artifact"
        )
        first_asset_path.write_bytes(PNG_SIGNATURE + b"same-asset")

        crop_results_path = root / "diagnostics" / "crop-results.json"
        write_json(crop_results_path, {
            "schemaVersion": CROP_RESULT_VERSION,
            "crops": [
                {"assetId": "test-asset-0001", "occurrenceId": "test-occurrence-0001",
                 "status": "created", "assetQuality": quality},
                {"assetId": "test-asset-0002", "occurrenceId": "test-occurrence-0002",
                 "status": "created", "assetQuality": quality}
            ]
        })
        command_duplicates(argparse.Namespace(
            output_dir=str(root), crop_results=str(crop_results_path), threshold=6
        ))
        suggestions = load_json(root / "diagnostics" / "duplicate-suggestions.json")["suggestions"]
        require(len(suggestions) == 1 and suggestions[0]["matchType"] == "exact",
                "Self-test exact duplicate was not detected")
        same_asset_results = copy.deepcopy(load_json(crop_results_path))
        same_asset_results["crops"][1]["assetId"] = "test-asset-0001"
        write_json(crop_results_path, same_asset_results)
        command_duplicates(argparse.Namespace(
            output_dir=str(root), crop_results=str(crop_results_path), threshold=6
        ))
        suggestions = load_json(root / "diagnostics" / "duplicate-suggestions.json")["suggestions"]
        require(not suggestions, "Self-test emitted a same-asset duplicate suggestion")
        write_json(crop_results_path, {
            "schemaVersion": CROP_RESULT_VERSION,
            "crops": [
                {"assetId": "test-asset-0001", "occurrenceId": "test-occurrence-0001",
                 "status": "created", "assetQuality": quality},
                {"assetId": "test-asset-0002", "occurrenceId": "test-occurrence-0002",
                 "status": "created", "assetQuality": quality}
            ]
        })
        command_duplicates(argparse.Namespace(
            output_dir=str(root), crop_results=str(crop_results_path), threshold=6
        ))
        write_json(root / "diagnostics" / "region-proposals.json", {
            "schemaVersion": REGION_VERSION,
            "documents": [{
                "documentId": "test-document",
                "pages": [{
                    "pageNumber": 1,
                    "image": "pages/test-document/page-0001.png",
                    "regions": []
                }]
            }]
        })
        stale_path = root / "assets" / "test-document" / "stale.png"
        stale_path.write_bytes(b"stale")
        alternate_manifest = root / "alternate.json"
        write_json(alternate_manifest, manifest)
        expect_validation_error(
            lambda: command_package(argparse.Namespace(
                output_dir=str(root), manifest=str(alternate_manifest),
                archive=str(temporary_path / "wrong-name.zip")
            )),
            "incorrect manifest filename"
        )
        expect_validation_error(
            lambda: command_package(argparse.Namespace(
                output_dir=str(root), manifest=str(manifest_path),
                archive=str(root / "inside.zip")
            )),
            "archive inside the output directory"
        )
        archive_target = temporary_path / "archive-target.zip"
        archive_symlink = temporary_path / "archive-link.zip"
        try:
            archive_symlink.symlink_to(archive_target)
        except OSError:
            pass
        else:
            expect_validation_error(
                lambda: command_package(argparse.Namespace(
                    output_dir=str(root), manifest=str(manifest_path),
                    archive=str(archive_symlink)
                )),
                "archive symlink"
            )
            require(not archive_target.exists(), "Self-test archive symlink target was created")
        archive = temporary_path / "self-test.zip"
        command_package(argparse.Namespace(
            output_dir=str(root), manifest=str(manifest_path), archive=str(archive)
        ))
        with zipfile.ZipFile(archive) as bundle:
            required = {
                "manifest.json", "summary.md", "pages/test-document/page-0001.png",
                "assets/test-document/asset-0001.png",
                "diagnostics/region-proposals.json",
                "diagnostics/crop-results.json",
                "diagnostics/validation-report.json",
                "diagnostics/duplicate-suggestions.json"
            }
            require(required.issubset(bundle.namelist()), "Self-test archive is incomplete")
            require("assets/test-document/stale.png" not in bundle.namelist(),
                    "Self-test archive included an unreferenced stale file")
        write_json(crop_results_path, {
            "schemaVersion": CROP_RESULT_VERSION,
            "crops": []
        })
        stale_archive = temporary_path / "stale-suggestions.zip"
        command_package(argparse.Namespace(
            output_dir=str(root), manifest=str(manifest_path), archive=str(stale_archive)
        ))
        with zipfile.ZipFile(stale_archive) as bundle:
            require("diagnostics/duplicate-suggestions.json" not in bundle.namelist(),
                    "Self-test archive included stale duplicate suggestions")

        try:
            from PIL import Image
        except ImportError:
            Image = None
        if Image is not None:
            crop_root = temporary_path / "crop-output"
            crop_page = crop_root / "pages" / "crop-document" / "page-0001.png"
            crop_page.parent.mkdir(parents=True, exist_ok=True)
            source_image = Image.new("RGB", (100, 100), color="white")
            source_image.save(crop_page, format="PNG")
            source_image.close()
            crop_proposals = crop_root / "diagnostics" / "region-proposals.json"
            write_json(crop_proposals, {
                "schemaVersion": REGION_VERSION,
                "documents": [{
                    "documentId": "crop-document",
                    "pages": [{
                        "pageNumber": 1,
                        "image": "pages/crop-document/page-0001.png",
                        "regions": [
                            {
                                "assetId": "crop-document-asset-0001",
                                "occurrenceId": "crop-document-occurrence-0001",
                                "assetType": "photo",
                                "assetBox": [0.1, 0.1, 0.8, 0.8],
                                "contextBox": None,
                                "assetOutput": "assets/crop-document/asset-0001.png",
                                "contextOutput": None,
                                "reason": "Valid self-test crop"
                            },
                            {
                                "assetId": "crop-document-asset-0002",
                                "occurrenceId": "crop-document-occurrence-0002",
                                "assetType": "icon",
                                "assetBox": [0.0, 0.0, 0.1, 0.1],
                                "contextBox": None,
                                "assetOutput": "assets/crop-document/asset-0002.png",
                                "contextOutput": None,
                                "reason": "Undersized self-test crop"
                            }
                        ]
                    }]
                }]
            })
            command_crop(argparse.Namespace(
                output_dir=str(crop_root), regions=str(crop_proposals), minimum_pixels=20
            ))
            crop_records = load_json(crop_root / "diagnostics" / "crop-results.json")["crops"]
            require([item["status"] for item in crop_records] == ["created", "rejected"],
                    "Self-test crop statuses are not deterministic")
            require((crop_root / "assets" / "crop-document" / "asset-0001.png").is_file(),
                    "Self-test valid crop was not created")
            require(not (crop_root / "assets" / "crop-document" / "asset-0002.png").exists(),
                    "Self-test undersized crop file was created")
    print("Self-test passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="Render selected PDF pages to PNG")
    render.add_argument("--input", required=True)
    render.add_argument("--output-dir", required=True)
    render.add_argument("--document-id", required=True)
    render.add_argument("--dpi", type=int, default=220, choices=range(120, 401), metavar="120-400")
    render.add_argument("--page-range", dest="page_ranges", type=parse_page_range, action="append",
                        metavar="FROM-TO")
    render.set_defaults(handler=command_render)

    crop = commands.add_parser("crop", help="Create asset and context crops from normalized proposals")
    crop.add_argument("--output-dir", required=True)
    crop.add_argument("--regions", required=True)
    crop.add_argument("--minimum-pixels", type=int, default=32, choices=range(1, 513), metavar="1-512")
    crop.set_defaults(handler=command_crop)

    duplicates = commands.add_parser("duplicates", help="Suggest exact and near-duplicate assets")
    duplicates.add_argument("--output-dir", required=True)
    duplicates.add_argument("--crop-results", required=True)
    duplicates.add_argument("--threshold", type=int, default=6, choices=range(0, 17), metavar="0-16")
    duplicates.set_defaults(handler=command_duplicates)

    validate = commands.add_parser("validate", help="Validate a normalized manifest")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--output-dir")
    validate.set_defaults(handler=command_validate)

    package = commands.add_parser("package", help="Validate and package extraction results")
    package.add_argument("--output-dir", required=True)
    package.add_argument("--manifest", required=True)
    package.add_argument("--archive", required=True)
    package.set_defaults(handler=command_package)

    self_test = commands.add_parser("self-test", help="Run dependency-free contract and packaging tests")
    self_test.set_defaults(handler=command_self_test)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        args.handler(args)
        return 0
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())