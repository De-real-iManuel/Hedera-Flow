#!/bin/bash
echo "PORT environment variable: $PORT"
echo "Starting server on port ${PORT:-8000}"
uvicorn app.core.app:app --host 0.0.0.0 --port ${PORT:-8000}