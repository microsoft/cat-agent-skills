from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
from uuid import uuid4

from analyze_solution import analyze_solution, write_json
from extract_solution import extract_solution
from render_report import render_report


def run_assessment(
    zip_path: Path,
    work_dir: Path,
    output_dir: Path | None = None,
) -> dict[str, object]:
    zip_path = zip_path.resolve()
    work_dir = work_dir.resolve()
    run_dir = work_dir / f"run-{uuid4().hex[:12]}"
    resolved_output_dir = (
        output_dir.resolve() if output_dir is not None else run_dir / "output"
    )
    resolved_output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        resolved_output_dir.mkdir()
    except FileExistsError as error:
        raise FileExistsError(
            f"Output directory already exists; use a new path: "
            f"{resolved_output_dir}"
        ) from error

    extract_dir = run_dir / "solution_extract"
    metrics_path = resolved_output_dir / "assessment_metrics.json"
    report_path = resolved_output_dir / "assessment_report.md"
    metrics_staging_path = resolved_output_dir / ".assessment_metrics.json.tmp"
    report_staging_path = resolved_output_dir / ".assessment_report.md.tmp"

    try:
        extraction = extract_solution(zip_path, extract_dir)
        metrics = analyze_solution(extract_dir)
        write_json(metrics_staging_path, metrics)

        report = render_report(metrics)
        with report_staging_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(report)
        metrics_staging_path.replace(metrics_path)
        report_staging_path.replace(report_path)
    except Exception:
        if resolved_output_dir.exists():
            shutil.rmtree(resolved_output_dir)
        raise

    return {
        "extraction": extraction,
        "runDirectory": str(run_dir),
        "metricsPath": str(metrics_path),
        "reportPath": str(report_path),
        "workflowCount": metrics["totals"]["workflowCount"],
        "totalActions": metrics["totals"]["totalActions"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the portable Power Automate solution assessment workflow."
    )
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("/tmp/pad-assessment"),
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    result = run_assessment(args.zip, args.work_dir, args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
