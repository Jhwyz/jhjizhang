#!/bin/bash
# 设置 Telegram Webhook 的 URL（用你的 Render 服务域名替换 YOUR_DOMAIN）
WEBHOOK_URL="https://YOUR_DOMAIN/${TELEGRAM_BOT_TOKEN}"

# 设置 webhook
python - <<EOF
from telegram import Bot
import os
Bot(os.environ["TELEGRAM_BOT_TOKEN"]).delete_webhook()
Bot(os.environ["TELEGRAM_BOT_TOKEN"]).set_webhook(url=os.environ.get("WEBHOOK_URL", "$WEBHOOK_URL"))
EOF

# 启动 FastAPI
exec uvicorn main:app --host 0.0.0.0 --port $PORT
