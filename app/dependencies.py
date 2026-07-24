from __future__ import annotations

from functools import lru_cache

from app.config import AppSettings, settings
from app.services import AppContext


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return settings


@lru_cache(maxsize=1)
def get_app_context() -> AppContext:
    cfg = get_settings()
    cfg.temp_dir.mkdir(parents=True, exist_ok=True)
    cfg.generated_dir.mkdir(parents=True, exist_ok=True)
    cfg.static_dir.mkdir(parents=True, exist_ok=True)
    return AppContext(
        key_file_path=str(cfg.key_file_path),
        default_key_b64=cfg.default_key_b64,
    )
