from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional

from .markdown_utils import Anchor

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency for DRY_RUN
    OpenAI = None  # type: ignore


@dataclass
class Placement:
    anchor_id: str
    position: str  # "after" or "before"
    prompt: str
    alt_text: str
    caption: Optional[str]
    aspect_ratio: str  # e.g., "16:9", "1:1", "4:3"


SYSTEM_PROMPT = (
    "You are an expert content illustrator. Given a blog structure with labeled anchors, "
    "propose tasteful, helpful images. Avoid charts if data is not present. Prefer illustrative, "
    "metaphoric visuals that clarify concepts. Avoid text in images when possible. Return strict JSON."
)


def _llm_plan(
    text_model: str,
    anchors: List[Anchor],
    blog_title: str,
    max_images: int,
) -> List[Placement]:
    if os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"} or OpenAI is None:
        return _heuristic_plan(anchors, blog_title, max_images)

    client = OpenAI()

    anchor_digest = [
        {
            "anchor_id": a.anchor_id,
            "kind": a.kind,
            "level": a.level,
            "text_excerpt": (a.text[:200] + ("…" if len(a.text) > 200 else "")),
            "start_line": a.start_line,
        }
        for a in anchors
    ]

    user_prompt = {
        "blog_title": blog_title,
        "max_images": max_images,
        "anchors": anchor_digest,
        "instructions": (
            "Choose up to max_images anchors. Prefer placing images AFTER anchor. "
            "Avoid the very first short intro paragraph unless a hero image is needed. "
            "Never place images back-to-back. Generate a cinematic, descriptive prompt suitable for SDXL/DALL·E. "
            "Return JSON with a 'placements' array of objects: {anchor_id, position, prompt, alt_text, caption, aspect_ratio}."
        ),
    }

    response = client.chat.completions.create(
        model=text_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_prompt)},
        ],
        response_format={"type": "json_object"},
        temperature=0.6,
    )

    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return _heuristic_plan(anchors, blog_title, max_images)

    placements_data = data.get("placements", [])
    placements: List[Placement] = []
    used_anchor_ids: set[str] = set()

    for p in placements_data:
        anchor_id = str(p.get("anchor_id", "")).strip()
        if not anchor_id or anchor_id in used_anchor_ids:
            continue
        used_anchor_ids.add(anchor_id)

        position = p.get("position", "after").lower()
        if position not in {"after", "before"}:
            position = "after"

        prompt = str(p.get("prompt", "")).strip()
        alt_text = str(p.get("alt_text", "")).strip() or "Illustration for section"
        caption = str(p.get("caption", "")).strip() or None
        aspect_ratio = str(p.get("aspect_ratio", "16:9")).strip()

        placements.append(
            Placement(
                anchor_id=anchor_id,
                position=position,
                prompt=prompt,
                alt_text=alt_text,
                caption=caption,
                aspect_ratio=aspect_ratio,
            )
        )

    if not placements:
        return _heuristic_plan(anchors, blog_title, max_images)

    return placements[:max_images]


def _heuristic_plan(anchors: List[Anchor], blog_title: str, max_images: int) -> List[Placement]:
    placements: List[Placement] = []
    # Prefer first few H2 sections and a mid-article paragraph
    for a in anchors:
        if len(placements) >= max_images:
            break
        if a.kind == "heading" and (a.level == 2 or a.level == 3) and a.text:
            placements.append(
                Placement(
                    anchor_id=a.anchor_id,
                    position="after",
                    prompt=f"Illustrative concept art for: {a.text}. Clean, editorial, modern, high-detail, soft lighting, depth of field.",
                    alt_text=f"Illustration: {a.text}",
                    caption=None,
                    aspect_ratio="16:9",
                )
            )

    if len(placements) < max_images:
        for a in anchors:
            if len(placements) >= max_images:
                break
            if a.kind == "paragraph" and len(a.text.split()) > 30:
                placements.append(
                    Placement(
                        anchor_id=a.anchor_id,
                        position="after",
                        prompt=f"Diagrammatic illustration of: {a.text[:120]}... Minimalist, editorial, vector-art style, white background.",
                        alt_text="Editorial diagram",
                        caption=None,
                        aspect_ratio="4:3",
                    )
                )
                break

    return placements[:max_images]


def plan_placements(
    text_model: str,
    anchors: List[Anchor],
    blog_title: str,
    max_images: int,
) -> List[Placement]:
    return _llm_plan(text_model=text_model, anchors=anchors, blog_title=blog_title, max_images=max_images)