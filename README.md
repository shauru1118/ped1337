# Ped1337 Steganography Suite

Adaptive LSB steganography with Kuznyechik (GOST R 34.12-2015 CBC) + GOST MAC + Zlib.

Managed with [uv](https://docs.astral.sh/uv/).

## Stack

- FastAPI web UI (`app/`)
- Telegram bot (`bot/`)
- Domain library (`stego/`)

## Local run

```bash
# install uv if needed: curl -LsSf https://astral.sh/uv/install.sh | sh
cp .env.example .env
uv sync
uv run ped1337
# equivalent: uv run python -m app
```

Open http://127.0.0.1:8000

Telegram bot (same process): set `TELEGRAM_BOT_TOKEN` and `RUN_TELEGRAM_BOT=true` in `.env`.

Bot only:

```bash
uv run ped1337-bot
# equivalent: uv run python -m bot
```

CLI:

```bash
uv run python cli.py keygen key.key
uv run python cli.py capacity cover.png
uv run python cli.py encrypt cover.png secret.bin out.png key.key
uv run python cli.py decrypt out.png key.key > secret.bin
```

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Optional separate bot container:

```bash
docker compose --profile bot up --build
```

## Railway

1. New project from this repo (Dockerfile / `railway.toml`).
2. Variables (recommended):
   - leave `KEY_FILE_PATH` / `TEMP_DIR_PATH` unset, **or** set them under `/tmp/ped1337/...`
   - optional `DEFAULT_KEY_B64` — stable default key across restarts
   - optional `TELEGRAM_BOT_TOKEN` + `RUN_TELEGRAM_BOT=true`
3. Health check: `/health`
4. Do **not** copy local `KEY_FILE_PATH=key.key` into Railway — `/app` is often read-only.
