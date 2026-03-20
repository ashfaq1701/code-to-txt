#!/usr/bin/env python3
"""CLI for exporting a source tree into an LLM-friendly text format."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".cache",
    ".idea",
    ".vscode",
}
IGNORED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".log",
    ".lock",
    ".sqlite3",
    ".bin",
    ".exe",
}
MAX_FILE_SIZE_BYTES = 1024 * 1024
READ_ERROR_PLACEHOLDER = "[ERROR: Could not read file]"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code-export",
        description="Export a directory of source files into a single text file.",
    )
    parser.add_argument("base_path", help="Path to the directory to scan")
    parser.add_argument(
        "output_path",
        help="Path to the output file or to a directory where the output file should be created",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    base_path = Path(args.base_path).expanduser().resolve()
    if not base_path.exists():
        parser.error(f"base_path does not exist: {base_path}")
    if not base_path.is_dir():
        parser.error(f"base_path is not a directory: {base_path}")

    args.base_path = base_path
    args.output_path = Path(args.output_path).expanduser()
    return args


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(8192)
    except OSError:
        return False
    return b"\x00" in chunk


def should_skip_file(path: Path) -> bool:
    if path.suffix.lower() in IGNORED_EXTENSIONS:
        return True
    try:
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return True
    except OSError:
        return False
    return is_binary_file(path)


def iter_candidate_files(base_path: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(base_path):
        dirs[:] = sorted(directory for directory in dirs if directory not in IGNORED_DIRECTORIES)
        for filename in sorted(files):
            yield Path(root, filename)


def collect_relative_paths(base_path: Path, excluded_path: Path | None = None) -> list[Path]:
    excluded_relative: Path | None = None
    if excluded_path is not None:
        try:
            excluded_relative = excluded_path.resolve().relative_to(base_path)
        except ValueError:
            excluded_relative = None

    selected_files: list[Path] = []
    for file_path in iter_candidate_files(base_path):
        relative_path = file_path.relative_to(base_path)
        if excluded_relative is not None and relative_path == excluded_relative:
            continue
        if should_skip_file(file_path):
            continue
        selected_files.append(relative_path)
    return sorted(selected_files, key=lambda path: path.as_posix())


def read_file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return READ_ERROR_PLACEHOLDER


def render_output(base_path: Path, relative_paths: list[Path]) -> str:
    lines: list[str] = [f"<BASE_PATH>{base_path}", "", "<FILES>"]
    lines.extend(path.as_posix() for path in relative_paths)
    lines.append("</FILES>")

    parts = ["\n".join(lines)]
    for relative_path in relative_paths:
        file_path = base_path / relative_path
        content = read_file_text(file_path)
        parts.append(f"<FILE: {relative_path.as_posix()}>\n{content}\n</FILE>")
    return "\n\n".join(parts) + "\n"


def resolve_output_file(base_path: Path, output_path: Path) -> Path:
    if output_path.exists() and output_path.is_dir():
        return output_path / f"{base_path.name}_output.txt"

    if output_path.exists() and output_path.is_file():
        return output_path

    if output_path.suffix:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    output_path.mkdir(parents=True, exist_ok=True)
    return output_path / f"{base_path.name}_output.txt"


def export_codebase(base_path: Path, output_path: Path) -> tuple[Path, int]:
    destination = resolve_output_file(base_path, output_path)
    relative_paths = collect_relative_paths(base_path, excluded_path=destination)
    export_text = render_output(base_path, relative_paths)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(export_text, encoding="utf-8")
    return destination, len(relative_paths)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    destination, exported_count = export_codebase(args.base_path, args.output_path)
    print(f"Exported {exported_count} files to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
