"""Celery application configuration for background processing."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings


def _create_celery_app() -> Celery:
    """Initialise and configure the Celery application instance."""

    celery_app = Celery(
        "office_vehicle_booking",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks.email"],
    )

    celery_app.conf.update(
        task_default_queue="notifications",
        task_default_retry_delay=60,
        task_acks_late=True,
        worker_max_tasks_per_child=100,
        timezone="UTC",
        enable_utc=True,
    )

    celery_app.autodiscover_tasks(["app.tasks"])
    return celery_app


# Shared Celery application that can be imported by workers
celery_app = _create_celery_app()


__all__ = ["celery_app"]
