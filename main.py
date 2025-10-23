import os
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ====== 配置 ======
TOKEN = os.environ.get("7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c")  # 在 Render 设置环境变量 BOT_TOKEN
WEBHOOK_URL = os.environ.get("https://jhwlkjjz.onrender.com/")  # https://你的域名/
PORT = int(os.environ.get("PORT", 8443))

# ====== 获取币价函数 ======
async def get_okx_price():
    url = "https://www.okx.com/api/v5/market/ticker?instId=USDT-USDT"  # OKX 示例接口
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            data = resp.json()
            # 根据接口返回解析价格（示例，需按实际 OKX 接口调整）
            price = data["data"][0]["last"] if "data" in data else "未知"
            return price
    except Exception as e:
        return f"获取价格失败: {e}"

# ====== 消息处理函数 ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() in ["价格", "price"]:
        price = await get_okx_price()
        await update.message.reply_text(f"💹 当前 OKX P2P 买入 USDT 价格: {price}")
    else:
        await update.message.reply_text("发送“价格”即可查询币价。")

# ====== 创建 Application ======
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ====== 启动 Webhook ======
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}{TOKEN}"
    )
