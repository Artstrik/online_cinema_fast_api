"""
Background tasks module for the Theater application.

This module contains Celery tasks for:
- Cleanup operations (expired tokens)
- Email notifications
- User notifications
"""

from .cleanup_tasks import cleanup_expired_refresh_tokens
