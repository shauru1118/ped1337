from __future__ import annotations

import base64
import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_app_context, get_settings
from stego import StegoError

router = APIRouter(tags=["extract"])


@router.post("/api/extract")
async def api_extract(
    stego: UploadFile = File(...),
    key: Optional[str] = Form(None),
):
    """Extracts and decrypts secret payload from stego container."""
    ctx = get_app_context()
    settings = get_settings()
    temp_stego = settings.temp_dir / f"web_extract_{uuid.uuid4().hex}_{stego.filename}"

    try:
        with open(temp_stego, "wb") as f:
            f.write(await stego.read())

        dec_key = ctx.resolve_key(key)
        decrypted_bytes = ctx.facade.extract_decrypted(str(temp_stego), dec_key)
        env_type, payload = ctx.facade.parse_envelope(decrypted_bytes)

        if env_type == "file":
            b64_content = base64.b64encode(payload["content"]).decode("utf-8")
            return JSONResponse(
                content={
                    "type": "file",
                    "filename": payload["filename"],
                    "content": b64_content,
                }
            )
        return JSONResponse(
            content={
                "type": "text",
                "text": payload["text"],
            }
        )
    except StegoError as e:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Ошибка демаскирования: {e}. "
                "Возможно, файл поврежден или введен неверный ключ."
            ),
        ) from e
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {e}") from e
    finally:
        if os.path.exists(temp_stego):
            try:
                os.remove(temp_stego)
            except OSError:
                pass
