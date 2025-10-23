import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests

# ---------- 配置 ----------
TOKEN = "YOUR_BOT_TOKEN"  # 替换为你的 Token
WEBHOOK_URL = "https://yourdomain.com/"  # 替换为你部署的 URL
PORT = 8443  # Render 等云平台默认端口

# ---------- 日志 ----------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- 查询 USDT 价格 ----------
def get_usdt_price():
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTUSDT")
        data = resp.json()
        return data.get("price", "未知")
    except Exception as e:
        logger.error(f"查询 USDT 出错: {e}")
        return "查询失败"

# ---------- 命令 ----------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("欢迎使用 USDT 价格查询机器人！发送 /price 查看价格。")

def price(update: Update, context: CallbackContext):
    p = get_usdt_price()
    update.message.reply_text(f"当前 USDT 价格: {p}")

# ---------- 主函数 ----------
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("price", price))

    # 启动 Webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url=WEBHOOK_URL + TOKEN)
    updater.idle()

if __name__ == "__main__":
    main()
