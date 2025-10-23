# main.py
import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
)

# =====================
# 配置
# =====================
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
PORT = int(os.environ.get("PORT", "10000"))
APP_URL = os.environ.get("APP_URL", "https://jhwlkjjz.onrender.com")

# =====================
# Flask 应用
# =====================
app = Flask(__name__)

# =====================
# 创建 Telegram Bot Application
# =====================
application = ApplicationBuilder().token(TOKEN).build()

# =====================
# 获取币价函数
# =====================
def get_price(symbol: str) -> str:
    try:
        symbol = symbol.upper()
        url = f"https://www.okx.com/v3/c2c/tradingOrders/book?quoteCurrency=CNY&baseCurrency={symbol}&side=buy"
        resp = requests.get(url, timeout=5).json()
        if "data" in resp and resp["data"]:
            price = resp["data"][0]["price"]
            return f"{price} CNY"
        return "未找到该币种的价格"
    except Exception as e:
        return f"查询失败: {e}"

# =====================
# /start 命令
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 欢迎使用币价查询 Bot！\n直接发送币种代码（如 USDT、BTC）即可查询当前 OKX P2P 买入价格。"
    )

# =====================
# 消息处理
# =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip()
    price = get_price(symbol)
    await update.message.reply_text(f"💹 {symbol} 当前价格: {price}")

# =====================
# 添加处理器
# =====================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# =====================
# Flask 路由，用于接收 Telegram Webhook
# =====================
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, Bot(TOKEN))
    await application.process_update(update)
    return "OK", 200

# =====================
# 设置 Webhook
# =====================
@app.route("/", methods=["GET"])
def set_webhook():
    bot = Bot(TOKEN)
    success = bot.set_webhook(f"{APP_URL}/{TOKEN}")
    return "Webhook 设置成功!" if success else "Webhook 设置失败!", 200

# =====================
# 启动 Flask
# =====================
if __name__ == "__main__":
    print(f"🚀 Bot 已启动，监听端口 {PORT}")
    app.run(host="0.0.0.0", port=PORT)
