from __future__ import annotations

import base64
import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_app_context, get_settings

router = APIRouter(tags=["keys"])


@router.get("/api/keygen")
def api_keygen():
    """Generates a new random 256-bit key and returns its Base64 encoding."""
    ctx = get_app_context()
    key_bytes = ctx.facade.key_manager.generate()
    return {"key": base64.b64encode(key_bytes).decode("utf-8")}


@router.post("/api/verify")
async def api_verify(
    stego: UploadFile = File(...),
    key: Optional[str] = Form(None),
):
    """Verifies the integrity/authenticity of the payload (validates GOST MAC)."""
    ctx = get_app_context()
    settings = get_settings()
    temp_stego = settings.temp_dir / f"web_verify_{uuid.uuid4().hex}_{stego.filename}"
    try:
        with open(temp_stego, "wb") as f:
            f.write(await stego.read())

        try:
            dec_key = ctx.resolve_key(key)
        except HTTPException:
            return JSONResponse(
                content={
                    "valid": False,
                    "reason": "Некорректный формат ключа. Должен быть 32 байта Base64.",
                }
            )

        try:
            decrypted_bytes = ctx.facade.extract_decrypted(str(temp_stego), dec_key)
            env_type, payload = ctx.facade.parse_envelope(decrypted_bytes)
            if env_type == "file":
                info = (
                    f"📦 Скрытые данные: Файл '{payload['filename']}' "
                    f"({round(len(payload['content']) / 1024, 2)} KB)"
                )
            else:
                info = (
                    f"📝 Скрытые данные: Текстовое сообщение "
                    f"({len(payload['text'])} символов)"
                )
            return JSONResponse(content={"valid": True, "info": info})
        except Exception as e:  # noqa: BLE001
            err_msg = str(e)
            if "имитовставки" in err_msg or "decryption failed" in err_msg:
                reason = (
                    "Ошибка проверки имитовставки "
                    "(данные изменены, повреждены или указан неверный ключ)"
                )
            else:
                reason = f"Ошибка разбора контейнера: {err_msg}"
            return JSONResponse(content={"valid": False, "reason": reason})
    finally:
        if os.path.exists(temp_stego):
            try:
                os.remove(temp_stego)
            except OSError:
                pass
