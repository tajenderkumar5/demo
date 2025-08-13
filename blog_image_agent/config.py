from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    text_model: str = Field(default=os.getenv("TEXT_MODEL", "gpt-4o-mini"))
    image_model: str = Field(default=os.getenv("IMAGE_MODEL", "gpt-image-1"))
    max_images: int = Field(default=int(os.getenv("MAX_IMAGES", "5")))

    default_width: int = Field(default=int(os.getenv("DEFAULT_WIDTH", "1280")))
    default_height: int = Field(default=int(os.getenv("DEFAULT_HEIGHT", "720")))

    hero_image: bool = Field(default=os.getenv("HERO_IMAGE", "false").lower() in {"1", "true", "yes"})

    compress_webp: bool = Field(default=os.getenv("COMPRESS_WEBP", "true").lower() in {"1", "true", "yes"})
    webp_quality: int = Field(default=int(os.getenv("WEBP_QUALITY", "82")))

    output_suffix: str = Field(default=os.getenv("OUTPUT_SUFFIX", ".illustrated.md"))

    assets_dir: Optional[str] = Field(default=os.getenv("ASSETS_DIR"))


def load_config(config_path: Optional[str]) -> AgentConfig:
    base = AgentConfig()
    if not config_path:
        return base

    path = Path(config_path)
    if not path.exists():
        return base

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    merged = base.model_dump()
    merged.update({k: v for k, v in data.items() if v is not None})
    return AgentConfig(**merged)