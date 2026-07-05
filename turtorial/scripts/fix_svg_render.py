#!/usr/bin/env python3
"""Work around qlmanage's SVG thumbnail bug: it always forces a square canvas,
cropping non-square (e.g. 1280x720) diagrams. Fix: pad the SVG into a square
canvas ourselves (so nothing gets cropped), render via qlmanage, then crop the
padding back off with sips."""
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_BG = "#fbf7ef"


def get_svg_dims(svg_text: str) -> tuple[int, int]:
    m = re.search(r'<svg[^>]*\bviewBox="0 0 (\d+) (\d+)"', svg_text)
    return int(m.group(1)), int(m.group(2))


def get_bg_color(svg_text: str) -> str:
    m = re.search(r'\.bg\s*\{\s*fill\s*:\s*(#[0-9a-fA-F]{3,6})', svg_text)
    return m.group(1) if m else DEFAULT_BG


def wrap_square(svg_path: Path, out_path: Path) -> tuple[int, int, int]:
    text = svg_path.read_text(encoding="utf-8")
    width, height = get_svg_dims(text)
    bg = get_bg_color(text)
    size = max(width, height)
    offset = (size - height) / 2

    open_tag_match = re.search(r"<svg[^>]*>", text)
    inner = text[open_tag_match.end():]
    inner = re.sub(r"</svg>\s*$", "", inner.rstrip())

    wrapped = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
<rect width="{size}" height="{size}" fill="{bg}"/>
<g transform="translate(0, {offset})">
{inner}
</g>
</svg>"""
    out_path.write_text(wrapped, encoding="utf-8")
    return width, height, size


def render_and_crop(svg_path: Path, out_png: Path, qlmanage_size: int = 1600):
    tmp_dir = out_png.parent / "_sq_tmp"
    tmp_dir.mkdir(exist_ok=True)
    squared_svg = tmp_dir / (svg_path.stem + "_square.svg")
    width, height, size = wrap_square(svg_path, squared_svg)

    subprocess.run(
        ["qlmanage", "-t", "-s", str(qlmanage_size), "-o", str(tmp_dir), str(squared_svg)],
        check=True, capture_output=True,
    )
    thumb = tmp_dir / (squared_svg.name + ".png")
    if not thumb.exists():
        raise RuntimeError(f"qlmanage did not produce thumbnail for {svg_path}")

    scale = qlmanage_size / size
    crop_y = round((size - height) / 2 * scale)
    crop_h = round(height * scale)
    crop_w = round(width * scale)

    subprocess.run(
        [
            "sips", "--cropOffset", str(crop_y), "0",
            "--cropToHeightWidth", str(crop_h), str(crop_w),
            str(thumb), "--out", str(out_png),
        ],
        check=True, capture_output=True,
    )
    print(f"{svg_path.name} -> {out_png.name}  ({width}x{height}, no crop)")


if __name__ == "__main__":
    pairs = [
        ("LG-02-tools/images/tool-context-boundary-cn.svg", "lg02-tool-context-boundary.png"),
        ("LG-02-tools/images/pancreatic-cancer-tools-boundary.svg", "lg02-pancreatic-migration.png"),
        ("LG-03-human-in-the-loop/images/three-interrupt-positions.svg", "three-interrupt-positions.png"),
        ("LG-04-memory/images/memory-panorama-cn.svg", "lg04-panorama.png"),
        ("LG-05-subgraphs/images/node-parallel-reducer-cn.svg", "lg05-node-parallel-reducer.png"),
        ("LG-05-subgraphs/images/subgraph-boundary-cn.svg", "lg05-subgraph-boundary.png"),
        ("LG-06-prebuilt-agents/images/create-agent-anatomy-cn.svg", "lg06-create-agent-anatomy.png"),
        ("LG-06-prebuilt-agents/images/prebuilt-vs-custom-cn.svg", "lg06-prebuilt-vs-custom.png"),
        ("LG-06-prebuilt-agents/images/supervisor-swarm-cn.svg", "lg06-supervisor-swarm.png"),
        ("LG-07-streaming/images/blackbox-vs-stream-cn.svg", "lg07-blackbox-vs-stream.png"),
        ("LG-07-streaming/images/stream-modes-overview-cn.svg", "lg07-stream-modes-overview.png"),
        ("LG-08-deepagent/images/deepagent-architecture-cn.svg", "lg08-architecture.png"),
    ]
    turtorial_root = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(exist_ok=True)

    for src_rel, out_name in pairs:
        src = turtorial_root / src_rel
        out = out_dir / out_name
        render_and_crop(src, out)
