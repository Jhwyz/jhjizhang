import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# =============== 获取 OKX 价格函数 ===============
def get_okx_price():
    try:
        url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        price_spans = soup.select("span[data-v-37e80a9f]") or soup.select("span.price")
        for s in price_spans:
            txt = s.get_text(strip=True)
            if txt.replace('.', '', 1).isdigit():
                return txt
        return "❌ 未找到价格"
    except Exception as e:
        print("❌ 获取价格错误：", e)
        return "⚠️ 获取价格失败"

# =============== 指令响应 ===============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 欢迎使用天官助手！\n发送“价格”即可查看当前 OKX USDT 价格。")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ 正在获取价格，请稍候...")
    price = get_okx_price()
    await update.message.reply_text(f"💹 当前 OKX USDT 买入价：{price}")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in ["价格", "汇率", "/price"]:
        await price(update, context)
    elif text == "/start":
        await start(update, context)
    else:
        await update.message.reply_text("🤖 可用指令：\n• 价格 — 获取 OKX USDT 当前买入价")

# =============== Telegram 应用 ===============
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("price", price))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200

@app.route("/")
def home():
    return "✅ Bot is running!"

# =============== 启动 ===============
if __name__ == "__main__":
    print(f"🚀 启动 Telegram Bot，端口：{PORT}")
    asyncio.run(application.bot.set_webhook(url=WEBHOOK_URL + TOKEN))
    app.run(host="0.0.0.0", port=PORT)
