import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import time

# ===== 配置 =====
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = 10000  # 直接写端口，不用 os.environ

# 每次启动强制设置 Webhook
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}{TOKEN}")
print(r.text)  # 输出确认信息

# ===== 从 OKX JSON 接口获取前五个卖家价格 =====
def get_top_5_sellers():
    try:
        url = "https://www.okx.com/v3/c2c/tradingOrders/books"
        params = {
            "quoteCurrency": "CNY",
            "baseCurrency": "USDT",
            "paymentMethod": "all",
            "side": "sell",
            "userType": "all",
            "t": str(int(time.time() * 1000))  # 动态生成时间戳
        }
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        sellers = data.get("data", {}).get("sell", [])
        top_5 = []

        for seller in sellers[:5]:
            name = seller.get("advUserName", "未知卖家")
            price = seller.get("price", "未知价格")
            top_5.append(f"{name} - ¥{price}")

        if not top_5:
            return "💰 当前 USDT 买入价格：暂无数据"

        msg = "💰 当前 OKX 买入 USDT 前五个卖家价格：\n" + "\n".join([f"{i+1}. {p}" for i, p in enumerate(top_5)])
        return msg
    except Exception as e:
        print(f"❌ 获取 OKX 价格出错: {e}")
        return "💰 当前 USDT 价格：未知"

# ===== 命令处理函数 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 OKX USDT 实时价格机器人！输入 /usdt 查看前五个卖家价格。")

async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_msg = get_top_5_sellers()
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
