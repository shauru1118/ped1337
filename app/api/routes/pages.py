from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_settings

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Serves the main single page web application."""
    templates = Jinja2Templates(directory=str(get_settings().templates_dir))
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request},
        request=request,
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
