import os
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================
# Bot 配置
# ==========================
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", "10000"))

URL = "https://www.okx.com/v3/c2c/tradingOrders/books"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt",
    "Accept": "application/json, text/plain, */*"
}

# ==========================
# 日本代理节点信息（显示用）
# ==========================
PROXY_NODE = {
    "name": "🇯🇵专线VIP1|1x 日本2|ChatGPT",
    "server": "jp2.pptv-tv.store",
    "port": 17722,
    "password": "f6df64bb-9717-4030-8387-0bd5ee1199a4",
    "sni": "data.52daishu.life"
}

# 本地 SOCKS5 端口
DEFAULT_SOCKS = os.environ.get("PROXY_SOCKS5", "socks5h://127.0.0.1:1080")

# ==========================
# 检测代理是否可用
# ==========================
def check_proxy(proxy_url: str) -> bool:
    test_url = "https://www.google.com"
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        resp = requests.get(test_url, timeout=5, proxies=proxies)
        return resp.status_code == 200
    except Exception:
        return False

if check_proxy(DEFAULT_SOCKS):
    PROXIES = {"http": DEFAULT_SOCKS, "https": DEFAULT_SOCKS}
    print(f"✅ 代理可用：{DEFAULT_SOCKS}")
    print(f"代理节点信息：{PROXY_NODE['name']} - {PROXY_NODE['server']}:{PROXY_NODE['port']}")
else:
    PROXIES = None
    print("⚠️ 代理不可用，Bot 将直接访问网络（不使用代理）")
    print(f"代理节点信息：{PROXY_NODE['name']} - {PROXY_NODE['server']}:{PROXY_NODE['port']}（未连接）")

# ==========================
# 获取 OKX 前十卖家
# ==========================
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
        resp = requests.get(URL, params=params, headers=HEADERS, timeout=15, proxies=PROXIES)
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

# ==========================
# Telegram 命令
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用 OKX USDT 实时价格机器人！\n输入 /usdt 查看前十个唯一卖家价格。"
    )

async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_msg = get_okx_usdt_unique_sellers()
    await update.message.reply_text(price_msg)

# ==========================
# 主程序入口
# ==========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usdt", usdt))
    print("🚀 Bot 启动中，Webhook 模式...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
