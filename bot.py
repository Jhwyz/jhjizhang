import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os

# ===== 配置 =====
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"  # 替换为你的 Bot Token
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # 替换为你的域名
PORT = int(os.environ.get("PORT", 8443))  # 可以直接写 PORT = 8443

# ===== 从 OKX 获取 USDT 人民币报价 =====
def get_okx_usdt_price():
    try:
        url = "https://www.okx.com/v3/c2c/tradingOrders/books?quoteCurrency=cny&baseCurrency=usdt&side=sell&paymentMethod=all"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        orders = data.get("data", {}).get("sell", [])
        if not orders:
            return "💰 当前 USDT 价格：暂无数据"

        # 取前5个卖家的报价计算平均价
        prices = [float(order["price"]) for order in orders[:5]]
        avg_price = sum(prices) / len(prices)
        return f"💰 当前 OKX C2C 人民币买入 USDT 均价：{avg_price:.2f} CNY"
    except Exception as e:
        print(f"❌ 获取 OKX 价格出错: {e}")
        return "💰 当前 USDT 价格：未知"

# ===== 命令 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 OKX USDT 价格机器人！输入 /usdt 查看最新价格。")

async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_message = get_okx_usdt_price()
    await update.message.reply_text(price_message)

# ===== 主程序 =====
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usdt", usdt))

    print("🚀 启动中...")
    await app.initialize()
    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
    )
    print(f"✅ Webhook 已启动: {WEBHOOK_URL}/{TOKEN}")

    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
