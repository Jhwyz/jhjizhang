from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import os
import requests
from bs4 import BeautifulSoup

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # 例如 https://yourapp.onrender.com/
PORT = int(os.environ.get("PORT", 8443))

OKX_P2P_URL = "https://www.okx.com/p2p-markets/cny/buy-usdt"

# ---------- 获取OKX P2P 买入 USDT 前五价格 ----------
async def get_okx_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(OKX_P2P_URL, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        offers = soup.find_all('div', class_='css-1p5a3p4')[:5]
        if not offers:
            await update.message.reply_text("无法获取价格，请稍后再试")
            return
        msg = "💰 OKX P2P 买入 USDT 前五价格:\n"
        for i, offer in enumerate(offers, 1):
            price = offer.find('span', class_='css-1jv3g7').text.strip()
            amount = offer.find('span', class_='css-1jv3g7').find_next('span').text.strip()
            msg += f"{i}. 价格: {price} CNY, 可买: {amount} USDT\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"获取价格出错: {e}")

# ---------- 处理消息 ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == "usdt价":
        await get_okx_prices(update, context)

# ---------- 应用 ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN
)
