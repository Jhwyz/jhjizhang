from telegram.ext import CommandHandler, Application
import requests

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 8443))

def get_okx_p2p_price():
    url = "https://www.okx.com/v3/c2c/tradingOrders/books"
    params = {
        "quoteCurrency": "cny",
        "baseCurrency": "usdt",
        "side": "sell",
        "paymentMethod": "all",
        "userType": "merchant",
        "receivingAds": "false"
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        price = res["data"][0]["price"]
        merchant = res["data"][0]["nickName"]
        return f"💹 当前 OKX P2P 买入 USDT 价格: {price} CNY（商家：{merchant}）"
    except Exception as e:
        return f"❌ 获取失败: {e}"

async def price(update, context):
    msg = get_okx_p2p_price()
    await update.message.reply_text(msg)

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("price", price))
app.run_polling()


