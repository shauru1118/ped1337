# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY app ./app
COPY bot ./bot
COPY stego ./stego
COPY cli.py config.py web_app.py tgbot.py ./

RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WRITABLE_DIR=/tmp/ped1337 \
    TEMP_DIR_PATH=/tmp/ped1337/temp \
    KEY_FILE_PATH=/tmp/ped1337/key.key \
    GENERATED_STATIC_DIR=/tmp/ped1337/generated \
    RUN_TELEGRAM_BOT=false \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /tmp/ped1337/temp /tmp/ped1337/generated \
    && chown -R appuser:appuser /tmp/ped1337

COPY --from=builder --chown=appuser:appuser /app /app
COPY --chown=appuser:appuser static ./static
COPY --chown=appuser:appuser templates ./templates

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=3)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
