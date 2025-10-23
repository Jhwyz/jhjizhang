from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests
from bs4 import BeautifulSoup

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # 替换成你 Render 的 URL
PORT = int(os.environ.get("PORT", 8443))

OKX_URL = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"

# ---------- 查询前五个价格 ----------
async def okx_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        }
        res = requests.get(OKX_URL, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 找到价格元素（网页结构可能会变化，这里按目前网页结构解析）
        prices = []
        for tag in soup.select("div.O_price")[:5]:  # 前五个
            prices.append(tag.get_text(strip=True))
        
        if prices:
            msg = "OKX P2P 前五个买入 USDT 价格:\n" + "\n".join(prices)
        else:
            msg = "未找到价格，请稍后重试。"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"查询失败: {e}")


# ---------- 创建应用 ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("okx", okx_price))

# ---------- 启动 Webhook ----------
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN
)
