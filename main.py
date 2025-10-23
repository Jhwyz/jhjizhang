import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Telegram Bot Token
TOKEN = "你的BotToken"
PORT = int(os.environ.get("PORT", 8443))
WEBHOOK_URL = "https://你的域名/"  # 填写你部署的 URL

# OKX P2P 买入 USDT 页面
OKX_URL = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"

async def get_prices():
    """抓取 OKX 前五个买入 USDT 的价格"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(OKX_URL, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # P2P 页面里的价格在 data-price 属性或者特定类名里
    # 这里用示例 CSS 类选择器，根据网页实际结构可能需要调整
    prices = []
    for item in soup.select(".p2p-table .p2p-item .price")[:5]:
        prices.append(item.get_text(strip=True))

    return prices if prices else ["未能获取价格"]

async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prices = await get_prices()
        msg = "💰 OKX CNY-USDT 前五个买入价格:\n" + "\n".join(prices)
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ 获取价格失败: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("prices", prices_command))

    # 使用 webhook 部署
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL + TOKEN
    )
