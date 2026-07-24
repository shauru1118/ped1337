"""Backward-compatible ASGI entrypoint.

Prefer: ``uvicorn app.main:app`` or ``python -m app``.
"""

from app.main import app

__all__ = ["app"]


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
