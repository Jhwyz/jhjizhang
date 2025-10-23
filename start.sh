#!/usr/bin/env bash
# start.sh
export PORT=${PORT:-10000}
exec uvicorn main:app --host 0.0.0.0 --port $PORT
