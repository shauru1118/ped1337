from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.router import register_routes
from app.dependencies import get_app_context, get_settings
from app.services import TempCleanupService


def _start_telegram_bot() -> None:
    try:
        from bot.service import StegoBotService

        logger.info("Starting Telegram Bot thread...")
        StegoBotService().run()
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Error starting Telegram Bot: {exc}")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    settings.static_dir.mkdir(parents=True, exist_ok=True)
    settings.templates_dir.mkdir(parents=True, exist_ok=True)

    cleanup = TempCleanupService(
        temp_dir=settings.temp_dir,
        static_dir=settings.static_dir,
        max_age_seconds=settings.cleanup_max_age_seconds,
        interval_seconds=settings.cleanup_interval_seconds,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        get_app_context()
        cleanup.start()
        bot_thread: threading.Thread | None = None
        if settings.run_telegram_bot and settings.telegram_bot_token:
            bot_thread = threading.Thread(
                target=_start_telegram_bot,
                name="telegram-bot",
                daemon=True,
            )
            bot_thread.start()
        elif not settings.telegram_bot_token:
            logger.info("TELEGRAM_BOT_TOKEN not set. Running web interface only.")
        else:
            logger.info(
                "Telegram bot disabled in this process "
                "(set RUN_TELEGRAM_BOT=true or run the bot service)."
            )
        try:
            yield
        finally:
            cleanup.stop()

    app = FastAPI(
        title="Ped1337 Steganography Suite",
        description=(
            "Adaptive LSB steganography with Kuznyechik "
            "(GOST R 34.12-2015 CBC) + Zlib."
        ),
        lifespan=lifespan,
    )
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
    register_routes(app)
    return app


app = create_app()
