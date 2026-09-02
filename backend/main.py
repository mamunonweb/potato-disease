"""FastAPI application: potato disease detection backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routes import chat, health, predict, report


def create_app() -> FastAPI:
    app = FastAPI(title="Potato Disease Detection API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(predict.router)
    app.include_router(report.router)
    app.include_router(chat.router)

    if config.PRELOAD_MODEL:
        from services import model

        model.get_model()

    return app


app = create_app()
