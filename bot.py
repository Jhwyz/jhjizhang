import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import logging

# ---------- 配置 ----------
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"  # 替换成你的 Telegram Token
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"               # 替换成你的域名
PORT = 8443

# ---------- 日志 ----------
logging.basicConfig(level=logging.INFO)

# ---------- 处理消息 ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if "usdt价" in text:
        try:
            url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            prices = []
            # 解析前五个价格
            for span in soup.select("span.price")[:5]:
                prices.append(span.get_text(strip=True))
            
            msg = "🔥 OKX P2P 前五买入价格:\n" + "\n".join(prices) if prices else "⚠️ 未能获取价格"
        except Exception as e:
            msg = f"❌ 获取价格失败: {e}"
        
        await update.message.reply_text(msg)

# ---------- 创建应用 ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---------- 启动 Webhook ----------
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,                 # 必须和 webhook_url + TOKEN 一致
    webhook_url=WEBHOOK_URL + TOKEN
)
