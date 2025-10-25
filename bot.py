from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import json
import os
import re
from datetime import datetime, timedelta, timezone
import time
import requests

# =======================
# 配置
# =======================
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 8443))
DATA_FILE = "data.json"

# OKX API
OKX_URL = "https://www.okx.com/v3/c2c/tradingOrders/books"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt",
    "Accept": "application/json, text/plain, */*"
}

# Trojan-Go Socks5 代理
PROXIES = {
    "http": "socks5h://127.0.0.1:1080",
    "https": "socks5h://127.0.0.1:1080"
}

# =======================
# 数据初始化
# =======================
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

# =======================
# 北京时间
# =======================
def get_bj_now():
    return datetime.now(tz=timezone.utc) + timedelta(hours=8)

# =======================
# OKX USDT 卖家价格查询
# =======================
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
        res = requests.get(OKX_URL, params=params, headers=HEADERS, timeout=10, proxies=PROXIES)
        res.raise_for_status()
        data_json = res.json()
        sellers = data_json.get("data", {}).get("sell", [])
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

# =======================
# 格式化账单
# =======================
def format_message(transactions):
    bj_now = get_bj_now()
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

# =======================
# 上课/下课
# =======================
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
        "date": get_bj_now().isoformat(),
        "transactions": data["transactions"]
    })
    data["transactions"] = []
    data["running"] = False
    save_data()
    await update.message.reply_text("✅ 机器人已关闭，本次账单已保存到历史。")

# =======================
# 设置费率/汇率
# =======================
async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match = re.search(r"(\d+(\.\d+)?)", update.message.text)
    if match:
        data["rate"] = float(match.group(1))
        save_data()
        await update.message.reply_text(f"✅ 设置费率 {data['rate']}% 成功")
    else:
        await update.message.reply_text("请使用: 设置费率5% 格式")

async def set_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match = re.search(r"(\d+(\.\d+)?)", update.message.text)
    if match:
        data["exchange"] = float(match.group(1))
        save_data()
        await update.message.reply_text(f"✅ 设置汇率 {data['exchange']} 成功")
    else:
        await update.message.reply_text("请使用: 设置汇率 6.5 格式")

# =======================
# 安全计算器
# =======================
def safe_eval(expr: str):
    if not re.match(r"^[0-9+\-*/().\s]+$", expr):
        return "❌ 表达式包含非法字符"
    try:
        result = eval(expr, {"__builtins__": None}, {})
        return f"{expr} = {result}"
    except:
        return "❌ 表达式计算出错"

