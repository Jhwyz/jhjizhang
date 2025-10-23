import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import asyncio
import os

# ---------- 配置 ----------
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"  # 替换为你的 Bot Token
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # 替换为你部署的 URL
PORT = int(os.environ.get("PORT", 8443))

# ---------- 日志 ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- 查询 USDT ----------
def get_usdt_price():
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTUSDT")
        return resp.json().get("price", "未知")
    except Exception as e:
        logger.error(f"查询 USDT 出错: {e}")
        return "查询失败"

# ---------- 命令 ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 USDT 查询机器人！发送 /price 查看价格。")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_usdt_price()
    await update.message.reply_text(f"当前 USDT 价格: {p}")

# ---------- 主函数 ----------
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))

    # 启动 Webhook
    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL + TOKEN
    )
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
