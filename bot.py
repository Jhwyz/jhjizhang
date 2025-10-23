import os
import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ------------------- 配置 -------------------
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"  # 替换为你自己的 webhook 地址
PORT = 8443

# ------------------- 查询 OKX USDT 前五价格 -------------------
OKX_API = "https://www.okx.com/v3/c2c/market/ticker?instId=USDT-CNY"

async def get_usdt_prices():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(OKX_API)
            data = resp.json()
            # OKX P2P 数据可能在 "data" 或 "ticker" 字段，这里假设返回 list
            prices = []
            if isinstance(data, list):
                for i, item in enumerate(data[:5]):
                    price = item.get("price") or item.get("last") or "未知"
                    prices.append(f"{i+1}. {price} CNY")
            else:
                # fallback: 如果返回对象包含 ticker
                ticker = data.get("ticker", [])
                for i, item in enumerate(ticker[:5]):
                    price = item.get("price") or "未知"
                    prices.append(f"{i+1}. {price} CNY")
            return "\n".join(prices) if prices else "获取失败"
        except Exception as e:
            return f"获取失败: {e}"

# ------------------- 消息处理 -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ["usdt", "价格", "查询usdt"]:
        prices = await get_usdt_prices()
        await update.message.reply_text(f"🔥 OKX 买入 USDT 前五价：\n{prices}")
    else:
        await update.message.reply_text("请输入 'USDT' 查询最新价格")

# ------------------- Webhook 应用 -------------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL + TOKEN
    )
    print(f"Bot 已启动，Webhook 地址: {WEBHOOK_URL + TOKEN}")
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
