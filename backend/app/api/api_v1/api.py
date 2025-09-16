"""
API v1 router
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, bookings, drivers, health, users, vehicles

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
