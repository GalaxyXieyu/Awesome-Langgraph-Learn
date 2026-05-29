#!/usr/bin/env python3
"""Validate student-facing technical tutorial artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FORBIDDEN_PATTERNS = [
    "学员",
    "课堂",
    "讲师",
    "老师",
    "同学",
    "读者",
    "适合教学",
    "更适合教学",
    "这里要",
    "先让",
    "你可以直接告诉",
    "为什么这样设计",
]

FINAL_DEMO_PATTERNS = [
    "最终演示",
    "Final Demo",
    "final demo",
    "验收",
]


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    allowed = {".ipynb", ".md", ".py", ".json", ".yaml", ".yml"}
    return [
        p
        for p in path.rglob("*")
        if p.is_file()
        and p.suffix in allowed
        and ".agents/skills/technical-tutorial-designer" not in p.as_posix()
    ]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_json(path: Path, errors: list[str]) -> None:
    try:
        json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001 - CLI validator should report all parse failures.
        errors.append(f"{path}: invalid JSON: {exc}")


def validate_ipynb(path: Path, errors: list[str], warnings: list[str]) -> None:
    try:
        notebook = json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{path}: invalid notebook JSON: {exc}")
        return

    cells = notebook.get("cells", [])
    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
    markdown_text = "\n".join(
        "".join(cell.get("source", [])) for cell in cells if cell.get("cell_type") == "markdown"
    )
    all_text = "\n".join("".join(cell.get("source", [])) for cell in cells)

    if not code_cells:
        warnings.append(f"{path}: no code cells found")
    if not any(pattern in all_text for pattern in FINAL_DEMO_PATTERNS):
        warnings.append(f"{path}: no explicit final demo marker found")

    expected_sections = ["核心概念", "案例背景"]
    for section in expected_sections:
        if section not in markdown_text:
            warnings.append(f"{path}: missing section marker: {section}")


def scan_forbidden(path: Path, text: str, errors: list[str]) -> None:
    for pattern in FORBIDDEN_PATTERNS:
        for match in re.finditer(re.escape(pattern), text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{path}:{line}: forbidden wording: {pattern}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate technical tutorial files.")
    parser.add_argument("path", type=Path, help="Tutorial file or directory")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"not found: {args.path}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    files = iter_files(args.path)

    for path in files:
        if path.suffix == ".json":
            validate_json(path, errors)
        elif path.suffix == ".ipynb":
            validate_ipynb(path, errors, warnings)

        if path.suffix in {".ipynb", ".md", ".py"}:
            scan_forbidden(path, read_text(path), errors)

    print(f"checked files: {len(files)}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
