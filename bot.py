import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN", "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://jhwlkjjz.onrender.com/")
PORT = int(os.environ.get("PORT", 8443))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if "usdt价" in text:
        try:
            url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            prices = []
            # 假设页面有 <span class="price"> 标签包含价格
            for span in soup.select("span.price")[:5]:
                prices.append(span.get_text(strip=True))
            
            if prices:
                msg = "🔥 OKX P2P 前五买入价格:\n" + "\n".join(prices)
            else:
                msg = "⚠️ 未能获取价格，请稍后再试"
        except Exception as e:
            msg = f"❌ 获取价格失败: {e}"
        
        await update.message.reply_text(msg)

app = ApplicationBuilder().token(TOKEN).build()
app.ad
