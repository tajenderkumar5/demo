import os
from pathlib import Path

from blog_image_agent.config import AgentConfig
from blog_image_agent.pipeline import process_blog


def test_pipeline_dry_run(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")

    sample = Path("/workspace/samples/sample.md")
    assert sample.exists()

    out_assets = tmp_path / "assets"
    cfg = AgentConfig()

    result = process_blog(
        input_markdown_path=str(sample),
        assets_dir=str(out_assets),
        config=cfg,
        max_images_override=2,
    )

    assert result.output_markdown_path.exists()
    assert len(result.image_paths) == 2
    for p in result.image_paths:
        assert p.exists()
        assert p.suffix in {".png"}

    content = result.output_markdown_path.read_text(encoding="utf-8")
    assert "<!-- ai-image anchor:" in content