# Blog Image Agent

An agent that reads a blog post (Markdown), decides where images should go like a thoughtful content writer, generates on-brand illustrations, and inserts them back into the blog with proper alt text and captions.

Key features:
- Image planning: Finds relevant places for images using an LLM or a simple rule-based fallback
- Image generation: OpenAI image model by default, with a local placeholder generator in DRY_RUN mode
- Smart insertion: Adds images at the right anchors with clean Markdown and accessibility text
- Asset management: Saves images into a folder you control and references them with relative paths

## Quickstart

1) Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure your environment
- Copy `.env.example` to `.env` and fill values
- Or set environment variables directly

4) Try a dry run (no external API calls)
```bash
export DRY_RUN=1
python -m blog_image_agent.cli process \
  --input /workspace/samples/sample.md \
  --assets-dir /workspace/samples/assets \
  --max-images 3
```
This will create placeholder images and an `*.illustrated.md` file.

5) Use real image generation with OpenAI
```bash
unset DRY_RUN
export OPENAI_API_KEY=sk-...
python -m blog_image_agent.cli process \
  --input /workspace/samples/sample.md \
  --assets-dir /workspace/samples/assets \
  --max-images 3 \
  --image-model gpt-image-1 \
  --text-model gpt-4o-mini
```

## CLI usage
```bash
python -m blog_image_agent.cli process \
  --input /absolute/path/to/blog.md \
  --assets-dir /absolute/path/to/assets \
  [--config /absolute/path/to/agent.config.yaml] \
  [--max-images 5] \
  [--image-model gpt-image-1] \
  [--text-model gpt-4o-mini] \
  [--hero-image/--no-hero-image]
```

Outputs:
- Saves images to `--assets-dir`
- Creates a new file next to the input named `<name>.illustrated.md`

## How it works
- Parses your Markdown and extracts candidate anchors (headings, paragraphs)
- Asks the LLM to propose insertions with prompts, alt text, and captions
- Generates images from prompts (or placeholders in DRY_RUN)
- Inserts Markdown image blocks after selected anchors

## Config
You can pass a YAML config file via `--config` or rely on environment variables. See `.env.example` for available options.

## Testing
```bash
pytest -q
```
Dry-run tests create placeholder images locally so there are no external dependencies.

## Notes
- The agent is conservative: it avoids inserting images back-to-back and near the very top unless a hero image is requested.
- Works best for expository articles with clear section structure.