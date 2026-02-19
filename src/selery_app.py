from celery import Celery
from celery.schedules import crontab

from src.config import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "theater_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Configure periodic tasks with Celery Beat
celery_app.conf.beat_schedule = {
    # Delete expired activation tokens every hour
    "cleanup-expired-activation-tokens": {
        "task": "tasks.cleanup_tasks.cleanup_expired_activation_tokens",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Delete expired password reset tokens every 30 minutes
    "cleanup-expired-password-reset-tokens": {
        "task": "tasks.cleanup_tasks.cleanup_expired_password_reset_tokens",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    # Delete expired refresh tokens every day
    "cleanup-expired-refresh-tokens": {
        "task": "tasks.cleanup_tasks.cleanup_expired_refresh_tokens",
        "schedule": crontab(hour=0, minute=0),  # Every day at midnight
    },
}

# Auto-discover tasks in the tasks module
celery_app.autodiscover_tasks(["tasks"])
