from __future__ import annotations

import base64

from fastapi import HTTPException

from stego import StegoFacade
from stego.analysis import SteganalysisEngine


class AppContext:
    """Shared application services (dependency container)."""

    def __init__(self, key_file_path: str) -> None:
        self.facade = StegoFacade()
        self.steganalysis = SteganalysisEngine()
        self.default_key = self.facade.key_manager.load_or_create(key_file_path)

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
