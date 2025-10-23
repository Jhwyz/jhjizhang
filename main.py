import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import asyncio

# === 配置 ===
TOKEN = os.environ.get("TOKEN", "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://jhwlkjjz.onrender.com/")
PORT = int(os.environ.get("PORT", 8443))

# === 获取 OKX P2P 买入 USDT 价格 ===
def get_okx_price():
    try:
        url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        prices = [span.get_text(strip=True) for span in soup.select("span.price")[:5]]
        return prices[0] if prices else "获取失败"
    except Exception as e:
        print("获取价格失败:", e)
        return "获取失败"

# === Flask 应用 ===
app = Flask(__name__)

# === Telegram 消息处理 ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "价格":
        price = get_okx_price()
        await update.message.reply_text(f"💹 当前 OKX P2P 买入 USDT 价格: {price}")
    else:
        await update.message.reply_text("请输入 '价格' 查询当前币价。")

# === 创建 Telegram 应用 ===
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Webhook 接口 ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200

@app.route("/")
def home():
    return "✅ Bot is running!"

# === 主程序入口 ===
if __name__ == "__main__":
    # 设置 Webhook
    asyncio.run(application.bot.set_webhook(url=WEBHOOK_URL + TOKEN))
    print(f"🚀 Bot 已启动，端口 {PORT}，Webhook URL: {WEBHOOK_URL + TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
