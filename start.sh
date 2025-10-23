#!/bin/bash

# Render 上默认端口
PORT=${PORT:=10000}

# 启动 FastAPI + PTB Webhook
uvicorn main:app --host 0.0.0.0 --port $PORT
