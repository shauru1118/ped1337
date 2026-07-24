from __future__ import annotations

import os
import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.dependencies import get_app_context, get_settings
from stego import CapacityExceededError, StegoError

router = APIRouter(tags=["embed"])


@router.post("/api/embed")
async def api_embed(
    cover: UploadFile = File(...),
    payload_file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    key: Optional[str] = Form(None),
):
    """Embeds text or file into cover image using adaptive LSB."""
    ctx = get_app_context()
    settings = get_settings()
    temp_dir = settings.temp_dir
    facade = ctx.facade

    temp_cover = temp_dir / f"web_cover_{uuid.uuid4().hex}_{cover.filename}"
    temp_payload: Path | None = None
    out_stego = temp_dir / f"web_stego_{uuid.uuid4().hex}.png"

    try:
        with open(temp_cover, "wb") as f:
            f.write(await cover.read())

        enc_key = ctx.resolve_key(key)

        if payload_file and payload_file.filename:
            temp_payload = temp_dir / f"web_pay_{uuid.uuid4().hex}_{payload_file.filename}"
            payload_content = await payload_file.read()
            with open(temp_payload, "wb") as f:
                f.write(payload_content)
            envelope_bytes = facade.create_file_envelope(
                payload_file.filename, payload_content
            )
        elif text:
            envelope_bytes = facade.create_text_envelope(text)
        else:
            raise HTTPException(
                status_code=400,
                detail="Пожалуйста, введите текст или выберите файл для встраивания.",
            )

        facade.embed_encrypted(
            str(temp_cover),
            str(out_stego),
            envelope_bytes,
            enc_key,
        )

        return FileResponse(
            path=out_stego,
            filename="stego_container.png",
            media_type="image/png",
        )
    except CapacityExceededError as e:
        raise HTTPException(
            status_code=400,
            detail=(
                "Недостаточно места в изображении! Вмещается только "
                f"{round(e.required_ratio * 100, 1)}% данных."
            ),
        ) from e
    except StegoError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {e}") from e
    finally:
        def cleanup() -> None:
            for p in (temp_cover, temp_payload):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

        threading.Timer(10, cleanup).start()
