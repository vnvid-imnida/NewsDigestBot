#!/bin/sh
set -e

echo "=== News Digest Bot Startup ==="
echo "Timestamp: $(date)"

echo "Running database migrations..."
alembic upgrade head

echo "Starting News Digest Bot..."
exec python main.py