# =======================
# 菜单
# =======================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("设置费率", callback_data="rate")],
        [InlineKeyboardButton("设置汇率", callback_data="exchange")],
        [InlineKeyboardButton("添加管理员", callback_data="add_admin")],
        [InlineKeyboardButton("删除管理员", callback_data="del_admin")],
        [InlineKeyboardButton("查看历史账单", callback_data="show_history")],
        [InlineKeyboardButton("清空本群历史账单", callback_data="clear_history")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("请选择操作:", reply_markup=reply_markup)

# =======================
# 按钮回调
# =======================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.username
    chat_id = query.message.chat.id
    await query.answer()

    if query.data == "rate":
        await query.message.reply_text("请输入: 设置费率7.12")
    elif query.data == "exchange":
        await query.message.reply_text("请输入: 设置汇率 7.12")
    elif query.data == "add_admin":
        if user not in data["admins"]:
            await query.message.reply_text("只有管理员可以添加管理员")
            return
        await query.message.reply_text("请回复要添加管理员的用户消息")
        context.user_data["action"] = "add_admin"
    elif query.data == "del_admin":
        if user not in data["admins"]:
            await query.message.reply_text("只有管理员可以删除管理员")
            return
        await query.message.reply_text("请回复要删除管理员的用户消息")
        context.user_data["action"] = "del_admin"
    elif query.data == "show_history":
        if chat_id not in data['history'] or not data['history'][chat_id]:
            await query.message.reply_text("本群没有历史账单")
        else:
            msgs = []
            for idx, h in enumerate(data['history'][chat_id], 1):
                dt = datetime.fromisoformat(h['date']).astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
                detail = "\n".join([f"{t['type']} {t['amount']} @{t['user']} {t['rate']}% / {t['exchange']}" for t in h['transactions']])
                msgs.append(f"{idx}. {dt} 上课账单 {len(h['transactions'])} 笔\n{detail}")
            await query.message.reply_text("\n\n".join(msgs))
    elif query.data == "clear_history":
        data['history'][chat_id] = []
        save_data()
        await query.message.reply_text("本群历史账单已清空")

# =======================
# 消息处理
# =======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user.username

    # ---------- 处理按钮动作 ----------
    if "action" in context.user_data:
        if context.user_data["action"] == "add_admin":
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                if target_user.username not in data['admins']:
                    data['admins'].append(target_user.username)
                    save_data()
                    await update.message.reply_text(f"✅ 已成功添加管理员 @{target_user.username}")
                else:
                    await update.message.reply_text(f"⚠️ @{target_user.username} 已是管理员")
            else:
                await update.message.reply_text("❌ 请回复要添加管理员的用户消息")
            context.user_data["action"] = None
            return

        if context.user_data["action"] == "del_admin":
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                if target_user.username in data['admins']:
                    data['admins'].remove(target_user.username)
                    save_data()
                    await update.message.reply_text(f"✅ 已成功删除管理员 @{target_user.username}")
                else:
                    await update.message.reply_text(f"⚠️ @{target_user.username} 不是管理员")
            else:
                await update.message.reply_text("❌ 请回复要删除管理员的用户消息")
            context.user_data["action"] = None
            return

    # ---------- 入账/下发 ----------
    if text.startswith("+") or text.startswith("-"):
        if user not in data["admins"]:
            await update.message.reply_text("只有管理员可以操作")
            return
        try:
            amount = float(text[1:])
            t_type = 'in' if text.startswith("+") else 'out'
            data['transactions'].append({
                "user": user,
                "amount": amount,
                "type": t_type,
                "time": get_bj_now().isoformat(),
                "rate": data["rate"],
                "exchange": data["exchange"]
            })
            save_data()
            await update.message.reply_text(format_message(data['transactions']))
        except:
            await update.message.reply_text("格式错误，请输入 +50 或 -30")
        return

    # ---------- 设置费率/汇率 ----------
    if text.startswith("设置费率"):
        await set_rate(update, context)
        return
    if text.startswith("设置汇率"):
        await set_exchange(update, context)
        return

    # ---------- 查询币价 ----------
    if text.lower() == "z0":
        msg = get_okx_usdt_unique_sellers()
        await update.message.reply_text(msg)
        return

    # ---------- 安全计算器 ----------
    if re.match(r"^[0-9+\-*/().\s]+$", text):
        await update.message.reply_text(safe_eval(text))
        return

    # ---------- 实时账单 ----------
    if text == "账单":
        if data["running"]:
            if data["transactions"]:
                await update.message.reply_text(format_message(data['transactions']))
            else:
                await update.message.reply_text("当前账单没有任何交易记录")
        else:
            await update.message.reply_text("当前没有进行中的账单，请先发送“上课”开始新账单")
        return

    # ---------- 管理员列表 ----------
    if text == "管理员":
        if data["admins"]:
            await update.message.reply_text("当前管理员列表:\n" + "\n".join([f"@{a}" for a in data["admins"]]))
        else:
            await update.message.reply_text("当前没有管理员")
        return

    # ---------- 菜单 ----------
    if text == "菜单":
        await menu(update, context)
        return

# =======================
# 启动机器人
# =======================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.Regex("^上课$"), start_class))
app.add_handler(MessageHandler(filters.Regex("^下课$"), end_class))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(MessageHandler(filters.Regex("^菜单$"), menu))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

from aiohttp import web

# 保活 HTTP 路由（Render访问 / 时返回成功）
async def keep_alive(request):
    return web.Response(text="天官机器人正常运行!")

# 添加到 Application
app.web_app.router.add_get("/", keep_alive)

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN
)
