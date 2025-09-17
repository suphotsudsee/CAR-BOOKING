"""Office Vehicle Booking System - FastAPI Application"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.api_v1.api import api_router
from app.db import async_session_factory
from app.middleware import AuditLogMiddleware, MaintenanceModeMiddleware
from app.models import User
from app.services.notification import notification_broadcaster
from app.utils import InvalidTokenError, decode_token

# Setup logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Office Vehicle Booking System API",
    description="ระบบจองรถสำนักงาน - Vehicle booking and management system API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Set up CORS
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS or ["*"]
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Maintenance mode and audit logging middleware
maintenance_exempt_paths = (
    f"{settings.API_V1_STR}/system",
    f"{settings.API_V1_STR}/health",
    "/health",
    "/docs",
    "/openapi",
)

audit_ignored_paths = (
    "/docs",
    "/openapi",
    "/static",
)

app.add_middleware(
    MaintenanceModeMiddleware,
    exempt_path_prefixes=maintenance_exempt_paths,
)
app.add_middleware(
    AuditLogMiddleware,
    ignored_path_prefixes=audit_ignored_paths,
)

# Mount static files
app.mount("/static", StaticFiles(directory="uploads"), name="static")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Office Vehicle Booking System API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint that streams real-time notifications to clients."""

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload.get("sub"))
    except (InvalidTokenError, TypeError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        if user is None or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await notification_broadcaster.connect(user_id, websocket)
    await notification_broadcaster.broadcast(
        user_id, {"type": "connection.established"}
    )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_broadcaster.disconnect(user_id, websocket)
    except Exception:  # pragma: no cover - safety catch-all
        notification_broadcaster.disconnect(user_id, websocket)
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
