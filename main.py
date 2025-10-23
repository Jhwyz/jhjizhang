import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TOKEN = "你的BotToken"

# ---------- 获取 OKX 前五个 CNY 买入 USDT 价格 ----------
def get_okx_prices():
    url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # 找到前五个价格，OKX 页面结构可能变化，需要调整选择器
    prices = []
    table_rows = soup.select("table tbody tr")  # 可能需要调整选择器
    for row in table_rows[:5]:
        price_td = row.select_one("td")  # 第一个 td 是价格
        if price_td:
            prices.append(price_td.get_text(strip=True))
    return prices

# ---------- Telegram Bot 命令 ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("发送 /price 查询 OKX 前五个买入 USDT 价格")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prices = get_okx_prices()
        if prices:
            msg = "OKX 前五个 CNY 买入 USDT 价格:\n" + "\n".join(prices)
        else:
            msg = "获取价格失败，请稍后重试"
    except Exception as e:
        msg = f"获取价格出错: {e}"
    await update.message.reply_text(msg)

# ---------- 启动 Bot ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))

# Webhook 方式可以用 run_polling 简化部署
app.run_polling()
