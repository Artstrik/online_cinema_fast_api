#!/usr/bin/env bash
set -euo pipefail

cd /usr/src/fastapi/src

echo "Starting Celery worker..."
celery -A celery_app.celery_app worker --loglevel=${LOG_LEVEL:-info}
