#!/bin/bash
# Render 会自动设置 $PORT 环境变量
uvicorn main:app --host 0.0.0.0 --port $PORT
