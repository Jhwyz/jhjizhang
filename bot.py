import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== 配置 =====
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = 10000
SCRAPINGBEE_API_KEY = "GS65DVP3XMA9M2WBRUY990MW2Z7KZSQKNC5ZZT1K2S6JAIS73NHIA5IGMPH35UU0PEWOXMG8HCF6R6FB"

# 每次启动强制设置 Webhook
r = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}{TOKEN}")
print(r.text)  # 输出确认信息

# ===== 从 OKX P2P 获取前十个卖家实时人民币价格 =====
def get_okx_usdt_prices():
    try:
        url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        # 通过 ScrapingBee 渲染 JS 页面
        res = requests.get(
            "https://app.scrapingbee.com/api/v1/",
            params={
                "api_key": SCRAPINGBEE_API_KEY,
                "url": url,
                "render_js": "true"
            },
            timeout=15
        )
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select(
            "#root > div:nth-child(4) > div > main > section > div > div > div > div > div > table > tbody > tr"
        )
        sellers = []
        for row in rows[:10]:  # 前十个卖家
            try:
                name = row.select_one("td:nth-child(1) span").text.strip()  # 卖家名字
                price = row.select_one("td:nth-child(2) span").text.strip()  # 卖价
                limit_info = row.select_one("td:nth-child(3)").text.strip()  # 限额
                pay_info = row.select_one("td:nth-child(4)").text.strip()  # 支付方式
                sellers.append((name, price, limit_info, pay_info))
            except:
                continue

        if not sellers:
            return "💰 当前 USDT 买入价格：暂无数据"

        msg = "💰 当前 OKX 买入 USDT 前十个卖家价格：\n"
        for i, (name, price, limit_info, pay_info) in enumerate(sellers, 1):
            msg += f"{i}. {name} - {price} CNY （限额 {limit_info}，支付方式：{pay_info}）\n"
        return msg
    except Exception as e:
        print(f"❌ 获取 OKX 价格出错: {e}")
        return "💰 当前 USDT 价格：未知"

# ===== 命令处理函数 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用 OKX USDT 实时价格机器人！输入 /usdt 查看前十个卖家价格。"
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
