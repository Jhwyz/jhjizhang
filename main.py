import hmac
import hashlib
import time
import requests
import re
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler
)

# ------------------- 配置 -------------------
# Telegram
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = 8443

# OKX API
OKX_API_KEY = "01a0cf85-df0f-4d2d-b034-f863f7177369"
OKX_API_SECRET = "6ACD89EC0F81CD76CC24072BC824FD58"
OKX_PASSPHRASE = "Yue990304."
OKX_BASE_URL = "https://www.okx.com"

# ------------------- 数据存储 -------------------
DATA_FILE = "data.json"
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
except:
    data = {
        "admins": [],
        "transactions": [],
        "rate": 0.0,
        "exchange": 0.0,
        "running": False,
        "history": {}
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ------------------- 格式化账单 -------------------
def format_message(transactions):
    bj_now = datetime.utcnow() + timedelta(hours=8)
    date_str = bj_now.strftime("%Y年%-m月%-d日")
    header = f"🌟 天 官 记账机器人 🌟\n{date_str}\n"

    in_tx = [t for t in transactions if t['type'] == 'in']
    in_lines = [f"💰 已入款（{len(in_tx)}笔）："]
    for t in in_tx:
        try:
            time_dt = datetime.fromisoformat(t['time'])
            time_str = time_dt.strftime("%H:%M:%S")
        except:
            time_str = "未知时间"
        amt_after_fee = t['amount'] * (1 - t['rate']/100)
        usd = amt_after_fee / t['exchange'] if t['exchange'] > 0 else 0.0
        in_lines.append(f"  {time_str} {t['amount']} - {t['rate']}% / {t['exchange']} = {usd:.2f} by @{t['user']}")

    out_tx = [t for t in transactions if t['type'] == 'out']
    out_lines = [f"📤 已下发（{len(out_tx)}笔）："]
    for t in out_tx:
        try:
            time_dt = datetime.fromisoformat(t['time'])
            time_str = time_dt.strftime("%H:%M:%S")
        except:
            time_str = "未知时间"
        out_lines.append(f"  {time_str} {t['amount']} by @{t['user']}")

    total_in = sum(t['amount'] for t in in_tx)
    total_out = sum(t['amount'] for t in out_tx)
    usd_total = sum((t['amount'] * (1 - t['rate']/100)) / t['exchange'] for t in in_tx if t['exchange'] > 0)

    summary_lines = [
        f"\n📊 总入款金额：{total_in}",
        f"💵 当前费率：{data['rate']}%",
        f"💱 当前汇率：{data['exchange']}",
        f"✅ 应下发：{usd_total:.2f} (USDT)",
        f"📤 已下发：{total_out} (USDT)",
        f"❌ 未下发：{usd_total - total_out:.2f} (USDT)"
    ]
    return header + "\n".join(in_lines + out_lines + summary_lines)

# ------------------- 上课/下课 -------------------
async def start_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        data["admins"].append(user)
        save_data()
    data["running"] = True
    data["transactions"] = []
    await update.message.reply_text(f"✅ 机器人已启用，管理员: @{user}")

async def end_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        return
    chat_id = update.effective_chat.id
    if chat_id not in data['history']:
        data['history'][chat_id] = []
    data['history'][chat_id].append({
        "date": datetime.utcnow().isoformat(),
        "transactions": data["transactions"]
    })
    data["transactions"] = []
    data["running"] = False
    save_data()
    await update.message.reply_text("✅ 机器人已关闭，本次账单已保存到历史。")

# ------------------- 设置费率/汇率 -------------------
async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        return
    match = re.search(r"(\d+(\.\d+)?)\s*%?", update.message.text)
    if match:
        data["rate"] = float(match.group(1))
        save_data()
        await update.message.reply_text(f"✅ 设置费率 {data['rate']}% 成功")
    else:
        await update.message.reply_text("请使用: 设置费率5% 格式")

async def set_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        return
    match = re.search(r"(\d+(\.\d+)?)", update.message.text)
    if match:
        data["exchange"] = float(match.group(1))
        save_data()
        await update.message.reply_text(f"✅ 设置汇率 {data['exchange']} 成功")
    else:
        await update.message.reply_text("请使用: 设置汇率 6.5 格式")

# ------------------- OKX C2C 买入前10商家 -------------------
def get_okx_c2c_buy_list(limit=10):
    endpoint = "/api/v5/c2c/order-book"
    url = OKX_BASE_URL + endpoint
    params = {
        "baseCurrency": "USDT",
        "quoteCurrency": "CNY",
        "side": "sell",
        "limit": limit
    }

    timestamp = str(time.time())
    msg = timestamp + 'GET' + endpoint
    signature = hmac.new(
        OKX_API_SECRET.encode('utf-8'),
        msg.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data_json = resp.json()
        orders = []
        for item in data_json.get("data", []):
            price = item.get("price")
            seller = item.get("nickName", "未知商家")
            orders.append((price, seller))
        return orders[:limit]
    except Exception as e:
        print("获取 OKX C2C 数据失败:", e)
        return []

# ------------------- z0 指令 -------------------
async def z0(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ 正在获取 OKX C2C 实时报价，请稍候...")
    orders = get_okx_c2c_buy_list(limit=10)
    if not orders:
        await update.message.reply_text("❌ 无法获取 OKX C2C 实时报价，请稍后再试。")
        return
    msg = "💱 OKX C2C USDT 实时报价（CNY）\n\n🟢 买入（商家卖出 USDT）\n"
    for i, (price, seller) in enumerate(orders, start=1):
        msg += f"{i}️⃣ 价格：{price} 元 — 商家：{seller}\n"
    await update.message.reply_text(msg.strip())

# ------------------- 消息处理 -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # 计算器
    if re.fullmatch(r'[\d\s\.\+\-\*/\(\)]+', text):
        try:
            result = eval(text, {"__builtins__": None}, {})
            await update.message.reply_text(f"{text} = {result}")
        except:
            await update.message.reply_text("❌ 表达式错误，请检查格式")
        return

    # z0 指令
    if text.lower() == "z0":
        await z0(update, context)
        return

    # 这里可以继续添加记账、管理员功能等逻辑

# ------------------- 启动 -------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("z0", z0))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN
)
