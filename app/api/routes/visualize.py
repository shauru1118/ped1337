from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_app_context, get_settings

router = APIRouter(tags=["visualize"])


@router.post("/api/visualize")
async def api_visualize(stego: UploadFile = File(...)):
    """Generates visual LSB maps and returns web URLs for them."""
    ctx = get_app_context()
    settings = get_settings()
    temp_stego = settings.temp_dir / f"web_vis_{uuid.uuid4().hex}_{stego.filename}"

    try:
        with open(temp_stego, "wb") as f:
            f.write(await stego.read())

        views = ctx.facade.generate_visualization(str(temp_stego))
        web_urls: list[str] = []
        for path_str in views:
            path_obj = Path(path_str)
            if path_obj.exists():
                web_filename = f"vis_{uuid.uuid4().hex}_{path_obj.name}"
                dest = settings.static_dir / web_filename
                dest.write_bytes(path_obj.read_bytes())
                web_urls.append(f"/static/{web_filename}")
                try:
                    os.remove(path_obj)
                except OSError:
                    pass
        return JSONResponse(content={"urls": web_urls})
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ошибка визуализации: {e}") from e
    finally:
        if os.path.exists(temp_stego):
            try:
                os.remove(temp_stego)
            except OSError:
                pass
