"""Email delivery service and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

import emails
from emails.backend.smtp import MailResponse
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from app.core.config import settings
from app.core.logging import get_logger
from app.models.notification import EmailNotification


logger = get_logger(__name__)


class EmailNotConfiguredError(RuntimeError):
    """Raised when email settings are incomplete."""


@dataclass(slots=True)
class EmailDeliveryResult:
    """Result of a delivery attempt returned by the email service."""

    status_code: int
    status_text: str
    message_id: Optional[str]


@dataclass(slots=True)
class RenderedEmailTemplate:
    """Container for rendered email template content."""

    html: Optional[str]
    text: Optional[str]


class EmailTemplateRenderer:
    """Render email templates stored on disk."""

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        base_path = template_dir or Path(__file__).resolve().parent.parent / "templates" / "email"
        self._environment = Environment(
            loader=FileSystemLoader(str(base_path)),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict[str, Any]) -> RenderedEmailTemplate:
        """Render the HTML and plaintext variants of a template."""

        base_name = template_name.replace(".html", "").replace(".txt", "")
        html_content = self._render_if_exists(f"{base_name}.html", context)
        text_content = self._render_if_exists(f"{base_name}.txt", context)
        return RenderedEmailTemplate(html=html_content, text=text_content)

    def _render_if_exists(self, template_name: str, context: dict[str, Any]) -> Optional[str]:
        try:
            template = self._environment.get_template(template_name)
        except TemplateNotFound:
            return None
        return template.render(**context)


class EmailService:
    """High level email sending orchestration."""

    def __init__(
        self,
        *,
        renderer: Optional[EmailTemplateRenderer] = None,
    ) -> None:
        self._renderer = renderer or EmailTemplateRenderer()

    @property
    def is_configured(self) -> bool:
        """Return ``True`` when all mandatory SMTP settings are available."""

        return bool(
            settings.EMAIL_HOST
            and settings.EMAIL_FROM
            and settings.EMAIL_USERNAME
            and settings.EMAIL_PASSWORD
        )

    def deliver_notification(self, notification: EmailNotification) -> EmailDeliveryResult:
        """Send the provided :class:`EmailNotification`."""

        if not self.is_configured:
            raise EmailNotConfiguredError("Email service is not fully configured.")

        rendered = self._renderer.render(notification.template_name, notification.context or {})

        if not (rendered.html or rendered.text):
            raise TemplateNotFound(notification.template_name)

        mail_from = (
            settings.EMAIL_FROM_NAME or "Office Vehicle Booking System",
            settings.EMAIL_FROM,
        )

        text_body = rendered.text
        html_body = rendered.html or rendered.text

        message = emails.Message(
            subject=notification.subject,
            mail_from=mail_from,
            text=text_body,
            html=html_body,
        )

        headers: dict[str, str] = {}
        if notification.reply_to:
            headers["Reply-To"] = notification.reply_to

        if headers:
            message.headers.update(headers)

        response = self._send(
            message=message,
            to=notification.to_email,
            cc=notification.cc or [],
            bcc=notification.bcc or [],
        )

        logger.info(
            "email_delivery_attempt",
            to=notification.to_email,
            subject=notification.subject,
            status_code=response.status_code,
            message_id=response.message_id,
        )

        return EmailDeliveryResult(
            status_code=response.status_code,
            status_text=response.status,
            message_id=response.message_id,
        )

    def _send(
        self,
        *,
        message: emails.Message,
        to: str,
        cc: Iterable[str],
        bcc: Iterable[str],
    ) -> MailResponse:
        return message.send(
            to=to,
            cc=list(cc) or None,
            bcc=list(bcc) or None,
            smtp={
                "host": settings.EMAIL_HOST,
                "port": settings.EMAIL_PORT,
                "user": settings.EMAIL_USERNAME,
                "password": settings.EMAIL_PASSWORD,
                "tls": settings.EMAIL_USE_TLS,
            },
        )


email_service = EmailService()


__all__ = [
    "email_service",
    "EmailService",
    "EmailNotConfiguredError",
    "EmailDeliveryResult",
    "EmailTemplateRenderer",
]