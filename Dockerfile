# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy source and samples
COPY blog_image_agent ./blog_image_agent
COPY README.md ./
COPY samples ./samples

# Default to dry-run unless explicitly disabled
ENV DRY_RUN=1

# Expose a clean CLI entrypoint (pass subcommands/flags after image name)
ENTRYPOINT ["python", "-m", "blog_image_agent.cli"]