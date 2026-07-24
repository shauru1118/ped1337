from __future__ import annotations

import base64
from pathlib import Path

from fastapi import HTTPException
from loguru import logger

from stego import StegoFacade
from stego.analysis import SteganalysisEngine


class AppContext:
    """Shared application services (dependency container)."""

    def __init__(
        self,
        key_file_path: str,
        default_key_b64: str | None = None,
    ) -> None:
        self.facade = StegoFacade()
        self.steganalysis = SteganalysisEngine()
        self.default_key = self._load_default_key(key_file_path, default_key_b64)

    def _load_default_key(
        self, key_file_path: str, default_key_b64: str | None
    ) -> bytes:
        if default_key_b64:
            try:
                key = base64.b64decode(default_key_b64.encode("utf-8"), validate=True)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    "DEFAULT_KEY_B64 must be a valid Base64-encoded 32-byte key."
                ) from exc
            if len(key) != 32:
                raise RuntimeError(
                    "DEFAULT_KEY_B64 must decode to exactly 32 bytes."
                )
            logger.info("Using default encryption key from DEFAULT_KEY_B64.")
            return key

        path = Path(key_file_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            return self.facade.key_manager.load_or_create(str(path))
        except OSError as exc:
            # Railway/read-only images: fall back to ephemeral in-memory key.
            logger.warning(
                "Cannot persist key at {}: {}. Using ephemeral in-memory key "
                "(set DEFAULT_KEY_B64 for a stable key across restarts).",
                path,
                exc,
            )
            return self.facade.key_manager.generate()

    def resolve_key(self, key_b64: str | None) -> bytes:
        if not key_b64:
            return self.default_key
        try:
            key = base64.b64decode(key_b64.encode("utf-8"))
            if len(key) != 32:
                raise ValueError
            return key
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=400,
                detail="Некорректный ключ. Должен быть 32-байтовым Base64 хэшем.",
            ) from exc
