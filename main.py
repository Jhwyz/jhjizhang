import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# === 获取 OKX P2P 价格 ===
def get_okx_price():
    try:
        url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        prices = [span.get_text(strip=True) for span in soup.select("span") if any(c.isdigit() for c in span.get_text(strip=True))]
        for p in prices:
            if p.replace('.', '', 1).isdigit():
                return p
        return "❌ 未能解析价格"
    except Exception as e:
        print("[ERROR] 获取 OKX P2P 失败:", e)
        return "❌ 获取失败"

# === Telegram 消息处理 ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in ["价格", "/price"]:
        await update.message.reply_text("⏳ 正在获取 OKX USDT 买入价...")
        price = get_okx_price()
        await update.message.reply_text(f"💹 当前 OKX P2P 买入 USDT 价格：{price}")
    else:
        await update.message.reply_text("请输入“价格”获取币价。")

# === Telegram 应用 ===
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 初始化应用并设置 Webhook
application.initialize()
application.bot.set_webhook(url=WEBHOOK_URL + TOKEN)

# === Flask 路由 ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

@app.route("/")
def home():
    return "✅ Bot is running!"

if __name__ == "__main__":
    print(f"🚀 启动 Telegram Bot，端口：{PORT}")
    app.run(host="0.0.0.0", port=PORT)
