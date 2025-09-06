#!/bin/bash
# 激活虚拟环境
source .venv/bin/activate

# 启动 Gunicorn + Uvicorn worker
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
