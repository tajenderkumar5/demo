from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .config import AgentConfig
from .image_gen import ImageGenConfig, ImageGenerator
from .markdown_utils import extract_anchors
from .planner import Placement, plan_placements
from .inserter import plan_insertions


@dataclass
class PipelineResult:
    output_markdown_path: Path
    image_paths: List[Path]


def process_blog(
    input_markdown_path: str,
    assets_dir: str | None,
    config: AgentConfig,
    max_images_override: int | None = None,
) -> PipelineResult:
    input_path = Path(input_markdown_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input markdown not found: {input_markdown_path}")

    raw = input_path.read_text(encoding="utf-8")

    # Extract blog title (first heading) if present
    first_line = raw.splitlines()[0] if raw.splitlines() else ""
    blog_title = first_line.lstrip("# ").strip() if first_line.startswith("#") else input_path.stem

    anchors = extract_anchors(raw)

    max_images = max_images_override or config.max_images

    placements: List[Placement] = plan_placements(
        text_model=config.text_model, anchors=anchors, blog_title=blog_title, max_images=max_images
    )

    # Prepare image generator
    assets_root = assets_dir or config.assets_dir or str(input_path.parent / "assets")
    gen = ImageGenerator(
        config=ImageGenConfig(
            image_model=config.image_model,
            default_width=config.default_width,
            default_height=config.default_height,
            compress_webp=config.compress_webp,
            webp_quality=config.webp_quality,
        ),
        assets_dir=assets_root,
    )

    # Generate images
    generated_paths: List[Path] = []
    rel_paths: List[str] = []

    for p in placements:
        image_path = gen.generate(prompt=p.prompt, aspect_ratio=p.aspect_ratio, alt_text=p.alt_text)
        generated_paths.append(image_path)
        rel_path = os.path.relpath(image_path, start=input_path.parent)
        rel_paths.append(rel_path)

    # Prepare insertions
    placement_tuples: List[tuple[str, str, str | None]] = []
    for p, rel in zip(placements, rel_paths):
        placement_tuples.append((p.anchor_id, rel, p.caption))

    new_markdown = plan_insertions(original_markdown=raw, anchors=anchors, placements=placement_tuples)

    output_path = input_path.with_suffix("")
    output_path = output_path.with_name(output_path.name + config.output_suffix)
    output_path.write_text(new_markdown, encoding="utf-8")

    return PipelineResult(output_markdown_path=output_path, image_paths=generated_paths)