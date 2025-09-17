"""
API v1 router
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    assignments,
    auth,
    bookings,
    calendar,
    drivers,
    health,
    job_runs,
    notifications,
    uploads,
    users,
    vehicles,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(
    assignments.router, prefix="/assignments", tags=["assignments"]
)
api_router.include_router(
    calendar.router, prefix="/calendar", tags=["calendar"]
)
api_router.include_router(job_runs.router, prefix="/job-runs", tags=["job-runs"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
