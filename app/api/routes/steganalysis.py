from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_app_context, get_settings

router = APIRouter(tags=["steganalysis"])


@router.post("/api/steganalysis")
async def api_steganalysis(image: UploadFile = File(...)):
    """Performs multi-channel LSB steganalysis with Chi-Square and Shannon Entropy."""
    ctx = get_app_context()
    settings = get_settings()
    temp_img = settings.temp_dir / f"web_stegoan_{uuid.uuid4().hex}_{image.filename}"
    try:
        with open(temp_img, "wb") as f:
            f.write(await image.read())

        img_array = ctx.facade.engine.image_adapter.load(str(temp_img))
        result = ctx.steganalysis.analyze(img_array, num_points=50)
        return JSONResponse(content=result.to_dict())
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"Ошибка стегоанализа: {e}"
        ) from e
    finally:
        if os.path.exists(temp_img):
            try:
                os.remove(temp_img)
            except OSError:
                pass
