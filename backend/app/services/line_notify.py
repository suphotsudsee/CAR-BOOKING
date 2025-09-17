"""Integration helpers for LINE Notify."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import settings

LINE_NOTIFY_ENDPOINT = "https://notify-api.line.me/api/notify"


class LineNotifyError(RuntimeError):
    """Raised when the LINE Notify API returns an error."""


@dataclass
class LineNotifyResponse:
    """Result from attempting to deliver a LINE notification."""

    success: bool
    status_code: int
    message: str


class LineNotifyClient:
    """Thin async client for the LINE Notify REST API."""

    def __init__(self, default_token: Optional[str] = None, timeout: float = 10.0):
        self._default_token = default_token or settings.LINE_NOTIFY_TOKEN
        self._timeout = timeout

    async def send_message(
        self, message: str, *, token: Optional[str] = None
    ) -> LineNotifyResponse:
        """Send *message* to LINE using the supplied *token*."""

        access_token = token or self._default_token
        if not access_token:
            raise LineNotifyError("LINE Notify access token is not configured")

        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"message": message}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(LINE_NOTIFY_ENDPOINT, headers=headers, data=data)

        if response.status_code >= 400:
            try:
                payload = response.json()
                error_message = payload.get("message") or response.text
            except ValueError:  # pragma: no cover - fallback when JSON parsing fails
                error_message = response.text

            raise LineNotifyError(
                f"LINE Notify request failed with {response.status_code}: {error_message}"
            )

        return LineNotifyResponse(
            success=True,
            status_code=response.status_code,
            message="Message delivered",
        )


__all__ = [
    "LineNotifyClient",
    "LineNotifyError",
    "LineNotifyResponse",
]

