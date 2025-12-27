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
import requests
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

PROXIES = {
    "http": "socks5h://127.0.0.1:1080",
    "https": "socks5h://127.0.0.1:1080",
}

# =======================
# OKX Session（修复 SSL EOF）
# =======================
def create_okx_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    session.proxies.update(PROXIES)
    return session


OKX_SESSION = create_okx_session()

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
def _get_okx_sync():
    params = {
        "quoteCurrency": "CNY",
        "baseCurrency": "USDT",
        "paymentMethod": "all",
        "side": "sell",
        "t": int(time.time() * 1000),
    }

    res = OKX_SESSION.get(OKX_URL, params=params, timeout=15)
    res.raise_for_status()
    sellers = res.json().get("data", {}).get("sell", [])

    if not sellers:
        return "暂无 OKX 数据"

    seen = set()
    msg = "💰 OKX 买入 USDT 前十卖家：\n"
    idx = 0
    for s in sellers:
        name = s.get("nickName")
        price = s.get("price")
        if name and name not in seen:
            seen.add(name)
            idx += 1
            msg += f"{idx}. {name} - {price} CNY\n"
            if idx >= 10:
                break
    return msg


async def get_okx():
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _get_okx_sync)
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
        lines.append(f"+{t['amount']} @{t['user']}")

    lines.append(f"\n📤 下发 {len(outs)} 笔")
    for t in outs:
        lines.append(f"-{t['amount']} @{t['user']}")

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
    await update.message.reply_text("✅ 已上课，开始记账")


async def end_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    data["history"].setdefault(str(chat_id), []).append(
        {
            "time": bj_now().isoformat(),
            "transactions": data["transactions"],
        }
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
    await update.message.reply_text("请选择：", reply_markup=InlineKeyboardMarkup(kb))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "okx":
        await q.message.reply_text(await get_okx())

    if q.data == "history":
        chat_id = str(q.message.chat.id)
        hist = data["history"].get(chat_id)
        if not hist:
            await q.message.reply_text("暂无历史")
        else:
            await q.message.reply_text(f"历史账单 {len(hist)} 次")


# =======================
# 消息处理
# =======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user.username

    if text.startswith("+") or text.startswith("-"):
        if not data["running"]:
            return
        amt = float(text[1:])
        data["transactions"].append(
            {
                "user": user,
                "amount": amt,
                "type": "in" if text.startswith("+") else "out",
                "time": bj_now().isoformat(),
            }
        )
        save_data()
        await update.message.reply_text(format_bill(data["transactions"]))
        return

    if text == "账单":
        await update.message.reply_text(format_bill(data["transactions"]))
        return

    if text == "菜单":
        await menu(update, context)
        return

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
