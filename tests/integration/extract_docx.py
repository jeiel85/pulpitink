"""One-shot helper: extract paragraphs from a .docx to Markdown.

Used to prepare reference fixtures for the integration scenario without
adding `python-docx` as a project dependency. Run:

    python tests/integration/extract_docx.py <input.docx> <output.md>
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract(src: Path) -> list[str]:
    with zipfile.ZipFile(src) as zf:
        with zf.open("word/document.xml") as fh:
            tree = ET.parse(fh)
    body = tree.getroot().find(f"{WORD_NS}body")
    if body is None:
        return []
    paragraphs: list[str] = []
    for p in body.iter(f"{WORD_NS}p"):
        parts: list[str] = []
        for t in p.iter(f"{WORD_NS}t"):
            if t.text:
                parts.append(t.text)
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def to_markdown(paragraphs: list[str]) -> str:
    lines: list[str] = []
    title_emitted = False
    for raw in paragraphs:
        # Light heuristics: lines that look like a top-level title get '#'
        if not title_emitted and len(raw) < 80 and re.search(r"로마서|설교|서론|복음", raw):
            lines.append(f"# {raw}")
            title_emitted = True
            continue
        # Bible verse-only lines (e.g. "1절 ...") get treated as block quotes
        if re.match(r"^\d+\s*절", raw):
            lines.append(f"> {raw}")
        else:
            lines.append(raw)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write("usage: extract_docx.py <input.docx> <output.md>\n")
        return 2
    src = Path(argv[1])
    dst = Path(argv[2])
    if not src.exists():
        sys.stderr.write(f"입력 파일을 찾을 수 없습니다: {src}\n")
        return 1
    paragraphs = extract(src)
    if not paragraphs:
        sys.stderr.write("추출된 문단이 없습니다.\n")
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(to_markdown(paragraphs), encoding="utf-8")
    sys.stdout.write(f"OK paragraphs={len(paragraphs)} -> {dst}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
