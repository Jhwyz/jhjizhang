import time
import requests
from flask import Flask, request

# ===== 配置 =====
BOT_TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com"
PORT = 10000

app = Flask(__name__)

# 启动时自动设置webhook
def setup_webhook():
    """自动设置webhook"""
    webhook_url = f"{WEBHOOK_URL}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {
        'url': webhook_url
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Webhook自动设置成功: {webhook_url}")
        else:
            print(f"❌ Webhook自动设置失败: {response.text}")
    except Exception as e:
        print(f"❌ Webhook自动设置出错: {e}")

# 应用启动时自动设置webhook
setup_webhook()

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

# Telegram机器人路由
@app.route('/')
def health_check():
    return "🤖 OKX USDT价格机器人运行正常!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """处理Telegram Webhook"""
    try:
        data = request.get_json()
        
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            text = data['message']['text']
            
            if text == '/start':
                response_text = "🤖 OKX USDT买入价格机器人\n\n命令：/price - 获取USDT买入价格前十名"
            elif text == '/price':
                response_text = get_okx_buy_prices()
            else:
                response_text = "请输入 /price 获取USDT买入价格前十名"
            
            send_telegram_message(chat_id, response_text)
        
        return 'ok'
    except Exception as e:
        print(f"处理webhook出错: {e}")
        return 'error'

def send_telegram_message(chat_id, text):
    """发送消息到Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"发送Telegram消息出错: {e}")

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """手动设置webhook的备用接口"""
    webhook_url = f"{WEBHOOK_URL}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {
        'url': webhook_url
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return f"✅ Webhook设置成功: {webhook_url}"
        else:
            return f"❌ Webhook设置失败: {response.text}"
    except Exception as e:
        return f"❌ Webhook设置出错: {e}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=False)
