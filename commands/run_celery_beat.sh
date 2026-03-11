#!/usr/bin/env bash
set -euo pipefail

cd /usr/src/fastapi/src

echo "Starting Celery beat..."
celery -A celery_app.celery_app beat --loglevel=${LOG_LEVEL:-info}
