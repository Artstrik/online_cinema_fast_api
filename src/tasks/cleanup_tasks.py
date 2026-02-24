"""
Cleanup tasks for removing expired tokens from the database.

These tasks are executed periodically by Celery Beat.
"""
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.celery_app import celery_app
from src.config import get_settings
from src.database.models import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
)

settings = get_settings()

# Create async engine for Celery tasks
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@celery_app.task(name="tasks.cleanup_tasks.cleanup_expired_activation_tokens")
def cleanup_expired_activation_tokens():
    """
    Delete expired activation tokens from the database.

    This task runs every hour to clean up activation tokens
    that have exceeded their 24-hour expiration period.
    """
    import asyncio

    async def _cleanup():
        async with async_session_factory() as session:
            now_utc = datetime.now(timezone.utc)

            # Delete expired activation tokens
            stmt = delete(ActivationTokenModel).where(
                ActivationTokenModel.expires_at < now_utc
            )
            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            return deleted_count

    deleted_count = asyncio.run(_cleanup())
    return f"Deleted {deleted_count} expired activation tokens"


@celery_app.task(name="tasks.cleanup_tasks.cleanup_expired_password_reset_tokens")
def cleanup_expired_password_reset_tokens():
    """
    Delete expired password reset tokens from the database.

    This task runs every 30 minutes to clean up password reset tokens
    that have expired.
    """
    import asyncio

    async def _cleanup():
        async with async_session_factory() as session:
            now_utc = datetime.now(timezone.utc)

            # Delete expired password reset tokens
            stmt = delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.expires_at < now_utc
            )
            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            return deleted_count

    deleted_count = asyncio.run(_cleanup())
    return f"Deleted {deleted_count} expired password reset tokens"


@celery_app.task(name="tasks.cleanup_tasks.cleanup_expired_refresh_tokens")
def cleanup_expired_refresh_tokens():
    """
    Delete expired refresh tokens from the database.

    This task runs daily at midnight to clean up expired refresh tokens.
    """
    import asyncio

    async def _cleanup():
        async with async_session_factory() as session:
            now_utc = datetime.now(timezone.utc)

            # Delete expired refresh tokens
            stmt = delete(RefreshTokenModel).where(
                RefreshTokenModel.expires_at < now_utc
            )
            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            return deleted_count

    deleted_count = asyncio.run(_cleanup())
    return f"Deleted {deleted_count} expired refresh tokens"
