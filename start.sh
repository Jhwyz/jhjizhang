#!/bin/bash
# 启动 Telegram Bot Webhook (FastAPI)
export APP_URL="https://jhwlkjjz.onrender.com"
uvicorn main:app --host 0.0.0.0 --port $PORT
