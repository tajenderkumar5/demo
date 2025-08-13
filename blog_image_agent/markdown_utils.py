from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

from markdown_it import MarkdownIt


@dataclass
class Anchor:
    anchor_id: str
    kind: Literal["heading", "paragraph"]
    level: Optional[int]
    text: str
    start_line: int
    end_line: int


def build_markdown_parser() -> MarkdownIt:
    return MarkdownIt()


def extract_anchors(markdown_text: str) -> List[Anchor]:
    md = build_markdown_parser()
    tokens = md.parse(markdown_text)

    anchors: List[Anchor] = []
    running_index = 1

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok.type == "heading_open":
            level = int(tok.tag.replace("h", "")) if tok.tag.startswith("h") else None
            inline = tokens[i + 1]
            text = inline.content.strip() if inline.type == "inline" else ""
            start, end = tok.map if tok.map else (0, 0)
            anchors.append(
                Anchor(
                    anchor_id=f"a{running_index}",
                    kind="heading",
                    level=level,
                    text=text,
                    start_line=start,
                    end_line=end,
                )
            )
            running_index += 1
            i += 3
            continue

        if tok.type == "paragraph_open":
            inline = tokens[i + 1]
            text = inline.content.strip() if inline.type == "inline" else ""
            start, end = tok.map if tok.map else (0, 0)
            # Skip empty/very short paragraphs
            if text and len(text.split()) >= 5:
                anchors.append(
                    Anchor(
                        anchor_id=f"a{running_index}",
                        kind="paragraph",
                        level=None,
                        text=text[:220],
                        start_line=start,
                        end_line=end,
                    )
                )
                running_index += 1
            i += 3
            continue

        i += 1

    return anchors


def insert_block_after_line(original_text: str, insertion_line: int, block: str) -> str:
    lines = original_text.splitlines()
    insertion_index = max(0, min(len(lines), insertion_line))

    # Ensure surrounding blank line for readability
    prefix_blank = [""] if insertion_index > 0 and lines[insertion_index - 1].strip() != "" else []
    suffix_blank = [""] if insertion_index < len(lines) and (insertion_index >= len(lines) or lines[insertion_index].strip() != "") else []

    new_lines = lines[:insertion_index] + prefix_blank + [block] + suffix_blank + lines[insertion_index:]
    return "\n".join(new_lines) + ("\n" if original_text.endswith("\n") else "")