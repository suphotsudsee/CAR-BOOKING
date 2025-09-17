"""Maintenance mode middleware."""

from __future__ import annotations

import logging
from typing import Iterable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.db import async_session_factory
from app.services.system_config import get_system_configuration

_logger = logging.getLogger(__name__)


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """Block requests when the application is in maintenance mode."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        exempt_path_prefixes: Optional[Iterable[str]] = None,
    ) -> None:
        super().__init__(app)
        self._exempt_prefixes = tuple(exempt_path_prefixes or ())

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if self._exempt_prefixes and path.startswith(self._exempt_prefixes):
            return await call_next(request)

        try:
            async with async_session_factory() as session:
                config = await get_system_configuration(session)
        except (
            Exception
        ):  # pragma: no cover - fail open if configuration cannot be read
            _logger.exception("Failed to resolve system configuration state")
            return await call_next(request)

        if config.maintenance_mode:
            message = (
                config.maintenance_message or "System is under scheduled maintenance"
            )
            return JSONResponse(
                status_code=503,
                content={
                    "detail": message,
                    "maintenance": True,
                },
            )

        return await call_next(request)
