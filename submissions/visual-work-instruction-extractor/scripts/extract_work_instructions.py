#!/usr/bin/env python3
"""Deterministic file operations for the Visual Work Instruction Extractor skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "visual-work-instruction-manifest/1.0"
REGION_VERSION = "visual-work-instruction-regions/1.0"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VALID_STATUSES = {"verified", "best-effort", "review-required"}
VALID_KINDS = {"instruction-evidence", "instruction-photo", "safety-warning", "overview"}
ARTIFACT_ROOTS = {"pages", "crops", "diagnostics"}
ROOT_KEYS = {"schemaVersion", "generatedAt", "document", "pages", "instructions", "review", "limitations"}
DOCUMENT_KEYS = {"id", "sourceFile", "sha256", "title", "purpose", "languages"}
PAGE_KEYS = {"pageNumber", "image", "title", "warnings", "status", "reviewReasons"}
INSTRUCTION_KEYS = {
    "id", "sequence", "sourcePage", "sourceRegion", "title", "action", "component", "location",
    "partNumbers", "toolsAndMaterials", "warnings", "evidenceImage", "photoImage", "fullPageFallback",
    "confidence", "status", "reviewReasons", "extractionMethod",
}
WARNING_KEYS = {"text", "severity", "sourcePage", "sourceRegion"}
REVIEW_KEYS = {"required", "instructionIds", "notes"}
METHODS = {"native-vision", "ocr-and-vision", "text-layer-and-vision", "manual"}


class ValidationError(Exception):
    """Raised when an artifact violates the extraction contract."""


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_keys(value: dict[str, Any], required: set[str], allowed: set[str], field: str) -> None:
    missing = sorted(required - value.keys())
    extra = sorted(value.keys() - allowed)
    require(not missing, f"{field} is missing required key(s): {', '.join(missing)}")
    require(not extra, f"{field} contains unknown key(s): {', '.join(extra)}")


def safe_relative_path(value: Any, field: str, roots: set[str] | None = None) -> PurePosixPath:
    require(isinstance(value, str) and value, f"{field} must be a non-empty relative path")
    require("\\" not in value, f"{field} must use forward slashes: {value}")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts and not re.match(r"^[A-Za-z]:", value),
            f"{field} must stay inside the output directory: {value}")
    if roots is not None:
        require(path.parts and path.parts[0] in roots,
                f"{field} must be under one of: {', '.join(sorted(roots))}")
    return path


def is_safe_artifact_file(output_dir: Path, relative_path: str | PurePosixPath) -> bool:
    candidate = output_dir
    for part in PurePosixPath(relative_path).parts:
        candidate /= part
        if candidate.is_symlink():
            return False
    return candidate.is_file()


def ensure_safe_directory(path: Path, field: str) -> None:
    require(not path.is_symlink(), f"{field} directory must not be a symlink")
    require(not path.exists() or path.is_dir(), f"{field} must be a directory")
    path.mkdir(parents=True, exist_ok=True)


def validate_box(value: Any, field: str) -> None:
    if value is None:
        return
    require(isinstance(value, list) and len(value) == 4, f"{field} must contain four coordinates or null")
    require(all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value),
            f"{field} coordinates must be numbers")
    left, top, right, bottom = value
    require(all(0 <= item <= 1 for item in value), f"{field} coordinates must be between 0 and 1")
    require(left < right and top < bottom, f"{field} must have positive width and height")


def validate_region_page_entry(page_entry: Any) -> PurePosixPath:
    require(isinstance(page_entry, dict), "Each region page must be an object")

    page_number = page_entry.get("page")
    require(
        isinstance(page_number, int)
        and not isinstance(page_number, bool)
        and page_number >= 1,
        "region page must be a positive integer",
    )

    image_path = safe_relative_path(page_entry.get("image"), "region page image")
    require(
        image_path.as_posix() == f"pages/page-{page_number:04d}.png",
        "region page image must match its page number",
    )
    return image_path


def validate_warning(value: Any, field: str, page_numbers: set[int]) -> None:
    require(isinstance(value, dict), f"{field} must be an object")
    require_keys(value, {"text", "severity", "sourcePage"}, WARNING_KEYS, field)
    require(isinstance(value["text"], str) and value["text"].strip(), f"{field}.text is required")
    require(value["severity"] in {"information", "caution", "warning", "danger", "unknown"},
            f"{field}.severity is invalid")
    require(isinstance(value["sourcePage"], int) and not isinstance(value["sourcePage"], bool),
            f"{field}.sourcePage must be an integer")
    require(value["sourcePage"] in page_numbers, f"{field}.sourcePage does not identify a page")
    validate_box(value.get("sourceRegion"), f"{field}.sourceRegion")


def validate_string_array(value: Any, field: str, min_length: int = 0, unique: bool = False) -> None:
    require(isinstance(value, list), f"{field} must be an array")
    require(all(isinstance(item, str) and len(item) >= min_length for item in value),
            f"{field} contains an invalid string")
    if unique:
        require(len(value) == len(set(value)), f"{field} must contain unique values")


def validate_manifest_data(manifest: Any, output_dir: Path | None = None) -> list[str]:
    require(isinstance(manifest, dict), "Manifest root must be an object")
    require_keys(manifest, {"schemaVersion", "document", "pages", "instructions", "review"}, ROOT_KEYS, "manifest")
    require(manifest["schemaVersion"] == SCHEMA_VERSION, f"schemaVersion must be {SCHEMA_VERSION}")
    generated_at = manifest.get("generatedAt")
    if generated_at is not None:
        require(isinstance(generated_at, str), "generatedAt must be a string or null")
        try:
            datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("generatedAt must be an ISO 8601 date-time") from exc
    validate_string_array(manifest.get("limitations", []), "limitations")

    document = manifest["document"]
    require(isinstance(document, dict), "document must be an object")
    require_keys(document, DOCUMENT_KEYS, DOCUMENT_KEYS, "document")
    require(isinstance(document["id"], str) and ID_PATTERN.fullmatch(document["id"]), "document.id is invalid")
    require(isinstance(document["sourceFile"], str) and document["sourceFile"], "document.sourceFile is required")
    sha256 = document["sha256"]
    require(sha256 is None or (isinstance(sha256, str) and re.fullmatch(r"[a-f0-9]{64}", sha256)),
            "document.sha256 must be null or a lowercase SHA-256")
    require(document["title"] is None or isinstance(document["title"], str), "document.title must be a string or null")
    require(document["purpose"] is None or isinstance(document["purpose"], str), "document.purpose must be a string or null")
    validate_string_array(document["languages"], "document.languages", min_length=2, unique=True)

    pages = manifest["pages"]
    require(isinstance(pages, list) and pages, "pages must contain at least one page")
    page_numbers: set[int] = set()
    page_review_required = False
    referenced_paths: list[str] = []
    for index, page in enumerate(pages):
        field = f"pages[{index}]"
        require(isinstance(page, dict), f"{field} must be an object")
        require_keys(page, {"pageNumber", "image", "title", "warnings", "status"}, PAGE_KEYS, field)
        number = page["pageNumber"]
        require(isinstance(number, int) and not isinstance(number, bool) and number >= 1, f"{field}.pageNumber is invalid")
        require(number not in page_numbers, f"Duplicate page number: {number}")
        page_numbers.add(number)
        image = safe_relative_path(page["image"], f"{field}.image", {"pages"})
        require(image.as_posix() == f"pages/page-{number:04d}.png", f"{field}.image must match its page number")
        referenced_paths.append(image.as_posix())
        require(page["title"] is None or isinstance(page["title"], str), f"{field}.title must be a string or null")
        require(page["status"] in VALID_STATUSES, f"{field}.status is invalid")
        if page["status"] == "review-required":
            page_review_required = True
        validate_string_array(page.get("reviewReasons", []), f"{field}.reviewReasons")
        require(isinstance(page["warnings"], list), f"{field}.warnings must be an array")
    for index, page in enumerate(pages):
        for warning_index, warning in enumerate(page["warnings"]):
            validate_warning(warning, f"pages[{index}].warnings[{warning_index}]", page_numbers)

    instructions = manifest["instructions"]
    require(isinstance(instructions, list), "instructions must be an array")
    instruction_ids: set[str] = set()
    review_required_ids: set[str] = set()
    for index, instruction in enumerate(instructions):
        field = f"instructions[{index}]"
        require(isinstance(instruction, dict), f"{field} must be an object")
        require_keys(instruction, INSTRUCTION_KEYS, INSTRUCTION_KEYS, field)
        instruction_id = instruction["id"]
        require(isinstance(instruction_id, str) and ID_PATTERN.fullmatch(instruction_id), f"{field}.id is invalid")
        require(instruction_id not in instruction_ids, f"Duplicate instruction id: {instruction_id}")
        instruction_ids.add(instruction_id)
        sequence = instruction["sequence"]
        require(sequence is None or (isinstance(sequence, int) and not isinstance(sequence, bool) and sequence >= 1),
                f"{field}.sequence must be a positive integer or null")
        source_page = instruction["sourcePage"]
        require(isinstance(source_page, int) and not isinstance(source_page, bool) and source_page in page_numbers,
                f"{field}.sourcePage does not identify a page")
        validate_box(instruction["sourceRegion"], f"{field}.sourceRegion")
        for nullable_field in ("title", "action", "component", "location"):
            require(instruction[nullable_field] is None or isinstance(instruction[nullable_field], str),
                    f"{field}.{nullable_field} must be a string or null")
        validate_string_array(instruction["partNumbers"], f"{field}.partNumbers", unique=True)
        validate_string_array(instruction["toolsAndMaterials"], f"{field}.toolsAndMaterials", unique=True)
        require(isinstance(instruction["warnings"], list), f"{field}.warnings must be an array")
        for warning_index, warning in enumerate(instruction["warnings"]):
            validate_warning(warning, f"{field}.warnings[{warning_index}]", page_numbers)
        for path_field in ("evidenceImage", "photoImage"):
            value = instruction[path_field]
            if value is not None:
                referenced_paths.append(str(safe_relative_path(value, f"{field}.{path_field}", ARTIFACT_ROOTS)))
        fallback = safe_relative_path(instruction["fullPageFallback"], f"{field}.fullPageFallback", {"pages"})
        referenced_paths.append(str(fallback))
        require(fallback.as_posix() == f"pages/page-{source_page:04d}.png",
                f"{field}.fullPageFallback must reference its source page image")
        confidence = instruction["confidence"]
        require(isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and 0 <= confidence <= 1,
                f"{field}.confidence must be between 0 and 1")
        require(instruction["status"] in VALID_STATUSES, f"{field}.status is invalid")
        if instruction["status"] == "review-required":
            review_required_ids.add(instruction_id)
        validate_string_array(instruction["reviewReasons"], f"{field}.reviewReasons")
        if instruction["status"] != "verified":
            require(bool(instruction["reviewReasons"]), f"{field} needs at least one review reason")
        require(instruction["extractionMethod"] in METHODS, f"{field}.extractionMethod is invalid")

    review = manifest["review"]
    require(isinstance(review, dict), "review must be an object")
    require_keys(review, REVIEW_KEYS, REVIEW_KEYS, "review")
    require(isinstance(review["required"], bool), "review.required must be boolean")
    validate_string_array(review["instructionIds"], "review.instructionIds", unique=True)
    require(set(review["instructionIds"]).issubset(instruction_ids), "review.instructionIds contains an unknown instruction")
    require(review_required_ids.issubset(set(review["instructionIds"])),
            "All review-required instructions must appear in review.instructionIds")
    validate_string_array(review["notes"], "review.notes")
    require(review["required"] == bool(page_review_required or review_required_ids or review["notes"]),
            "review.required must reflect review-required pages, instructions, or review notes")

    if output_dir is not None:
        render_results = output_dir / "diagnostics" / "render-results.json"
        if render_results.is_file():
            rendered = load_json(render_results)
            require(isinstance(rendered, dict) and isinstance(rendered.get("pageCount"), int) and rendered["pageCount"] >= 1,
                    "diagnostics/render-results.json.pageCount must be a positive integer")
            require(page_numbers == set(range(1, rendered["pageCount"] + 1)),
                    "Manifest pages must cover every rendered page")
        unsafe = [value for value in sorted(set(referenced_paths))
                  if not is_safe_artifact_file(output_dir, value)]
        require(not unsafe, "Referenced files are missing or unsafe: " + ", ".join(unsafe))
    return sorted(set(referenced_paths))


def command_render(args: argparse.Namespace) -> None:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ValidationError("PDF rendering needs pypdfium2 and Pillow; use native harness rendering or install them") from exc
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise ValidationError("PDF rendering needs Pillow; use native harness rendering or install it") from exc
    input_path = Path(args.input).resolve()
    require(input_path.is_file() and input_path.suffix.lower() == ".pdf", "Input must be an existing PDF")
    output_dir = Path(args.output_dir).resolve()
    pages_dir = output_dir / "pages"
    diagnostics_dir = output_dir / "diagnostics"
    ensure_safe_directory(pages_dir, "pages")
    ensure_safe_directory(diagnostics_dir, "diagnostics")
    for old_page in pages_dir.glob("page-*.png"):
        old_page.unlink()
    try:
        document = pdfium.PdfDocument(str(input_path))
    except Exception as exc:
        raise ValidationError(f"Cannot open PDF; it may be corrupt or encrypted: {exc}") from exc
    require(len(document) > 0, "PDF contains no pages")
    scale = args.dpi / 72
    for page_index in range(len(document)):
        page = document[page_index]
        bitmap = page.render(scale=scale)
        bitmap.to_pil().save(pages_dir / f"page-{page_index + 1:04d}.png", format="PNG", optimize=True)
        page.close()
    document.close()
    write_json(diagnostics_dir / "render-results.json", {
        "sourceFile": input_path.name,
        "sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "pageCount": page_index + 1,
        "dpi": args.dpi,
    })
    print(f"Rendered {page_index + 1} page(s) to {pages_dir}")


def command_crop(args: argparse.Namespace) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValidationError("Cropping needs Pillow; use native harness image cropping or install it") from exc
    output_dir = Path(args.output_dir).resolve()
    proposal = load_json(Path(args.regions).resolve())
    require(isinstance(proposal, dict) and proposal.get("schemaVersion") == REGION_VERSION,
            f"Region schemaVersion must be {REGION_VERSION}")
    require(isinstance(proposal.get("pages"), list), "Region pages must be an array")
    diagnostics_dir = output_dir / "diagnostics"
    ensure_safe_directory(diagnostics_dir, "diagnostics")
    crops_dir = output_dir / "crops"
    if crops_dir.exists():
        require(not crops_dir.is_symlink(), "crops directory must not be a symlink")
        for stale in sorted(crops_dir.rglob("*"), reverse=True):
            if stale.is_symlink() or stale.is_file():
                stale.unlink()
            elif stale.is_dir():
                stale.rmdir()
    crops_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    seen_outputs: set[str] = set()
    for page_entry in proposal["pages"]:
        image_path = validate_region_page_entry(page_entry)
        source_path = output_dir / Path(str(image_path))
        require(is_safe_artifact_file(output_dir, image_path), f"Page image is missing or unsafe: {image_path}")
        require(isinstance(page_entry.get("regions"), list), "regions must be an array")
        with Image.open(source_path) as image:
            width, height = image.size
            for region in page_entry["regions"]:
                require(isinstance(region, dict), "Each region must be an object")
                region_id = region.get("id")
                require(isinstance(region_id, str) and ID_PATTERN.fullmatch(region_id), "Region id is invalid")
                require(region.get("kind") in VALID_KINDS, f"Region {region_id} has an invalid kind")
                box = region.get("box")
                require(box is not None, f"region {region_id}.box is required")
                validate_box(box, f"region {region_id}.box")
                output = str(safe_relative_path(region.get("output"), f"region {region_id}.output", {"crops"}))
                require(output.lower().endswith(".png"), f"Region {region_id} output must be a PNG")
                require(output not in seen_outputs, f"Duplicate crop output: {output}")
                seen_outputs.add(output)
                left, top, right, bottom = box
                pixel_box = (
                    max(0, min(width - 1, round(left * width))),
                    max(0, min(height - 1, round(top * height))),
                    max(1, min(width, round(right * width))),
                    max(1, min(height, round(bottom * height))),
                )
                crop_width = pixel_box[2] - pixel_box[0]
                crop_height = pixel_box[3] - pixel_box[1]
                require(crop_width >= 64 and crop_height >= 64, f"Region {region_id} is smaller than 64 x 64 pixels")
                destination = output_dir / Path(output)
                destination.parent.mkdir(parents=True, exist_ok=True)
                image.crop(pixel_box).save(destination, format="PNG", optimize=True)
                results.append({"id": region_id, "output": output, "pixelBox": list(pixel_box),
                                "width": crop_width, "height": crop_height})
    write_json(diagnostics_dir / "crop-results.json", {"crops": results})
    print(f"Created {len(results)} crop(s)")


def command_validate(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    references = validate_manifest_data(load_json(manifest_path), output_dir)
    print(f"Manifest is valid; {len(references)} referenced artifact(s)")


def command_package(args: argparse.Namespace) -> None:
    lexical_output_dir = Path(os.path.abspath(args.output_dir))
    output_dir = lexical_output_dir.resolve()
    manifest_path = Path(args.manifest).resolve()
    require(output_dir.is_dir(), "Output directory does not exist")
    require(manifest_path == output_dir / "manifest.json", "manifest must be exactly <output-dir>/manifest.json")
    archive = Path(os.path.abspath(args.archive))
    resolved_archive = archive.resolve()
    require(not archive.is_relative_to(lexical_output_dir) and not resolved_archive.is_relative_to(output_dir),
            "archive must be outside the output directory")
    require(not archive.is_symlink(), "archive must not be a symlink")
    for required_file in (
        "manifest.json",
        "summary.md",
        "diagnostics/crop-results.json",
        "diagnostics/region-proposals.json",
    ):
        require(is_safe_artifact_file(output_dir, required_file), f"{required_file} is required and must not be a symlink")
    manifest = load_json(manifest_path)
    manifest["generatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_json(manifest_path, manifest)
    references = validate_manifest_data(manifest, output_dir)
    packaged_artifacts = sorted(set(references) | {
        "diagnostics/crop-results.json",
        "diagnostics/region-proposals.json",
    })
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    included = 0
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for relative in packaged_artifacts:
            require(is_safe_artifact_file(output_dir, relative), f"{relative} is missing or unsafe")
            bundle.write(output_dir / Path(relative), relative)
            included += 1
        for root_file in ("manifest.json", "summary.md"):
            source = output_dir / root_file
            require(source.is_file() and not source.is_symlink(), f"{root_file} is required")
            bundle.write(source, root_file)
            included += 1
    print(f"Packaged {included} file(s) in {archive}")


def expect_failure(callback: Any, label: str) -> None:
    try:
        callback()
    except ValidationError:
        return
    raise ValidationError(f"Self-test expected failure: {label}")


def command_self_test(_: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "pages").mkdir()
        (root / "crops").mkdir()
        (root / "diagnostics").mkdir()
        (root / "pages/page-0001.png").write_bytes(b"test-page")
        (root / "summary.md").write_text("# Test\n", encoding="utf-8")
        write_json(root / "diagnostics/crop-results.json", {"crops": []})
        write_json(root / "diagnostics/region-proposals.json", {"schemaVersion": REGION_VERSION, "pages": []})
        manifest = {
            "schemaVersion": SCHEMA_VERSION, "generatedAt": None,
            "document": {"id": "test-document", "sourceFile": "test.pdf", "sha256": None,
                         "title": "Test", "purpose": None, "languages": ["en"]},
            "pages": [{"pageNumber": 1, "image": "pages/page-0001.png", "title": "Test",
                       "warnings": [], "status": "verified", "reviewReasons": []}],
            "instructions": [], "review": {"required": False, "instructionIds": [], "notes": []},
            "limitations": [],
        }
        manifest_path = root / "manifest.json"
        write_json(manifest_path, manifest)
        validate_manifest_data(manifest, root)
        bad_box = dict(manifest)
        bad_box["pages"] = [{**manifest["pages"][0], "image": "pages/page-0001.png"}]
        bad_box["document"] = {**manifest["document"], "extra": True}
        expect_failure(lambda: validate_manifest_data(bad_box), "unknown properties")
        bad_page_review = {
            **manifest,
            "pages": [
                {
                    **manifest["pages"][0],
                    "status": "review-required",
                    "reviewReasons": ["Page requires review."],
                }
            ],
        }
        expect_failure(lambda: validate_manifest_data(bad_page_review), "page review requirement")
        valid_page_review = {
            **bad_page_review,
            "review": {"required": True, "instructionIds": [], "notes": []},
        }
        validate_manifest_data(valid_page_review)
        bad_source_page = {
            **manifest,
            "instructions": [
                {
                    "id": "test-instruction",
                    "sequence": 1,
                    "sourcePage": True,
                    "sourceRegion": None,
                    "title": "Test",
                    "action": "Test",
                    "component": None,
                    "location": None,
                    "partNumbers": [],
                    "toolsAndMaterials": [],
                    "warnings": [],
                    "evidenceImage": None,
                    "photoImage": None,
                    "fullPageFallback": "pages/page-0001.png",
                    "confidence": 1,
                    "status": "verified",
                    "reviewReasons": [],
                    "extractionMethod": "manual",
                }
            ],
        }
        expect_failure(lambda: validate_manifest_data(bad_source_page), "boolean instruction source page")
        bad_region = root / "bad-region.json"
        write_json(
            bad_region,
            {
                "schemaVersion": REGION_VERSION,
                "pages": [
                    {
                        "page": 2,
                        "image": "pages/page-0001.png",
                        "regions": [],
                    }
                ],
            },
        )

        def validate_bad_region() -> None:
            proposal = load_json(bad_region)
            require(isinstance(proposal, dict), "proposal must be an object")
            validate_region_page_entry(proposal["pages"][0])

        expect_failure(validate_bad_region, "region page/image mismatch")
        validate_region_page_entry({"page": 1, "image": "pages/page-0001.png", "regions": []})
        expect_failure(
            lambda: validate_region_page_entry(
                {"page": True, "image": "pages/page-0001.png", "regions": []}
            ),
            "boolean region page",
        )
        expect_failure(
            lambda: validate_region_page_entry(
                {"page": 0, "image": "pages/page-0000.png", "regions": []}
            ),
            "non-positive region page",
        )
        (root / "pages/stale-page.png").write_bytes(b"stale-page")
        write_json(root / "diagnostics/render-results.json", {
            "sourceFile": "test.pdf",
            "sha256": "0" * 64,
            "pageCount": 1,
            "dpi": 220,
        })
        expect_failure(
            lambda: command_package(
                argparse.Namespace(
                    output_dir=str(root),
                    manifest=str(manifest_path),
                    archive=str(root / "archive.zip"),
                )
            ),
            "archive inside output directory",
        )
        archive = root.parent / "self-test.zip"
        command_package(argparse.Namespace(output_dir=str(root), manifest=str(manifest_path), archive=str(archive)))
        with zipfile.ZipFile(archive) as bundle:
            require({"manifest.json", "summary.md", "pages/page-0001.png", "diagnostics/crop-results.json",
                     "diagnostics/region-proposals.json"}.issubset(bundle.namelist()), "Self-test archive is incomplete")
            require({"pages/stale-page.png", "diagnostics/render-results.json"}.isdisjoint(bundle.namelist()),
                    "Self-test archive contains unreferenced files")
        archive.unlink()
    print("Self-test passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("render", help="Render every PDF page to PNG")
    render.add_argument("--input", required=True); render.add_argument("--output-dir", required=True)
    render.add_argument("--dpi", type=int, default=220, choices=range(120, 401), metavar="120-400")
    render.set_defaults(handler=command_render)
    crop = commands.add_parser("crop", help="Create crops from normalized region proposals")
    crop.add_argument("--output-dir", required=True); crop.add_argument("--regions", required=True); crop.set_defaults(handler=command_crop)
    validate = commands.add_parser("validate", help="Validate a normalized manifest")
    validate.add_argument("--manifest", required=True); validate.add_argument("--output-dir"); validate.set_defaults(handler=command_validate)
    package = commands.add_parser("package", help="Validate and package extraction results")
    package.add_argument("--output-dir", required=True); package.add_argument("--manifest", required=True); package.add_argument("--archive", required=True); package.set_defaults(handler=command_package)
    self_test = commands.add_parser("self-test", help="Run dependency-free contract and packaging tests")
    self_test.set_defaults(handler=command_self_test)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args(); args.handler(args); return 0
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
