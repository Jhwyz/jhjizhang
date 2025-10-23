# main.py
import os
import httpx
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TOKEN = os.environ.get("7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c")  # 在 Render 环境中用环境变量
WEBHOOK_URL = os.environ.get("https://jhwlkjjz.onrender.com/")  # 你的 Render HTTPS URL，例如 https://your-app.onrender.com

# ---------- 查询 OKX P2P CNY 买 USDT 前五 ----------
async def fetch_okx_prices():
    url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # OKX P2P 页面的价格通常在特定 class 里，我们抓前 5 个
        prices = []
        rows = soup.select(".p2p-ads-table tbody tr")[:5]
        for row in rows:
            price_cell = row.select_one("td:nth-child(2)")
            if price_cell:
                prices.append(price_cell.text.strip())
        return prices

# ---------- /price 指令 ----------
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prices = await fetch_okx_prices()
        if not prices:
            await update.message.reply_text("❌ 获取价格失败")
            return
        msg = "💰 OKX CNY 买 USDT 前五价格:\n" + "\n".join([f"{i+1}. {p}" for i, p in enumerate(prices)])
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ 出错: {e}")

# ---------- Telegram Webhook ----------
async def start_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("price", price_command))

    # 设置 webhook
    await app.bot.set_webhook(WEBHOOK_URL + "/" + TOKEN)

    # 启动 webhook 监听
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=TOKEN
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_bot())

