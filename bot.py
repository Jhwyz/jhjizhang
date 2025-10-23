import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== 配置 =====
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"  # 替换为你的 Bot Token
WEBHOOK_URL = "https://jhwlkjjz.onrender.com"              # 替换为你的域名（不要加末尾斜杠）
PORT = 8443                                                # 固定端口

# ===== 从 OKX P2P 获取实时 USDT 人民币价格 =====
def get_okx_usdt_price():
    try:
        url = "https://www.okx.com/v3/c2c/tradingOrders/books?quoteCurrency=cny&baseCurrency=usdt&side=sell&paymentMethod=all"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        orders = data.get("data", {}).get("sell", [])
        if not orders:
            return "💰 当前 USDT 价格：暂无数据"
        prices = [float(o["price"]) for o in orders[:5]]
        avg_price = sum(prices) / len(prices)
        return f"💰 当前 OKX C2C 人民币买入 USDT 均价：{avg_price:.2f} CNY"
    except Exception as e:
        print(f"❌ 获取 OKX 价格出错: {e}")
        return "💰 当前 USDT 价格：未知"

# ===== /start 命令 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 OKX USDT 实时价格机器人！输入 /usdt 查看最新价格。")

# ===== /usdt 命令 =====
async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_msg = get_okx_usdt_price()
    await update.message.reply_text(price_msg)

# ===== 主函数 =====
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usdt", usdt))

    print("🚀 启动中...")
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
    )

if __name__ == "__main__":
    asyncio.run(main())
