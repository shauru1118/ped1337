from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_app_context, get_settings

router = APIRouter(tags=["capacity"])


@router.post("/api/capacity")
async def api_capacity(cover: UploadFile = File(...)):
    """Calculates maximum embedding capacity of the cover image."""
    ctx = get_app_context()
    settings = get_settings()
    temp_cover = settings.temp_dir / f"web_cap_{uuid.uuid4().hex}_{cover.filename}"
    try:
        with open(temp_cover, "wb") as f:
            f.write(await cover.read())
        cap = ctx.facade.calculate_capacity(str(temp_cover))
        return JSONResponse(content=cap)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if os.path.exists(temp_cover):
            try:
                os.remove(temp_cover)
            except OSError:
                pass
