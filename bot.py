import os
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== 直接写死的 TOKEN 和 WEBHOOK =====
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", "10000"))

URL = "https://www.okx.com/v3/c2c/tradingOrders/books"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt",
    "Accept": "application/json, text/plain, */*"
}

# ===== 代理（默认本地 trojan-go 提供的 SOCKS5） =====
default_socks = os.environ.get("PROXY_SOCKS5", "socks5h://127.0.0.1:1080")
PROXIES = {"http": default_socks, "https": default_socks}

def get_okx_usdt_unique_sellers():
    params = {
        "quoteCurrency": "CNY",
        "baseCurrency": "USDT",
        "paymentMethod": "all",
        "showTrade": "false",
        "receivingAds": "false",
        "isAbleFilter": "false",
        "showFollow": "false",
        "showAlreadyTraded": "false",
        "side": "sell",
        "userType": "all",
        "t": str(int(time.time() * 1000))
    }
    try:
        resp = requests.get(URL, params=params, headers=HEADERS, timeout=15, proxies=PROXIES if default_socks else None)
        resp.raise_for_status()
        data = resp.json()
        sellers = data.get("data", {}).get("sell", [])
        if not sellers:
            return "💰 当前 USDT 买入价格：暂无数据"

        msg = "💰 当前 OKX 买入 USDT 前十个唯一卖家：\n"
        seen = set()
        count = 0
        for seller in sellers:
            name = seller.get("nickName", "未知卖家")
            price = seller.get("price", "未知价格")
            if name not in seen:
                seen.add(name)
                count += 1
                msg += f"{count}. {name} - {price} CNY\n"
                if count >= 10:
                    break
        return msg
    except Exception as e:
        return f"❌ 获取 OKX 价格出错: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 OKX USDT 实时价格机器人！\n输入 /usdt 查看前十个唯一卖家价格。")

async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_okx_usdt_unique_sellers()
    await update.message.reply_text(msg)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usdt", usdt))
    print("🚀 Bot 启动中，Webhook 模式...")
    app.run_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{TOKEN}")

if __name__ == "__main__":
    main()
