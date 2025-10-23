import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import requests

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"  # 替换为你的 Bot Token
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # 替换为你的域名
PORT = 8443

async def get_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查询 USDT 价格"""
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTUSDT")  # 示例 API
        data = res.json()
        price = data.get("price", "未知")
        await update.message.reply_text(f"💰 当前 USDT 价格：{price}")
    except Exception as e:
        await update.message.reply_text(f"查询失败: {e}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # 初始化应用
    await app.initialize()

    # 添加处理器
    app.add_handler(CommandHandler("usdt", get_usdt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_usdt))

    # 启动 webhook
    await app.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL + TOKEN
    )

    print("Bot 已启动，Webhook 已就绪")

    # 阻塞运行
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
