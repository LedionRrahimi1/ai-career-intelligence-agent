from fastapi import APIRouter

from app.api import agents, cvs

api_router = APIRouter(prefix="/api")
api_router.include_router(cvs.router)
api_router.include_router(agents.router)
