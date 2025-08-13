from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from .markdown_utils import Anchor, insert_block_after_line


@dataclass
class ImageBlock:
    markdown: str
    insertion_line: int


def _build_image_block(image_rel_path: str, alt_text: str, caption: str | None, anchor_id: str) -> str:
    md_img = f"![{alt_text}]({image_rel_path}) <!-- ai-image anchor:{anchor_id} -->"
    if caption:
        return md_img + "\n" + f"*{caption}*"
    return md_img


def plan_insertions(
    original_markdown: str,
    anchors: List[Anchor],
    placements: List[tuple[str, str, str | None]],
    # Each placement: (anchor_id, image_rel_path, caption)
) -> str:
    anchor_map = {a.anchor_id: a for a in anchors}

    blocks: List[ImageBlock] = []
    for anchor_id, image_rel_path, caption in placements:
        anchor = anchor_map.get(anchor_id)
        if not anchor:
            continue
        block_text = _build_image_block(image_rel_path=image_rel_path, alt_text=f"{anchor.text[:120]}", caption=caption, anchor_id=anchor_id)
        blocks.append(ImageBlock(markdown=block_text, insertion_line=anchor.end_line))

    # Sort by insertion line descending to avoid shifting as we mutate the doc
    blocks.sort(key=lambda b: b.insertion_line, reverse=True)

    result = original_markdown
    for block in blocks:
        result = insert_block_after_line(result, block.insertion_line, block.markdown)

    return result