import os
import requests
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
APP_URL = os.environ.get("APP_URL", "https://jhwlkjjz.onrender.com")
PORT = int(os.environ.get("PORT", "10000"))

app = FastAPI()

# 创建 Bot Application（仅 webhook 模式）
application = ApplicationBuilder().token(TOKEN).post_init(lambda app: None).build()

# /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 欢迎使用币价查询 Bot！\n直接发送币种代码（如 USDT、BTC）即可查询当前 OKX P2P 买入价格。"
    )

# 币价查询
def get_price(symbol: str) -> str:
    try:
        symbol = symbol.upper()
        url = f"https://www.okx.com/v3/c2c/tradingOrders/book?quoteCurrency=CNY&baseCurrency={symbol}&side=buy"
        resp = requests.get(url, timeout=5).json()
        if "data" in resp and resp["data"]:
            return f"{resp['data'][0]['price']} CNY"
        return "未找到该币种的价格"
    except Exception as e:
        return f"查询失败: {e}"

# 消息处理
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip()
    price = get_price(symbol)
    await update.message.reply_text(f"💹 {symbol} 当前价格: {price}")

# 添加处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Telegram Webhook 接收
@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, Bot(TOKEN))
    await application.process_update(update)
    return {"ok": True}

# 启动时自动设置 Webhook
@app.on_event("startup")
async def set_webhook():
    bot = Bot(TOKEN)
    bot.set_webhook(f"{APP_URL}/{TOKEN}")
    print("✅ Webhook 已设置成功！")

# 本地测试/调试
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
