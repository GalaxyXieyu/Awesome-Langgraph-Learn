#!/usr/bin/env python3
"""把正文 XML 里的 <wb src="X.svg"/> 占位符替换成真实的 <whiteboard type="svg">…完整 SVG…</whiteboard>。

子 agent 只在正文里放占位符 `<wb src="文件名.svg"/>`（不碰 SVG 字节），
本脚本用对应章节 images 目录里的真实 SVG 内容做字节精确替换，产出可直接
`lark-cli docs +create` 的最终 XML。

用法:
    python assemble_whiteboards.py <body.xml> <images_dir> <out.xml>

说明:
- 只处理 SVG 占位符；mermaid 图由 agent 直接内联 <whiteboard type="mermaid">…</whiteboard>，无需占位符。
- 找不到的 SVG 会被删除并在结尾报 MISSING，避免留下坏标记。
- 结尾校验没有残留 <wb 、文件以 <title 开头。
"""
import re, sys, pathlib

if len(sys.argv) != 4:
    print(__doc__); sys.exit(1)

body_path, images_dir, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
body = pathlib.Path(body_path).read_text(encoding="utf-8")

missing, used = [], []

def repl(m):
    fn = m.group(1).strip()
    p = pathlib.Path(images_dir) / fn
    if not p.exists():
        missing.append(fn)
        return ""
    used.append(fn)
    return '<whiteboard type="svg">' + p.read_text(encoding="utf-8").strip() + "</whiteboard>"

pattern = re.compile(r'<wb\s+src=["\']([^"\']+)["\']\s*/>')
new, n = pattern.subn(repl, body)
pathlib.Path(out_path).write_text(new, encoding="utf-8")

print(f"placeholders_matched={n} embedded={len(used)} leftover_wb={new.count('<wb ')}")
if used:    print("embedded_svgs=" + ",".join(used))
if missing: print("MISSING_SVGS=" + ",".join(missing))
if not new.lstrip().startswith("<title"):
    print("WARN: 文件未以 <title 开头")
