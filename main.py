import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # Render 主 URL
PORT = int(os.environ.get("PORT", 8443))

app = Flask(__name__)

# === 获取 OKX P2P 价格 ===
def get_okx_price():
    try:
        url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        prices = [span.get_text(strip=True) for span in soup.select("span.price")[:5]]
        return prices[0] if prices else "获取失败"
    except Exception as e:
        print("[ERROR] 获取 OKX P2P 失败:", e)
        return "获取失败"

# === 消息处理函数 ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "价格":
        current_price = get_okx_price()
        await update.message.reply_text(f"💹 当前 OKX P2P 买入 USDT 价格: {current_price}")

# === 创建 Telegram 应用 ===
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Flask webhook ===
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    import asyncio
    asyncio.create_task(application.process_update(update))
    return "OK", 200

@app.route("/")
def home():
    return "✅ Bot is running!"

# === 启动 Webhook ===
if __name__ == "__main__":
    import asyncio
    async def main():
        # 初始化应用
        await application.initialize()
        # 设置 Webhook 到主 URL 根路径
        await application.bot.set_webhook(WEBHOOK_URL)
        # 运行 Flask（线程启动，不阻塞 asyncio）
        from threading import Thread
        Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
        print(f"🚀 Bot 已启动，监听端口 {PORT}")

    asyncio.run(main())
