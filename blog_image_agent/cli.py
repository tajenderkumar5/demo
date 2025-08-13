from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich import print
from rich.console import Console
from rich.panel import Panel

from .config import AgentConfig, load_config
from .pipeline import process_blog

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def process(
    input: str = typer.Option(..., "--input", help="Absolute path to the input Markdown file"),
    assets_dir: Optional[str] = typer.Option(None, "--assets-dir", help="Directory to store generated assets"),
    config_path: Optional[str] = typer.Option(None, "--config", help="Optional YAML config file"),
    max_images: Optional[int] = typer.Option(None, "--max-images", help="Override maximum number of images"),
    image_model: Optional[str] = typer.Option(None, "--image-model", help="Override image model"),
    text_model: Optional[str] = typer.Option(None, "--text-model", help="Override text model"),
    hero_image: Optional[bool] = typer.Option(None, "--hero-image/--no-hero-image", help="Enable/disable hero image planning"),
):
    """Process a blog: plan image placements, generate images, insert them, and write an illustrated Markdown file."""
    load_dotenv()

    cfg = load_config(config_path)

    if image_model:
        cfg.image_model = image_model
    if text_model:
        cfg.text_model = text_model
    if max_images is not None:
        cfg.max_images = max_images
    if hero_image is not None:
        cfg.hero_image = hero_image

    console.print(Panel.fit("Blog Image Agent", title="Agent", border_style="blue"))
    console.log(f"Input: {input}")
    console.log(f"Assets dir: {assets_dir or cfg.assets_dir or '(auto under blog folder)'}")
    console.log(f"Models: text={cfg.text_model} image={cfg.image_model}")
    console.log(f"DRY_RUN={'on' if os.getenv('DRY_RUN') else 'off'}")

    result = process_blog(
        input_markdown_path=input,
        assets_dir=assets_dir,
        config=cfg,
        max_images_override=max_images,
    )

    console.log(f"Wrote: {result.output_markdown_path}")
    for p in result.image_paths:
        console.log(f"Image: {p}")


if __name__ == "__main__":
    app()