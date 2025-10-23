#!/bin/bash
export APP_URL="https://jhwlkjjz.onrender.com"
export PORT=10000

uvicorn main:app --host 0.0.0.0 --port $PORT
