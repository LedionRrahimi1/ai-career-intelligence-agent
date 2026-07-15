"""AI Career Intelligence Agent — FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.chroma_persist_dir.parent).mkdir(parents=True, exist_ok=True)
    init_db()
    mode = "LLM" if settings.llm_enabled else "DEMO (heuristic agents)"
    logger.info("Starting %s v%s — mode: %s", settings.app_name, settings.app_version, mode)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Multi-agent AI career platform: CV analysis, job matching, "
            "resume optimization, interview coaching, and career roadmaps."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health")
    def health():
        s = get_settings()
        return {
            "status": "ok",
            "app": s.app_name,
            "version": s.app_version,
            "llm_enabled": s.llm_enabled,
        }

    return app


app = create_app()
