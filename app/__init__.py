"""Ped1337 FastAPI application package."""

from __future__ import annotations

__all__ = ["create_app"]


def __getattr__(name: str):
    if name == "create_app":
        from app.main import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
