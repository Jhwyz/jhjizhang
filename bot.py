import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

# ===== 配置 =====
BOT_TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com"
PORT = 10000

URL = "https://www.okx.com/v3/c2c/tradingOrders/books"

def get_okx_params():
    """生成OKX请求参数 - 只获取买入价格"""
    return {
        "quoteCurrency": "CNY",
        "baseCurrency": "USDT",
        "paymentMethod": "all",
        "showTrade": "false",
        "receivingAds": "false",
        "isAbleFilter": "false",
        "showFollow": "false",
        "showAlreadyTraded": "false",
        "side": "sell",  # 买入 USDT
        "userType": "all",
        "t": str(int(time.time() * 1000))
    }

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt",
    "Accept": "application/json, text/plain, */*"
}

def get_okx_buy_prices():
    """获取OKX USDT买入价格前十名"""
    try:
        params = get_okx_params()
        res = requests.get(URL, params=params, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
        sellers = data.get("data", {}).get("sell", [])

        if not sellers:
            return "💰 当前 USDT 买入价格：暂无数据"

        message = "💰 OKX USDT 买入价格前十名：\n\n"
        for i, seller in enumerate(sellers[:10], 1):
            name = seller.get("nickName", "未知卖家")
            price = seller.get("price", "未知价格")
            message += f"{i}. {name} - {price} CNY\n"
        
        return message

    except Exception as e:
        return f"❌ 获取 OKX 价格出错: {e}"

# Telegram命令处理函数
async def start(update: Update, context):
    """处理/start命令"""
    welcome_text = "🤖 OKX USDT买入价格机器人\n\n命令：/price - 获取USDT买入价格前十名"
    await update.message.reply_text(welcome_text)

async def price(update: Update, context):
    """处理/price命令"""
    price_info = get_okx_buy_prices()
    await update.message.reply_text(price_info)

async def echo(update: Update, context):
    """处理其他消息"""
    await update.message.reply_text("请输入 /price 获取USDT买入价格前十名")

def main():
    """主函数"""
    # 创建Telegram应用
    application = Application.builder().token(BOT_TOKEN).build()

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # 设置webhook
    async def setup_webhook():
        await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        print("✅ Webhook设置成功!")

    # 运行设置
    asyncio.run(setup_webhook())

    # 启动webhook模式
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == "__main__":
    main()
