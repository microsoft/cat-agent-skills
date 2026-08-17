#!/usr/bin/env python3
"""Deterministic file operations for the Visual Work Instruction Extractor skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
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


def safe_relative_path(value: str, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{field} must be a non-empty relative path")
    if "\\" in value:
        raise ValidationError(f"{field} must use forward slashes: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", value):
        raise ValidationError(f"{field} must stay inside the output directory: {value}")
    return path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_box(value: Any, field: str) -> None:
    if value is None:
        return
    require(isinstance(value, list) and len(value) == 4, f"{field} must contain four coordinates")
    require(all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value),
            f"{field} coordinates must be numbers")
    left, top, right, bottom = value
    require(all(0 <= item <= 1 for item in value), f"{field} coordinates must be between 0 and 1")
    require(left < right and top < bottom, f"{field} must have positive width and height")


def validate_warning(value: Any, field: str, page_numbers: set[int]) -> None:
    require(isinstance(value, dict), f"{field} must be an object")
    require(isinstance(value.get("text"), str) and value["text"].strip(), f"{field}.text is required")
    require(value.get("severity") in {"information", "caution", "warning", "danger", "unknown"},
            f"{field}.severity is invalid")
    require(value.get("sourcePage") in page_numbers, f"{field}.sourcePage does not identify a page")
    validate_box(value.get("sourceRegion"), f"{field}.sourceRegion")


def validate_manifest_data(manifest: Any, output_dir: Path | None = None) -> list[str]:
    require(isinstance(manifest, dict), "Manifest root must be an object")
    require(manifest.get("schemaVersion") == SCHEMA_VERSION, f"schemaVersion must be {SCHEMA_VERSION}")
    document = manifest.get("document")
    require(isinstance(document, dict), "document must be an object")
    require(ID_PATTERN.fullmatch(str(document.get("id", ""))) is not None, "document.id is invalid")
    require(isinstance(document.get("sourceFile"), str) and document["sourceFile"], "document.sourceFile is required")
    sha256 = document.get("sha256")
    require(sha256 is None or re.fullmatch(r"[a-f0-9]{64}", str(sha256)) is not None,
            "document.sha256 must be null or a lowercase SHA-256")
    require(isinstance(document.get("languages"), list), "document.languages must be an array")

    pages = manifest.get("pages")
    require(isinstance(pages, list) and pages, "pages must contain at least one page")
    page_numbers: set[int] = set()
    referenced_paths: list[str] = []
    for index, page in enumerate(pages):
        field = f"pages[{index}]"
        require(isinstance(page, dict), f"{field} must be an object")
        number = page.get("pageNumber")
        require(isinstance(number, int) and not isinstance(number, bool) and number >= 1,
                f"{field}.pageNumber is invalid")
        require(number not in page_numbers, f"Duplicate page number: {number}")
        page_numbers.add(number)
        referenced_paths.append(str(safe_relative_path(page.get("image"), f"{field}.image")))
        require(page.get("status") in VALID_STATUSES, f"{field}.status is invalid")
        require(isinstance(page.get("warnings"), list), f"{field}.warnings must be an array")

    for index, page in enumerate(pages):
        for warning_index, warning in enumerate(page["warnings"]):
            validate_warning(warning, f"pages[{index}].warnings[{warning_index}]", page_numbers)

    instructions = manifest.get("instructions")
    require(isinstance(instructions, list), "instructions must be an array")
    instruction_ids: set[str] = set()
    review_required_ids: set[str] = set()
    for index, instruction in enumerate(instructions):
        field = f"instructions[{index}]"
        require(isinstance(instruction, dict), f"{field} must be an object")
        instruction_id = instruction.get("id")
        require(isinstance(instruction_id, str) and ID_PATTERN.fullmatch(instruction_id) is not None,
                f"{field}.id is invalid")
        require(instruction_id not in instruction_ids, f"Duplicate instruction id: {instruction_id}")
        instruction_ids.add(instruction_id)
        require(instruction.get("sourcePage") in page_numbers, f"{field}.sourcePage does not identify a page")
        validate_box(instruction.get("sourceRegion"), f"{field}.sourceRegion")
        confidence = instruction.get("confidence")
        require(isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and 0 <= confidence <= 1,
                f"{field}.confidence must be between 0 and 1")
        status = instruction.get("status")
        require(status in VALID_STATUSES, f"{field}.status is invalid")
        if status == "review-required":
            review_required_ids.add(instruction_id)
        require(isinstance(instruction.get("reviewReasons"), list), f"{field}.reviewReasons must be an array")
        if status != "verified":
            require(bool(instruction["reviewReasons"]), f"{field} needs at least one review reason")
        require(isinstance(instruction.get("warnings"), list), f"{field}.warnings must be an array")
        for warning_index, warning in enumerate(instruction["warnings"]):
            validate_warning(warning, f"{field}.warnings[{warning_index}]", page_numbers)
        for path_field in ("evidenceImage", "photoImage"):
            value = instruction.get(path_field)
            if value is not None:
                referenced_paths.append(str(safe_relative_path(value, f"{field}.{path_field}")))
        fallback = str(safe_relative_path(instruction.get("fullPageFallback"), f"{field}.fullPageFallback"))
        referenced_paths.append(fallback)
        expected_page = next(page["image"] for page in pages if page["pageNumber"] == instruction["sourcePage"])
        require(fallback == expected_page, f"{field}.fullPageFallback must reference its source page image")

    review = manifest.get("review")
    require(isinstance(review, dict), "review must be an object")
    review_ids = review.get("instructionIds")
    require(isinstance(review_ids, list), "review.instructionIds must be an array")
    require(set(review_ids).issubset(instruction_ids), "review.instructionIds contains an unknown instruction")
    require(review_required_ids.issubset(set(review_ids)), "All review-required instructions must appear in review.instructionIds")
    require(review.get("required") is bool(review_required_ids or review.get("notes")),
            "review.required must reflect review-required instructions or review notes")
    require(isinstance(review.get("notes"), list), "review.notes must be an array")

    if output_dir is not None:
        missing = [value for value in sorted(set(referenced_paths)) if not (output_dir / Path(value)).is_file()]
        require(not missing, "Referenced files are missing: " + ", ".join(missing))
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
    pages_dir.mkdir(parents=True, exist_ok=True)
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
        image = bitmap.to_pil()
        image.save(pages_dir / f"page-{page_index + 1:04d}.png", format="PNG", optimize=True)
        page.close()
    document.close()

    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    write_json(output_dir / "diagnostics" / "render-results.json", {
        "sourceFile": input_path.name,
        "sha256": digest,
        "pageCount": page_index + 1,
        "dpi": args.dpi
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
    results: list[dict[str, Any]] = []
    seen_outputs: set[str] = set()

    for page_entry in proposal["pages"]:
        require(isinstance(page_entry, dict), "Each region page must be an object")
        image_path = safe_relative_path(page_entry.get("image"), "region page image")
        source_path = output_dir / Path(str(image_path))
        require(source_path.is_file(), f"Page image is missing: {image_path}")
        require(isinstance(page_entry.get("regions"), list), "regions must be an array")
        with Image.open(source_path) as image:
            width, height = image.size
            for region in page_entry["regions"]:
                require(isinstance(region, dict), "Each region must be an object")
                region_id = region.get("id")
                require(isinstance(region_id, str) and ID_PATTERN.fullmatch(region_id) is not None,
                        "Region id is invalid")
                require(region.get("kind") in VALID_KINDS, f"Region {region_id} has an invalid kind")
                box = region.get("box")
                require(box is not None, f"region {region_id}.box is required")
                validate_box(box, f"region {region_id}.box")
                output = str(safe_relative_path(region.get("output"), f"region {region_id}.output"))
                require(output.startswith("crops/") and output.lower().endswith(".png"),
                        f"Region {region_id} output must be a PNG under crops/")
                require(output not in seen_outputs, f"Duplicate crop output: {output}")
                seen_outputs.add(output)
                left, top, right, bottom = box
                pixel_box = (
                    max(0, min(width - 1, round(left * width))),
                    max(0, min(height - 1, round(top * height))),
                    max(1, min(width, round(right * width))),
                    max(1, min(height, round(bottom * height)))
                )
                crop_width = pixel_box[2] - pixel_box[0]
                crop_height = pixel_box[3] - pixel_box[1]
                require(crop_width >= 64 and crop_height >= 64, f"Region {region_id} is smaller than 64 x 64 pixels")
                destination = output_dir / Path(output)
                destination.parent.mkdir(parents=True, exist_ok=True)
                image.crop(pixel_box).save(destination, format="PNG", optimize=True)
                results.append({"id": region_id, "output": output, "pixelBox": list(pixel_box),
                                "width": crop_width, "height": crop_height})

    write_json(output_dir / "diagnostics" / "crop-results.json", {"crops": results})
    print(f"Created {len(results)} crop(s)")


def command_validate(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    references = validate_manifest_data(load_json(manifest_path), output_dir)
    print(f"Manifest is valid; {len(references)} referenced artifact(s)")


def command_package(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    require(output_dir.is_dir(), "Output directory does not exist")
    require(manifest_path.parent == output_dir, "manifest.json must be at the output directory root")
    manifest = load_json(manifest_path)
    manifest["generatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_json(manifest_path, manifest)
    validate_manifest_data(manifest, output_dir)
    require((output_dir / "summary.md").is_file(), "summary.md is required")

    archive = Path(args.archive).resolve()
    require(not archive.is_relative_to(output_dir), "archive must be outside the output directory")
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    included = 0
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source in sorted(output_dir.rglob("*")):
            if (
                source.is_file()
                and not source.is_symlink()
                and "__pycache__" not in source.parts
            ):
                bundle.write(source, source.relative_to(output_dir).as_posix())
                included += 1
    print(f"Packaged {included} file(s) in {archive}")


def command_self_test(_: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "pages").mkdir()
        (root / "pages" / "page-0001.png").write_bytes(b"test-page")
        (root / "summary.md").write_text("# Test\n", encoding="utf-8")
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "generatedAt": None,
            "document": {"id": "test-document", "sourceFile": "test.pdf", "sha256": None,
                         "title": "Test", "purpose": None, "languages": ["en"]},
            "pages": [{"pageNumber": 1, "image": "pages/page-0001.png", "title": "Test",
                       "warnings": [], "status": "verified", "reviewReasons": []}],
            "instructions": [],
            "review": {"required": False, "instructionIds": [], "notes": []},
            "limitations": []
        }
        manifest_path = root / "manifest.json"
        write_json(manifest_path, manifest)
        validate_manifest_data(manifest, root)
        archive = root.parent / "self-test.zip"
        namespace = argparse.Namespace(output_dir=str(root), manifest=str(manifest_path), archive=str(archive))
        command_package(namespace)
        with zipfile.ZipFile(archive) as bundle:
            require({"manifest.json", "summary.md", "pages/page-0001.png"}.issubset(bundle.namelist()),
                    "Self-test archive is incomplete")
        archive.unlink()
    print("Self-test passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="Render every PDF page to PNG")
    render.add_argument("--input", required=True)
    render.add_argument("--output-dir", required=True)
    render.add_argument("--dpi", type=int, default=220, choices=range(120, 401), metavar="120-400")
    render.set_defaults(handler=command_render)

    crop = commands.add_parser("crop", help="Create crops from normalized region proposals")
    crop.add_argument("--output-dir", required=True)
    crop.add_argument("--regions", required=True)
    crop.set_defaults(handler=command_crop)

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