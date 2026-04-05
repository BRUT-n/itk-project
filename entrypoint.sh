#!/bin/bash

set -e

echo "--- Запуск миграций ---"
uv run alembic upgrade head

echo "--- Запуск сервера ---"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000