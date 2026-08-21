#!/bin/bash
set -e

echo "=== MotionIQ Backend Startup ==="
echo "Running database migrations..."
python -m alembic upgrade head || {
    echo "Warning: Alembic migration skipped or encountered an error. Proceeding with application startup..."
}

PORT_NUM="${PORT:-10000}"
echo "Starting Uvicorn on 0.0.0.0:${PORT_NUM}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_NUM}" --workers 2
