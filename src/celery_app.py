from celery import Celery
from celery.schedules import crontab

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "theater_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-activation-tokens": {
        "task": "src.tasks.cleanup_tasks.cleanup_expired_activation_tokens",
        "schedule": crontab(minute=0),
    },
    "cleanup-expired-password-reset-tokens": {
        "task": "src.tasks.cleanup_tasks.cleanup_expired_password_reset_tokens",
        "schedule": crontab(minute="*/30"),
    },
    "cleanup-expired-refresh-tokens": {
        "task": "src.tasks.cleanup_tasks.cleanup_expired_refresh_tokens",
        "schedule": crontab(hour=0, minute=0),
    },
}

celery_app.autodiscover_tasks(["src.tasks"])
