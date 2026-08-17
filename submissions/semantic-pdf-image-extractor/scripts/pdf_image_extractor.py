#!/usr/bin/env python3
"""Deterministic file operations for the Semantic PDF Image Extractor skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import tempfile
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


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot read valid JSON from {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def safe_relative_path(value: Any, field: str) -> PurePosixPath:
    require(isinstance(value, str) and bool(value), f"{field} must be a non-empty relative path")
    require("\\" not in value and not any(ord(character) < 32 for character in value),
            f"{field} must use a safe path with forward slashes")
    path = PurePosixPath(value)
    require(value != "." and not path.is_absolute() and ".." not in path.parts,
            f"{field} must stay inside the output directory: {value}")
    require(re.match(r"^[A-Za-z]:", value) is None,
            f"{field} must stay inside the output directory: {value}")
    return path


def require_id(value: Any, field: str) -> str:
    require(isinstance(value, str) and ID_PATTERN.fullmatch(value) is not None,
            f"{field} must use lowercase letters, digits, and hyphens")
    return value


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
    require(isinstance(value, dict), f"{field} must be an object")
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
    require(isinstance(manifest, dict), "Manifest root must be an object")
    require(manifest.get("schemaVersion") == SCHEMA_VERSION, f"schemaVersion must be {SCHEMA_VERSION}")
    generated_at = manifest.get("generatedAt")
    if generated_at is not None:
        require(isinstance(generated_at, str), "generatedAt must be null or an ISO timestamp")
        try:
            datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("generatedAt must be null or an ISO timestamp") from exc

    request = manifest.get("request")
    require(isinstance(request, dict), "request must be an object")
    require(request.get("mode") in {"meaningful", "all-visuals", "photos", "diagrams", "charts", "custom"},
            "request.mode is invalid")
    include_types = request.get("includeTypes")
    exclude_types = request.get("excludeTypes")
    require(isinstance(include_types, list) and set(include_types).issubset(VALID_ASSET_TYPES)
            and len(include_types) == len(set(include_types)), "request.includeTypes is invalid")
    require(isinstance(exclude_types, list) and set(exclude_types).issubset(VALID_ASSET_TYPES)
            and len(exclude_types) == len(set(exclude_types)), "request.excludeTypes is invalid")
    require(set(include_types).isdisjoint(exclude_types), "A type cannot be both included and excluded")
    require(isinstance(request.get("includeDecorative"), bool), "request.includeDecorative must be boolean")
    require(isinstance(request.get("preserveContext"), bool), "request.preserveContext must be boolean")
    require(isinstance(request.get("pageRanges"), list), "request.pageRanges must be an array")

    documents = manifest.get("documents")
    require(isinstance(documents, list) and bool(documents), "documents must contain at least one document")
    document_ids: set[str] = set()
    page_lookup: dict[tuple[str, int], str] = {}
    referenced_paths: set[str] = set()
    page_count = 0
    for document_index, document in enumerate(documents):
        field = f"documents[{document_index}]"
        require(isinstance(document, dict), f"{field} must be an object")
        document_id = require_id(document.get("id"), f"{field}.id")
        require(document_id not in document_ids, f"Duplicate document id: {document_id}")
        document_ids.add(document_id)
        require(isinstance(document.get("sourceFile"), str) and bool(document["sourceFile"]),
                f"{field}.sourceFile is required")
        sha256 = document.get("sha256")
        require(sha256 is None or (isinstance(sha256, str) and HASH_PATTERN.fullmatch(sha256) is not None),
                f"{field}.sha256 must be null or a lowercase SHA-256")
        require(document.get("title") is None or isinstance(document.get("title"), str),
                f"{field}.title must be null or a string")
        require_string_array(document.get("languages"), f"{field}.languages", unique=True)
        declared_page_count = document.get("pageCount")
        require(isinstance(declared_page_count, int) and not isinstance(declared_page_count, bool)
                and declared_page_count >= 1, f"{field}.pageCount must be a positive integer")
        pages = document.get("pages")
        require(isinstance(pages, list) and bool(pages), f"{field}.pages must contain at least one page")
        require(len(pages) <= declared_page_count, f"{field}.pages exceeds the declared page count")
        numbers: set[int] = set()
        for page_index, page in enumerate(pages):
            page_field = f"{field}.pages[{page_index}]"
            require(isinstance(page, dict), f"{page_field} must be an object")
            number = page.get("pageNumber")
            require(isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= declared_page_count,
                    f"{page_field}.pageNumber is invalid")
            require(number not in numbers, f"Duplicate page number {number} in {document_id}")
            numbers.add(number)
            image = str(safe_relative_path(page.get("image"), f"{page_field}.image"))
            require(image.startswith(f"pages/{document_id}/") and image.lower().endswith(".png"),
                    f"{page_field}.image must be a PNG below pages/{document_id}/")
            require(page.get("status") in VALID_STATUSES, f"{page_field}.status is invalid")
            reasons = require_string_array(page.get("reviewReasons"), f"{page_field}.reviewReasons")
            if page["status"] != "verified":
                require(bool(reasons), f"{page_field} needs at least one review reason")
            for dimension in ("width", "height"):
                value = page.get(dimension)
                require(value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 1),
                        f"{page_field}.{dimension} must be null or a positive integer")
            page_lookup[(document_id, number)] = image
            referenced_paths.add(image)
            page_count += 1

    for range_index, page_range in enumerate(request["pageRanges"]):
        field = f"request.pageRanges[{range_index}]"
        require(isinstance(page_range, dict), f"{field} must be an object")
        document_id = require_id(page_range.get("documentId"), f"{field}.documentId")
        require(document_id in document_ids, f"{field}.documentId is unknown")
        start, end = page_range.get("from"), page_range.get("to")
        require(isinstance(start, int) and not isinstance(start, bool) and start >= 1,
                f"{field}.from is invalid")
        require(isinstance(end, int) and not isinstance(end, bool) and end >= start,
                f"{field}.to is invalid")

    assets = manifest.get("assets")
    require(isinstance(assets, list), "assets must be an array")
    asset_ids: set[str] = set()
    occurrence_ids: set[str] = set()
    occurrence_asset: dict[str, str] = {}
    review_required_occurrences: set[str] = set()
    asset_group_ids: dict[str, str | None] = {}
    for asset_index, asset in enumerate(assets):
        field = f"assets[{asset_index}]"
        require(isinstance(asset, dict), f"{field} must be an object")
        asset_id = require_id(asset.get("id"), f"{field}.id")
        require(asset_id not in asset_ids, f"Duplicate asset id: {asset_id}")
        asset_ids.add(asset_id)
        require(asset.get("assetType") in VALID_ASSET_TYPES, f"{field}.assetType is invalid")
        require(asset.get("semanticRole") in VALID_ROLES, f"{field}.semanticRole is invalid")
        require(asset.get("description") is None or isinstance(asset.get("description"), str),
                f"{field}.description must be null or a string")
        require_string_array(asset.get("labels"), f"{field}.labels", unique=True)
        require_string_array(asset.get("keywords"), f"{field}.keywords", unique=True)
        duplicate_group_id = asset.get("duplicateGroupId")
        if duplicate_group_id is not None:
            require_id(duplicate_group_id, f"{field}.duplicateGroupId")
        asset_group_ids[asset_id] = duplicate_group_id
        occurrences = asset.get("occurrences")
        require(isinstance(occurrences, list) and bool(occurrences), f"{field}.occurrences cannot be empty")
        for occurrence_index, occurrence in enumerate(occurrences):
            occurrence_field = f"{field}.occurrences[{occurrence_index}]"
            require(isinstance(occurrence, dict), f"{occurrence_field} must be an object")
            occurrence_id = require_id(occurrence.get("id"), f"{occurrence_field}.id")
            require(occurrence_id not in occurrence_ids, f"Duplicate occurrence id: {occurrence_id}")
            occurrence_ids.add(occurrence_id)
            occurrence_asset[occurrence_id] = asset_id
            document_id = require_id(occurrence.get("documentId"), f"{occurrence_field}.documentId")
            page_number = occurrence.get("pageNumber")
            require((document_id, page_number) in page_lookup,
                    f"{occurrence_field} does not identify a rendered source page")
            source_region = validate_box(occurrence.get("sourceRegion"), f"{occurrence_field}.sourceRegion")
            context_region = validate_box(occurrence.get("contextRegion"),
                                          f"{occurrence_field}.contextRegion", nullable=True)
            if context_region is not None:
                require(contains_box(context_region, source_region),
                        f"{occurrence_field}.contextRegion must contain sourceRegion")
            asset_image = str(safe_relative_path(occurrence.get("assetImage"),
                                                 f"{occurrence_field}.assetImage"))
            require(asset_image.startswith(f"assets/{document_id}/") and asset_image.lower().endswith(".png"),
                    f"{occurrence_field}.assetImage must be a PNG below assets/{document_id}/")
            context_image_value = occurrence.get("contextImage")
            require((context_region is None) == (context_image_value is None),
                    f"{occurrence_field}.contextImage and contextRegion must be provided together")
            context_image: str | None = None
            if context_image_value is not None:
                context_image = str(safe_relative_path(context_image_value,
                                                       f"{occurrence_field}.contextImage"))
                require(context_image.startswith(f"context/{document_id}/")
                        and context_image.lower().endswith(".png"),
                        f"{occurrence_field}.contextImage must be a PNG below context/{document_id}/")
            fallback = str(safe_relative_path(occurrence.get("fullPageFallback"),
                                              f"{occurrence_field}.fullPageFallback"))
            require(fallback == page_lookup[(document_id, page_number)],
                    f"{occurrence_field}.fullPageFallback must identify its source page")
            for text_field in ("caption", "nearbyText"):
                value = occurrence.get(text_field)
                require(value is None or isinstance(value, str),
                        f"{occurrence_field}.{text_field} must be null or a string")
            require(occurrence.get("extractionMethod") in VALID_METHODS,
                    f"{occurrence_field}.extractionMethod is invalid")
            confidence = occurrence.get("confidence")
            require(isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
                    and 0 <= confidence <= 1, f"{occurrence_field}.confidence must be between 0 and 1")
            status = occurrence.get("status")
            require(status in VALID_STATUSES, f"{occurrence_field}.status is invalid")
            reasons = require_string_array(occurrence.get("reviewReasons"),
                                           f"{occurrence_field}.reviewReasons")
            if status != "verified":
                require(bool(reasons), f"{occurrence_field} needs at least one review reason")
            if status == "review-required":
                review_required_occurrences.add(occurrence_id)
            referenced_paths.update({asset_image, fallback})
            if context_image is not None:
                referenced_paths.add(context_image)
            resolved_asset = output_dir / Path(asset_image) if output_dir is not None else None
            validate_quality(occurrence.get("quality"), f"{occurrence_field}.quality", resolved_asset)

    duplicate_groups = manifest.get("duplicateGroups")
    require(isinstance(duplicate_groups, list), "duplicateGroups must be an array")
    group_ids: set[str] = set()
    group_members: dict[str, set[str]] = {}
    for group_index, group in enumerate(duplicate_groups):
        field = f"duplicateGroups[{group_index}]"
        require(isinstance(group, dict), f"{field} must be an object")
        group_id = require_id(group.get("id"), f"{field}.id")
        require(group_id not in group_ids, f"Duplicate duplicate-group id: {group_id}")
        group_ids.add(group_id)
        canonical = require_id(group.get("canonicalAssetId"), f"{field}.canonicalAssetId")
        members = group.get("memberAssetIds")
        require(isinstance(members, list) and len(members) >= 2,
                f"{field}.memberAssetIds must contain at least two assets")
        require(all(isinstance(item, str) for item in members) and len(members) == len(set(members)),
                f"{field}.memberAssetIds must contain unique asset IDs")
        require(set(members).issubset(asset_ids) and canonical in members,
                f"{field} references unknown assets or omits its canonical asset")
        require(group.get("matchType") in {"exact", "near-duplicate", "semantic-variant"},
                f"{field}.matchType is invalid")
        confidence = group.get("confidence")
        require(isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
                and 0 <= confidence <= 1, f"{field}.confidence must be between 0 and 1")
        require(isinstance(group.get("reviewed"), bool), f"{field}.reviewed must be boolean")
        group_members[group_id] = set(members)
    for asset_id, group_id in asset_group_ids.items():
        if group_id is not None:
            require(group_id in group_members and asset_id in group_members[group_id],
                    f"Asset {asset_id} has an inconsistent duplicateGroupId")
    for group_id, members in group_members.items():
        require(all(asset_group_ids[member] == group_id for member in members),
                f"Every member of {group_id} must reference that duplicate group")

    exclusions = manifest.get("exclusions")
    require(isinstance(exclusions, dict), "exclusions must be an object")
    total_candidates = exclusions.get("totalCandidates")
    by_reason = exclusions.get("byReason")
    require(isinstance(total_candidates, int) and not isinstance(total_candidates, bool)
            and total_candidates >= 0, "exclusions.totalCandidates must be a non-negative integer")
    require(isinstance(by_reason, dict) and all(isinstance(key, str) and bool(key) for key in by_reason),
            "exclusions.byReason must be an object with non-empty reason keys")
    require(all(isinstance(value, int) and not isinstance(value, bool) and value >= 0
                for value in by_reason.values()), "exclusions.byReason counts must be non-negative integers")
    require(total_candidates == sum(by_reason.values()),
            "exclusions.totalCandidates must equal the sum of exclusions.byReason")

    review = manifest.get("review")
    require(isinstance(review, dict), "review must be an object")
    review_asset_ids = review.get("assetIds")
    review_occurrence_ids = review.get("occurrenceIds")
    require(isinstance(review_asset_ids, list) and len(review_asset_ids) == len(set(review_asset_ids))
            and set(review_asset_ids).issubset(asset_ids), "review.assetIds contains duplicates or unknown assets")
    require(isinstance(review_occurrence_ids, list)
            and len(review_occurrence_ids) == len(set(review_occurrence_ids))
            and set(review_occurrence_ids).issubset(occurrence_ids),
            "review.occurrenceIds contains duplicates or unknown occurrences")
    notes = require_string_array(review.get("notes"), "review.notes")
    require(review_required_occurrences.issubset(set(review_occurrence_ids)),
            "Every review-required occurrence must appear in review.occurrenceIds")
    required_assets = {occurrence_asset[item] for item in review_required_occurrences}
    require(required_assets.issubset(set(review_asset_ids)),
            "Assets with review-required occurrences must appear in review.assetIds")
    expected_review = bool(review_asset_ids or review_occurrence_ids or notes)
    require(review.get("required") is expected_review,
            "review.required must reflect the review IDs and notes")
    require_string_array(manifest.get("limitations"), "limitations")

    if output_dir is not None:
        missing = [path for path in sorted(referenced_paths) if not (output_dir / Path(path)).is_file()]
        require(not missing, "Referenced files are missing: " + ", ".join(missing))
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
            require(image.startswith(f"pages/{document_id}/") and image.lower().endswith(".png"),
                    f"{page_field}.image must be a PNG below pages/{document_id}/")
            if output_dir is not None:
                require((output_dir / Path(image)).is_file(), f"Page image is missing: {image}")
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
    output_dir = Path(args.output_dir).resolve()
    pages_dir = output_dir / "pages" / document_id
    pages_dir.mkdir(parents=True, exist_ok=True)
    for old_page in pages_dir.glob("page-*.png"):
        old_page.unlink()
    try:
        document = pdfium.PdfDocument(str(input_path))
    except Exception as exc:
        raise ValidationError(f"Cannot open PDF; it may be corrupt or encrypted: {exc}") from exc
    require(len(document) > 0, "PDF contains no pages")
    scale = args.dpi / 72
    rendered_pages: list[dict[str, Any]] = []
    for page_index in range(len(document)):
        page = document[page_index]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
        destination = pages_dir / f"page-{page_index + 1:04d}.png"
        image.save(destination, format="PNG", optimize=True)
        rendered_pages.append({
            "pageNumber": page_index + 1,
            "image": destination.relative_to(output_dir).as_posix(),
            "width": image.width,
            "height": image.height,
            "fileBytes": destination.stat().st_size,
            "sha256": file_sha256(destination)
        })
        page.close()
    document.close()
    result = {
        "documentId": document_id,
        "sourceFile": input_path.name,
        "sourceSha256": file_sha256(input_path),
        "pageCount": len(rendered_pages),
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
    output_dir = Path(args.output_dir).resolve()
    require(output_dir.is_dir(), "Output directory does not exist")
    proposal = load_json(Path(args.regions).resolve())
    regions = validate_region_proposals(proposal, output_dir)
    results: list[dict[str, Any]] = []
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
            require(asset_width >= args.minimum_pixels and asset_height >= args.minimum_pixels,
                    f"{region['occurrenceId']} is smaller than {args.minimum_pixels} pixels")
            asset_crop = image.crop(asset_pixel_box)
            asset_path = output_dir / Path(region["assetImage"])
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_crop.save(asset_path, format="PNG", optimize=True)
            result = dict(region)
            result["assetPixelBox"] = list(asset_pixel_box)
            result["assetQuality"] = crop_quality(asset_path, asset_crop)
            result["contextPixelBox"] = None
            result["contextQuality"] = None
            if region["contextRegion"] is not None:
                context_pixel_box = normalized_pixel_box(region["contextRegion"], image.width, image.height)
                context_crop = image.crop(context_pixel_box)
                context_path = output_dir / Path(region["contextImage"])
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
    print(f"Created {len(results)} asset crop(s) and "
          f"{sum(item['contextImage'] is not None for item in results)} context crop(s)")


def hamming_distance(first: str, second: str) -> int:
    return (int(first, 16) ^ int(second, 16)).bit_count()


def command_duplicates(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir).resolve()
    crop_results = load_json(Path(args.crop_results).resolve())
    require(isinstance(crop_results, dict) and crop_results.get("schemaVersion") == CROP_RESULT_VERSION,
            f"Crop result schemaVersion must be {CROP_RESULT_VERSION}")
    crops = crop_results.get("crops")
    require(isinstance(crops, list), "Crop results must contain a crops array")
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

    for index, crop in enumerate(crops):
        require(isinstance(crop, dict), f"crops[{index}] must be an object")
        require_id(crop.get("assetId"), f"crops[{index}].assetId")
        require_id(crop.get("occurrenceId"), f"crops[{index}].occurrenceId")
        quality = crop.get("assetQuality")
        validate_quality(quality, f"crops[{index}].assetQuality")
    for first_index in range(len(crops)):
        first_quality = crops[first_index]["assetQuality"]
        for second_index in range(first_index + 1, len(crops)):
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
            "assetIds": sorted({crops[index]["assetId"] for index in members}),
            "occurrenceIds": sorted({crops[index]["occurrenceId"] for index in members}),
            "confidence": 1.0 if exact else round(max(0.5, 1 - maximum_distance / 64), 3),
            "maximumPerceptualDistance": maximum_distance,
            "requiresSemanticReview": not exact
        })
    result = {
        "schemaVersion": DUPLICATE_RESULT_VERSION,
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
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    counts = validate_manifest_data(load_json(manifest_path), output_dir)
    if output_dir is not None:
        require(manifest_path.is_relative_to(output_dir), "Manifest must be inside the output directory")
        write_validation_report(output_dir, manifest_path, counts)
    print("Manifest is valid: " + ", ".join(f"{key}={value}" for key, value in counts.items()))


def command_package(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    require(output_dir.is_dir(), "Output directory does not exist")
    require(manifest_path.parent == output_dir, "manifest.json must be at the output directory root")
    require((output_dir / "summary.md").is_file(), "summary.md is required")
    manifest = load_json(manifest_path)
    manifest["generatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_json(manifest_path, manifest)
    counts = validate_manifest_data(manifest, output_dir)
    write_validation_report(output_dir, manifest_path, counts)
    archive = Path(args.archive).resolve()
    require(not archive.is_relative_to(output_dir), "Archive must be outside the output directory")
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    included = 0
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source in sorted(output_dir.rglob("*")):
            if source.is_file() and not source.is_symlink() and "__pycache__" not in source.parts:
                bundle.write(source, source.relative_to(output_dir).as_posix())
                included += 1
    print(f"Packaged {included} file(s) in {archive}")


def command_self_test(_: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        root = temporary_path / "output"
        page_path = root / "pages" / "test-document" / "page-0001.png"
        first_asset_path = root / "assets" / "test-document" / "asset-0001.png"
        second_asset_path = root / "assets" / "test-document" / "asset-0002.png"
        for path, content in ((page_path, b"test-page"), (first_asset_path, b"same-asset"),
                              (second_asset_path, b"same-asset")):
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
        crop_results_path = root / "diagnostics" / "crop-results.json"
        write_json(crop_results_path, {
            "schemaVersion": CROP_RESULT_VERSION,
            "crops": [
                {"assetId": "test-asset-0001", "occurrenceId": "test-occurrence-0001",
                 "assetQuality": quality},
                {"assetId": "test-asset-0002", "occurrenceId": "test-occurrence-0002",
                 "assetQuality": quality}
            ]
        })
        command_duplicates(argparse.Namespace(
            output_dir=str(root), crop_results=str(crop_results_path), threshold=6
        ))
        suggestions = load_json(root / "diagnostics" / "duplicate-suggestions.json")["suggestions"]
        require(len(suggestions) == 1 and suggestions[0]["matchType"] == "exact",
                "Self-test exact duplicate was not detected")
        try:
            safe_relative_path("../escape.png", "self-test")
            raise ValidationError("Self-test did not reject path traversal")
        except ValidationError:
            pass
        archive = temporary_path / "self-test.zip"
        command_package(argparse.Namespace(
            output_dir=str(root), manifest=str(manifest_path), archive=str(archive)
        ))
        with zipfile.ZipFile(archive) as bundle:
            required = {
                "manifest.json", "summary.md", "pages/test-document/page-0001.png",
                "assets/test-document/asset-0001.png", "diagnostics/validation-report.json"
            }
            require(required.issubset(bundle.namelist()), "Self-test archive is incomplete")
    print("Self-test passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="Render every PDF page to PNG")
    render.add_argument("--input", required=True)
    render.add_argument("--output-dir", required=True)
    render.add_argument("--document-id", required=True)
    render.add_argument("--dpi", type=int, default=220, choices=range(120, 401), metavar="120-400")
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