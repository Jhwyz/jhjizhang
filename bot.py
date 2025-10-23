import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import time

# ===== 配置 =====
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = 10000  # 直接写端口

# 每次启动强制设置 Webhook
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}{TOKEN}")
print(r.text)  # 输出确认信息

# ===== 从 OKX P2P 获取买入 USDT 的前五个卖家价格 =====
def get_okx_usdt_prices():
    try:
        url = "https://www.okx.com/v3/c2c/tradingOrders/books"
        params = {
            "quoteCurrency": "CNY",
            "baseCurrency": "USDT",
            "paymentMethod": "all",
            "showTrade": "false",
            "receivingAds": "false",
            "isAbleFilter": "false",
            "showFollow": "false",
            "showAlreadyTraded": "false",
            "side": "buy",  # 买入 USDT
            "userType": "all",
            "t": str(int(time.time() * 1000))  # 毫秒时间戳
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        }

        res = requests.get(url, headers=headers, params=params, timeout=10)
        data = res.json()
        orders = data.get("data", {}).get("buy", [])

        if not orders:
            return "💰 当前 USDT 买入价格：暂无数据"

        msg = "💰 当前 OKX 买入 USDT 前五个卖家价格：\n"
        for i, order in enumerate(orders[:5], 1):
            name = order.get("advUserName", "匿名")
            price = order.get("price", "未知")
            msg += f"{i}. {name} - {price} CNY\n"

        return msg

    except Exception as e:
        print(f"❌ 获取 OKX 价格出错: {e}")
        return "💰 当前 USDT 价格：未知"

# ===== 命令处理函数 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用 OKX USDT 实时价格机器人！输入 /usdt 查看前五个卖家价格。"
    )

async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_msg = get_okx_usdt_prices()
    await update.message.reply_text(price_msg)

# ===== 主程序入口 =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usdt", usdt))

    print("🚀 启动中...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}{TOKEN}",
    )

if __name__ == "__main__":
    main()
