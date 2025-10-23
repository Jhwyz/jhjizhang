import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 🔹 直接在这里写 Token 和 Webhook URL
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"  # 替换成你的机器人 Token
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"               # 替换成你的域名
PORT = 8443  # Render 默认端口可以用环境变量替代，这里直接写死

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
            for span in soup.select("span.price")[:5]:
                prices.append(span.get_text(strip=True))
            
            if prices:
                msg = "🔥 OKX P2P 前五买入价格:\n" + "\n".join(prices)
            else:
                msg = "⚠️ 未能获取价格，请稍后再试"
        except Exception as e:
            msg = f"❌ 获取价格失败: {e}"
        
        await update.message.reply_text(msg)

# 创建应用
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 启动 Webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN
)
