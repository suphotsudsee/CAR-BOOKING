"""Audit logging middleware."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, Iterable, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from app.db import async_session_factory
from app.services.audit import log_audit_event
from app.utils import InvalidTokenError, decode_token

_logger = logging.getLogger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Capture an audit log entry for each incoming HTTP request."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        ignored_path_prefixes: Optional[Iterable[str]] = None,
    ) -> None:
        super().__init__(app)
        self._ignored_prefixes = tuple(ignored_path_prefixes or ())

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if self._ignored_prefixes and path.startswith(self._ignored_prefixes):
            return await call_next(request)

        start = perf_counter()
        response: Response | None = None
        error: Exception | None = None

        actor_id = self._resolve_actor(request)
        try:
            response = await call_next(request)
            return response
        except Exception as exc:  # pragma: no cover - propagate after logging
            error = exc
            raise
        finally:
            duration_ms = round((perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response else 500
            metadata: dict[str, Any] = {
                "method": request.method,
                "path": path,
                "query": dict(request.query_params),
                "latency_ms": duration_ms,
            }
            if error is not None:
                metadata["error"] = repr(error)

            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            try:
                async with async_session_factory() as session:
                    await log_audit_event(
                        session,
                        actor_id=actor_id,
                        action=request.method,
                        resource=path,
                        status_code=status_code,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        context=metadata,
                    )
            except (
                Exception
            ):  # pragma: no cover - logging must never break request flow
                _logger.exception(
                    "Failed to persist audit log entry for request %s", path
                )

    @staticmethod
    def _resolve_actor(request: Request) -> Optional[int]:
        """Attempt to resolve the actor's user id from the request token."""

        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None

        if not auth_header.lower().startswith("bearer "):
            return None

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token, expected_type="access")
        except InvalidTokenError:
            return None

        subject = payload.get("sub")
        try:
            return int(subject)
        except (TypeError, ValueError):
            return None
