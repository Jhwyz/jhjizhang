from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import json
import os
import re
import time
import asyncio
import httpx
from datetime import datetime, timedelta, timezone

# =======================
# 基础配置
# =======================
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 8443))
DATA_FILE = "data.json"

# =======================
# OKX API
# =======================
OKX_URL = "https://www.okx.com/v3/c2c/tradingOrders/books"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.okx.com/",
}

# 本地 V2Ray VMess + WS + TLS 代理
PROXIES = "socks5://127.0.0.1:1080"

# =======================
# 异步 HTTP Client (支持 SOCKS5 代理)
# =======================
async_client = httpx.AsyncClient(
    headers=HEADERS,
    proxy="socks5://127.0.0.1:1080",
    timeout=15,
)


# =======================
# 数据初始化
# =======================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {
        "admins": [],
        "transactions": [],
        "rate": 0.0,
        "exchange": 0.0,
        "running": False,
        "history": {},
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =======================
# 北京时间
# =======================
def bj_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)

# =======================
# OKX 查询
# =======================
async def get_okx():
    params = {
        "quoteCurrency": "CNY",
        "baseCurrency": "USDT",
        "paymentMethod": "all",
        "side": "sell",
        "t": int(time.time() * 1000),
    }
    try:
        res = await async_client.get(OKX_URL, params=params)
        res.raise_for_status()
        sellers = res.json().get("data", {}).get("sell", [])
        if not sellers:
            return "💰 当前 USDT 买入价格：暂无数据"
        msg = "💰 OKX 买入 USDT 前十卖家：\n"
        seen = set()
        count = 0
        for s in sellers:
            name = s.get("nickName", "未知卖家")
            price = s.get("price", "未知价格")
            if name not in seen:
                seen.add(name)
                count += 1
                msg += f"{count}. {name} - {price} CNY\n"
                if count >= 10:
                    break
        return msg
    except Exception as e:
        return f"❌ 获取 OKX 失败: {type(e).__name__}"

# =======================
# 账单格式化
# =======================
def format_bill(tx):
    header = f"📅 {bj_now().strftime('%Y-%m-%d')}\n"
    ins = [t for t in tx if t["type"] == "in"]
    outs = [t for t in tx if t["type"] == "out"]

    lines = [header, f"💰 入款 {len(ins)} 笔"]
    for t in ins:
        amt_after_fee = t["amount"] * (1 - t.get("rate", 0)/100)
        usd = amt_after_fee / t.get("exchange", 1) if t.get("exchange", 0) > 0 else 0.0
        lines.append(f"+{t['amount']} - {t.get('rate',0)}% / {t.get('exchange',0)} = {usd:.2f} by @{t['user']}")

    lines.append(f"\n📤 下发 {len(outs)} 笔")
    for t in outs:
        lines.append(f"-{t['amount']} by @{t['user']}")

    total_in = sum(t["amount"] for t in ins)
    total_out = sum(t["amount"] for t in outs)
    usd_total = sum((t["amount"] * (1 - t.get("rate",0)/100) / t.get("exchange",1)) for t in ins if t.get("exchange",0) > 0)

    lines.append(f"\n📊 总入款: {total_in}")
    lines.append(f"💵 当前费率: {data['rate']}%")
    lines.append(f"💱 当前汇率: {data['exchange']}")
    lines.append(f"✅ 应下发: {usd_total:.2f} (USDT)")
    lines.append(f"📤 已下发: {total_out} (USDT)")
    lines.append(f"❌ 未下发: {usd_total - total_out:.2f} (USDT)")

    return "\n".join(lines)

# =======================
# 上课 / 下课
# =======================
async def start_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        data["admins"].append(user)
    data["transactions"] = []
    data["running"] = True
    save_data()
    await update.message.reply_text(f"✅ 已上课，管理员: @{user}")

async def end_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data["history"].setdefault(chat_id, []).append(
        {"date": bj_now().isoformat(), "transactions": data["transactions"]}
    )
    data["transactions"] = []
    data["running"] = False
    save_data()
    await update.message.reply_text("✅ 已下课，账单已保存")

# =======================
# 菜单 & 按钮
# =======================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📊 查询 OKX", callback_data="okx")],
        [InlineKeyboardButton("📜 历史账单", callback_data="history")],
    ]
    await update.message.reply_text("请选择操作:", reply_markup=InlineKeyboardMarkup(kb))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat_id = str(q.message.chat.id)

    if q.data == "okx":
        await q.message.reply_text(await get_okx())
    elif q.data == "history":
        hist = data["history"].get(chat_id)
        if not hist:
            await q.message.reply_text("本群没有历史账单")
        else:
            msgs = []
            for idx, h in enumerate(hist, 1):
                dt = datetime.fromisoformat(h['date']).astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
                detail = "\n".join([f"{t['type']} {t['amount']} @{t['user']} {t.get('rate',0)}% / {t.get('exchange',0)}" for t in h['transactions']])
                msgs.append(f"{idx}. {dt} 上课账单 {len(h['transactions'])} 笔\n{detail}")
            await q.message.reply_text("\n\n".join(msgs))

# =======================
# 消息处理
# =======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user.username

    # ---------- 入账/下发 ----------
    if text.startswith("+") or text.startswith("-"):
        if user not in data["admins"]:
            await update.message.reply_text("只有管理员可以操作")
            return
        try:
            amount = float(text[1:])
            t_type = "in" if text.startswith("+") else "out"
            data["transactions"].append({
                "user": user,
                "amount": amount,
                "type": t_type,
                "time": bj_now().isoformat(),
                "rate": data["rate"],
                "exchange": data["exchange"]
            })
            save_data()
            await update.message.reply_text(format_bill(data["transactions"]))
        except:
            await update.message.reply_text("格式错误，请输入 +50 或 -30")
        return

    # ---------- 查询账单 ----------
    if text == "账单":
        if data["transactions"]:
            await update.message.reply_text(format_bill(data["transactions"]))
        else:
            await update.message.reply_text("当前账单没有任何交易记录")
        return

    # ---------- 菜单 ----------
    if text == "菜单":
        await menu(update, context)
        return

    # ---------- OKX ----------
    if text.lower() == "z0":
        await update.message.reply_text(await get_okx())

# =======================
# 启动
# =======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.Regex("^上课$"), start_class))
app.add_handler(MessageHandler(filters.Regex("^下课$"), end_class))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN,
)
