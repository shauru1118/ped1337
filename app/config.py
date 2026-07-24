from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_token(raw: str | None) -> str | None:
    if raw is None:
        return None
    token = raw.strip()
    if token.lower() in {"", "false", "0", "none", "null", "undefined"}:
        return None
    return token


@dataclass(frozen=True)
class AppSettings:
    """Application runtime settings loaded from environment variables."""

    base_dir: Path
    telegram_bot_token: str | None
    admin_chat_id: str | None
    temp_dir: Path
    static_dir: Path
    templates_dir: Path
    key_file_path: Path
    run_telegram_bot: bool
    host: str
    port: int
    cleanup_max_age_seconds: int
    cleanup_interval_seconds: int

    @classmethod
    def from_env(cls) -> "AppSettings":
        base = BASE_DIR
        temp = Path(os.getenv("TEMP_DIR_PATH") or (base / "temp"))
        key = Path(os.getenv("KEY_FILE_PATH") or (base / "key.key"))
        token = _normalize_token(os.getenv("TELEGRAM_BOT_TOKEN"))

        run_bot = _env_flag("RUN_TELEGRAM_BOT", "false")
        # If a real token is present and RUN_TELEGRAM_BOT is unset, enable the bot.
        if token and os.getenv("RUN_TELEGRAM_BOT") is None:
            run_bot = True

        return cls(
            base_dir=base,
            telegram_bot_token=token,
            admin_chat_id=os.getenv("ADMIN_CHAT_ID") or None,
            temp_dir=temp,
            static_dir=base / "static",
            templates_dir=base / "templates",
            key_file_path=key,
            run_telegram_bot=run_bot,
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            cleanup_max_age_seconds=int(os.getenv("CLEANUP_MAX_AGE_SECONDS", "300")),
            cleanup_interval_seconds=int(os.getenv("CLEANUP_INTERVAL_SECONDS", "60")),
        )


settings = AppSettings.from_env()

# Backward-compatible module-level aliases (bot / legacy imports).
TELEGRAM_BOT_TOKEN = settings.telegram_bot_token
ADMIN_CHAT_ID = settings.admin_chat_id
TEMP_DIR_PATH = str(settings.temp_dir)
KEY_FILE_PATH = str(settings.key_file_path)
