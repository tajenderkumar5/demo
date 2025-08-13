from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency for DRY_RUN
    OpenAI = None  # type: ignore


@dataclass
class ImageGenConfig:
    image_model: str
    default_width: int
    default_height: int
    compress_webp: bool
    webp_quality: int


def _parse_aspect_ratio(aspect_ratio: str, default_width: int, default_height: int) -> Tuple[int, int]:
    try:
        parts = aspect_ratio.split(":")
        w, h = int(parts[0]), int(parts[1])
        # Fit to default width
        width = default_width
        height = int(width * h / max(1, w))
        return width, height
    except Exception:
        return default_width, default_height


class ImageGenerator:
    def __init__(self, config: ImageGenConfig, assets_dir: str):
        self.config = config
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        if not (os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"}) and OpenAI is not None:
            try:
                self._client = OpenAI()
            except Exception:
                self._client = None

    def _filename_for_prompt(self, prompt: str, ext: str = "png") -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
        return f"img-{digest}.{ext}"

    def generate(self, prompt: str, aspect_ratio: str, alt_text: str) -> Path:
        width, height = _parse_aspect_ratio(aspect_ratio, self.config.default_width, self.config.default_height)
        out_png = self.assets_dir / self._filename_for_prompt(prompt, "png")

        if os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"} or self._client is None:
            self._generate_placeholder(prompt=prompt, width=width, height=height, out_path=out_png)
        else:
            self._generate_openai(prompt=prompt, width=width, height=height, out_path=out_png)

        if self.config.compress_webp:
            self._to_webp(out_png, quality=self.config.webp_quality)

        return out_png

    def _generate_openai(self, prompt: str, width: int, height: int, out_path: Path) -> None:
        size = f"{width}x{height}"
        try:
            assert self._client is not None
            resp = self._client.images.generate(
                model=self.config.image_model,
                prompt=prompt,
                size=size,
            )
            b64 = resp.data[0].b64_json
            image_bytes = base64.b64decode(b64)
            out_path.write_bytes(image_bytes)
        except Exception as e:  # Fallback to placeholder
            self._generate_placeholder(prompt=prompt, width=width, height=height, out_path=out_path)

    def _generate_placeholder(self, prompt: str, width: int, height: int, out_path: Path) -> None:
        image = Image.new("RGB", (width, height), color=(240, 243, 247))
        draw = ImageDraw.Draw(image)

        text = (prompt[:300] + "…") if len(prompt) > 300 else prompt
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None  # type: ignore

        margin = 20
        y = margin
        for line in _wrap_text(text, line_length=48):
            draw.text((margin, y), line, fill=(60, 60, 60), font=font)
            y += 16

        image.save(out_path)

    def _to_webp(self, png_path: Path, quality: int) -> Optional[Path]:
        try:
            image = Image.open(png_path)
            webp_path = png_path.with_suffix(".webp")
            image.save(webp_path, format="WEBP", quality=quality, method=6)
            return webp_path
        except Exception:
            return None


def _wrap_text(text: str, line_length: int = 40):
    words = text.split()
    line: list[str] = []
    current_len = 0
    for word in words:
        if current_len + len(word) + (1 if line else 0) > line_length:
            yield " ".join(line)
            line = [word]
            current_len = len(word)
        else:
            line.append(word)
            current_len += len(word) + (1 if line else 0)
    if line:
        yield " ".join(line)