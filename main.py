import requests
import re
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
    filters
)

# ------------------- 配置 -------------------
TOKEN = "YOUR_TOKEN_HERE"
WEBHOOK_URL = "https://yourapp.onrender.com/"
PORT = 8443

# ------------------- 数据存储 -------------------
DATA_FILE = "data.json"
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
except:
    data = {
        "admins": [],
        "rate": 0.0,
        "exchange": 0.0,
        "running": {},  # 每个群组是否运行
        "transactions": {},  # 每个群组的交易记录
        "history": {}  # 每个群组历史
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ------------------- 格式化账单 -------------------
def format_message(chat_id):
    transactions = data['transactions'].get(str(chat_id), [])
    bj_now = datetime.utcnow() + timedelta(hours=8)
    date_str = bj_now.strftime("%Y年%-m月%-d日")
    header = f"🌟 天官 记账机器人 🌟\n{date_str}\n"

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
    chat_id = str(update.effective_chat.id)

    if user not in data["admins"]:
        await update.message.reply_text("❌ 只有管理员可以启动机器人")
        return

    data["running"][chat_id] = True
    data["transactions"][chat_id] = []
    if chat_id not in data["history"]:
        data["history"][chat_id] = []
    save_data()
    await update.message.reply_text(f"✅ 机器人已启用，管理员: @{user}")

async def end_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    chat_id = str(update.effective_chat.id)

    if user not in data["admins"]:
        await update.message.reply_text("❌ 只有管理员可以关闭机器人")
        return

    # 保存历史
    data["history"].setdefault(chat_id, []).append({
        "date": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
        "transactions": data["transactions"].get(chat_id, [])
    })

    data["transactions"][chat_id] = []
    data["running"][chat_id] = False
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

# ------------------- z0 指令（抓取 P2P 买 USDT） -------------------
async def z0(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ 正在获取 OKX P2P 买 USDT 实时报价，请稍候...")
    try:
        url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        orders = []
        for item in soup.find_all("div", class_=lambda x: x and "css" in x):
            price_tag = item.find("span")
            seller_tag = item.find("div")
            if price_tag and seller_tag:
                price = price_tag.get_text(strip=True)
                seller = seller_tag.get_text(strip=True)
                orders.append((price, seller))
            if len(orders) >= 10:
                break

        if not orders:
            await update.message.reply_text("❌ 无法获取 OKX P2P 实时报价，请稍后再试。")
            return

        msg = "💱 OKX P2P 买 USDT 实时报价（CNY）\n\n"
        for i, (price, seller) in enumerate(orders, start=1):
            msg += f"{i}️⃣ 价格：{price} 元 — 商家：{seller}\n"

        await update.message.reply_text(msg.strip())

    except Exception as e:
        print("获取 OKX P2P 数据失败:", e)
        await update.message.reply_text("❌ 获取数据失败，请稍后再试。")

# ------------------- 消息处理 -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user = update.effective_user.username

    # 计算器
    if re.fullmatch(r'[\d\s\.\+\-\*/\(\)]+', text):
        try:
            result = eval(text, {"__builtins__": None}, {})
            await update.message.reply_text(f"{text} = {result}")
        except:
            await update.message.reply_text("❌ 表达式错误，请检查格式")
        return

    # z0
    if text.lower() == "z0":
        await z0(update, context)
        return

    # 记账
    if text.startswith("+") or text.startswith("-"):
        if user not in data["admins"]:
            await update.message.reply_text("❌ 只有管理员可以操作")
            return
        try:
            amount = float(text[1:])
            t_type = 'in' if text.startswith("+") else 'out'
            data['transactions'].setdefault(chat_id, []).append({
                "user": user,
                "amount": amount,
                "type": t_type,
                "time": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                "rate": data["rate"],
                "exchange": data["exchange"]
            })
            save_data()
            await update.message.reply_text(format_message(chat_id))
        except:
            await update.message.reply_text("格式错误，请输入 +50 或 -30")
        return

    # 设置费率/汇率
    if text.startswith("设置费率"):
        await set_rate(update, context)
        return
    if text.startswith("设置汇率"):
        await set_exchange(update, context)
        return

# ------------------- 启动 -------------------
app = ApplicationBuilder().token(TOKEN).build()

# 命令
app.add_handler(CommandHandler("start_class", start_class))
app.add_handler(CommandHandler("end_class", end_class))
app.add_handler(CommandHandler("z0", z0))

# 消息
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN
)

