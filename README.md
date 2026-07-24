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

1. Deploy from repo (Dockerfile / `railway.toml`).
2. Set `TELEGRAM_BOT_TOKEN` / `ADMIN_CHAT_ID` and `RUN_TELEGRAM_BOT=true` if the bot should run inside the web service.
3. Health check: `/health`.
