import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "你的BotToken"

# ---------- 获取 OKX 前五个 CNY 买入 USDT 价格 ----------
def get_okx_prices():
    url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    prices = []
    table_rows = soup.select("table tbody tr")[:5]
    for row in table_rows:
        price_td = row.select_one("td")
        if price_td:
            prices.append(price_td.get_text(strip=True))
    return prices

# ---------- Telegram Bot 命令 ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("发送 /price 查询 OKX 前五个买入 USDT 价格")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prices = get_okx_prices()
        msg = "OKX 前五个 CNY 买入 USDT 价格:\n" + "\n".join(prices) if prices else "获取价格失败"
    except Exception as e:
        msg = f"获取价格出错: {e}"
    await update.message.reply_text(msg)

# ---------- 启动 Bot ----------
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    await app.run_polling()

import asyncio
asyncio.run(main())
