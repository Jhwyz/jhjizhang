from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"  # 替换为你的 Bot Token
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # 替换为你的域名
PORT = int(os.environ.get("PORT", 8443))  # 可以直接写 PORT = 8443

async def get_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查询 USDT 价格"""
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTUSDT")  # 示例 API
        data = res.json()
        price = data.get("price", "未知")
        await update.message.reply_text(f"💰 当前 USDT 价格：{price}")
    except Exception as e:
        await update.message.reply_text(f"查询失败: {e}")

def main():
    # 创建机器人应用
    app = ApplicationBuilder().token(TOKEN).build()

    # 添加处理器
    app.add_handler(CommandHandler("usdt", get_usdt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_usdt))

    # 启动 Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL + TOKEN
    )

if __name__ == "__main__":
    main()
