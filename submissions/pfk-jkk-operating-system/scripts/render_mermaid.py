#!/usr/bin/env python3
"""Render a Mermaid source file to SVG or PNG using Mermaid CLI.

Requires Python 3, Node.js, npx, and network access when Mermaid CLI is not
already cached. This helper is optional; the .mmd source remains canonical.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Mermaid .mmd file to SVG or PNG using Mermaid CLI."
    )
    parser.add_argument("input_file", type=Path, help="Path to the Mermaid source file.")
    parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        help="Output image path. Defaults to the input path with the chosen extension.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("svg", "png"),
        default="svg",
        help="Image format to produce. Default: svg.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    input_file = arguments.input_file.resolve()

    if not input_file.is_file():
        raise FileNotFoundError(f"Mermaid source file does not exist: {input_file}")

    npx = shutil.which("npx")
    if npx is None:
        raise RuntimeError("npx was not found. Install Node.js, or render the Mermaid source in the host.")

    output_file = arguments.output_file or input_file.with_suffix(f".{arguments.format}")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    command = [
        npx,
        "--yes",
        "@mermaid-js/mermaid-cli",
        "-i",
        str(input_file),
        "-o",
        str(output_file),
        "-e",
        arguments.format,
    ]
    subprocess.run(command, check=True)
    print(f"Rendered Mermaid diagram: {output_file}")


if __name__ == "__main__":
    main()