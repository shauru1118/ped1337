from fastapi import FastAPI

from app.api.routes import (
    capacity,
    embed,
    extract,
    keys,
    pages,
    steganalysis,
    visualize,
)


def register_routes(app: FastAPI) -> None:
    """Attach HTTP route modules to the application.

    FastAPI 0.139+ keeps nested ``include_router`` wrappers; including each
    module router directly on the app avoids empty route tables.
    """
    for module in (
        pages,
        embed,
        extract,
        visualize,
        keys,
        capacity,
        steganalysis,
    ):
        app.include_router(module.router)
