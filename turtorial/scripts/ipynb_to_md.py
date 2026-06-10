#!/usr/bin/env python3
"""Convert Jupyter notebooks into readable Markdown files."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any


IMAGE_MIME_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
}


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def output_text(value: Any) -> str:
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def fenced_block(content: str, language: str = "") -> str:
    content = content.rstrip()
    fence = "```"
    while fence in content:
        fence += "`"
    return f"{fence}{language}\n{content}\n{fence}"


def notebook_language(notebook: dict[str, Any]) -> str:
    language_info = notebook.get("metadata", {}).get("language_info", {})
    language = language_info.get("name")
    if isinstance(language, str) and language:
        return language
    return "python"


def write_image(asset_dir: Path, cell_index: int, output_index: int, mime: str, value: Any) -> Path:
    asset_dir.mkdir(parents=True, exist_ok=True)
    extension = IMAGE_MIME_EXTENSIONS[mime]
    image_path = asset_dir / f"cell-{cell_index:03d}-output-{output_index:02d}{extension}"

    if mime == "image/svg+xml":
        image_path.write_text(output_text(value), encoding="utf-8")
        return image_path

    image_data = output_text(value).replace("\n", "")
    image_path.write_bytes(base64.b64decode(image_data))
    return image_path


def markdown_for_output(
    output: dict[str, Any],
    cell_index: int,
    output_index: int,
    markdown_path: Path,
    asset_dir: Path,
) -> str:
    output_type = output.get("output_type")

    if output_type == "stream":
        text = output_text(output.get("text"))
        return fenced_block(text, "text") if text.strip() else ""

    if output_type == "error":
        traceback = output.get("traceback")
        if traceback:
            text = "\n".join(str(line) for line in traceback)
        else:
            text = f"{output.get('ename', '')}: {output.get('evalue', '')}".strip()
        return fenced_block(text, "text") if text.strip() else ""

    if output_type not in {"display_data", "execute_result"}:
        return ""

    data = output.get("data", {})
    if not isinstance(data, dict):
        return ""

    for mime in IMAGE_MIME_EXTENSIONS:
        if mime in data:
            image_path = write_image(asset_dir, cell_index, output_index, mime, data[mime])
            relative_path = image_path.relative_to(markdown_path.parent)
            return f"![输出图片]({relative_path.as_posix()})"

    if "text/markdown" in data:
        return output_text(data["text/markdown"]).rstrip()

    if "text/plain" in data:
        text = output_text(data["text/plain"])
        return fenced_block(text, "text") if text.strip() else ""

    if "text/html" in data:
        html = output_text(data["text/html"])
        return fenced_block(html, "html") if html.strip() else ""

    return ""


def convert_notebook(
    notebook_path: Path,
    markdown_path: Path,
    include_code: bool,
    include_outputs: bool,
) -> None:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    language = notebook_language(notebook)
    asset_dir = markdown_path.parent / f"{markdown_path.stem}-assets"
    sections: list[str] = []

    for cell_index, cell in enumerate(notebook.get("cells", []), start=1):
        cell_type = cell.get("cell_type")
        source = cell_source(cell).rstrip()

        if cell_type == "markdown":
            if source:
                sections.append(source)
            continue

        if cell_type != "code":
            continue

        code_parts: list[str] = []
        if include_code and source:
            code_parts.append(fenced_block(source, language))

        if include_outputs:
            rendered_outputs = []
            for output_index, output in enumerate(cell.get("outputs", []), start=1):
                rendered_output = markdown_for_output(
                    output,
                    cell_index,
                    output_index,
                    markdown_path,
                    asset_dir,
                )
                if rendered_output:
                    rendered_outputs.append(rendered_output)

            if rendered_outputs:
                code_parts.append("**输出**\n\n" + "\n\n".join(rendered_outputs))

        if code_parts:
            sections.append("\n\n".join(code_parts))

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n\n".join(sections).rstrip() + "\n", encoding="utf-8")


def discover_notebooks(paths: list[Path]) -> list[Path]:
    notebooks: list[Path] = []
    for path in paths:
        if path.is_dir():
            tutorial_path = path / "tutorial.ipynb"
            if tutorial_path.exists():
                notebooks.append(tutorial_path)
                continue

            directory_notebooks = sorted(path.glob("*.ipynb"))
            if directory_notebooks:
                notebooks.extend(directory_notebooks)
            else:
                print(f"目录中没有找到 .ipynb 文件: {path}", file=sys.stderr)
            continue

        if path.suffix == ".ipynb":
            notebooks.append(path)
            continue

        print(f"跳过非 notebook 路径: {path}", file=sys.stderr)

    return notebooks


def target_path(notebook_path: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return notebook_path.with_suffix(".md")
    return output_dir / f"{notebook_path.parent.name}.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one or more .ipynb files, or chapter directories, into Markdown."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Notebook files or directories containing notebooks.")
    parser.add_argument("--output-dir", type=Path, help="Write all Markdown files into this directory.")
    parser.add_argument("--no-code", action="store_true", help="Skip code cells and keep narrative Markdown/output only.")
    parser.add_argument("--no-outputs", action="store_true", help="Skip saved notebook outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notebooks = discover_notebooks(args.paths)
    if not notebooks:
        print("没有找到可转换的 .ipynb 文件。", file=sys.stderr)
        return 1

    for notebook_path in notebooks:
        markdown_path = target_path(notebook_path, args.output_dir)
        convert_notebook(
            notebook_path=notebook_path,
            markdown_path=markdown_path,
            include_code=not args.no_code,
            include_outputs=not args.no_outputs,
        )
        print(f"converted {notebook_path} -> {markdown_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
