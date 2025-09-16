"""
API v1 router
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])