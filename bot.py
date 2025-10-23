from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os

# ===== 配置 =====
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com"
PORT = 8443

# ===== 从 OKX P2P（买入 USDT 页面）获取实时人民币价格 =====
def get_okx_usdt_price():
    try:
        url = "https://www.okx.com/v3/c2c/tradingOrders/books?quoteCurrency=cny&baseCurrency=usdt&side=buy&paymentMethod=all"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        orders = data.get("data", {}).get("buy", [])
        if not orders:
            return "💰 当前 USDT 买入价格：暂无数据"
        prices = [float(o["price"]) for o in orders[:5]]
        avg_price = sum(prices) / len(prices)
        return f"💰 当前 OKX 买入 USDT 均价：{avg_price:.2f} CNY"
    except Exception as e:
        print(f"❌ 获取 OKX 价格出错: {e}")
        return "💰 当前 USDT 价格：未知"

# ===== 命令处理函数 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 OKX USDT 实时价格机器人！输入 /usdt 查看最新买入价格。")

async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_msg = get_okx_usdt_price()
    await update.message.reply_text(price_msg)

# ===== 主程序入口 =====
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usdt", usdt))

    print("🚀 启动中...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
    )

if __name__ == "__main__":
    main()
