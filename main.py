from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import json
import os
import re
from datetime import datetime, timedelta

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 8443))

DATA_FILE = "data.json"

# 初始化数据
try:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
except:
    data = {
        "admins": [],
        "transactions": [],
        "rate": 0.0,
        "exchange": 0.0,
        "running": False
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def format_message():
    bj_now = datetime.utcnow() + timedelta(hours=8)
    date_str = bj_now.strftime("%Y年%-m月%-d日")  # Windows 可改 %Y年%m月%d日
    lines = ["jhwlkj 记账机器人", date_str]

    in_list = [t for t in data["transactions"] if t["type"] == "in"][-6:]
    out_list = [t for t in data["transactions"] if t["type"] == "out"][-6:]

    lines.append("已入款（{}笔）：".format(len(in_list)))
    for t in in_list:
        lines.append(f" {t['time']} {t['amount']} / {t['exchange']}={t['actual']:.2f} by @{t['user']}")

    lines.append("")
    lines.append("已下发（{}笔）：".format(len(out_list)))
    for t in out_list:
        lines.append(f" {t['time']} {t['amount']} ({t['total_in']}) by @{t['user']}")

    total_in = sum(t['amount'] for t in data["transactions"] if t["type"]=="in")
    total_out = sum(t['amount'] for t in data["transactions"] if t["type"]=="out")
    rate = data["rate"]
    exchange = data["exchange"]
    should_send = total_in / exchange * (1 - rate/100) if exchange != 0 else 0
    not_sent = should_send - total_out

    lines.append("")
    lines.append(f"总入款金额：{total_in}")
    lines.append(f"费率：{rate}%")
    lines.append(f"固定汇率：{exchange}")
    lines.append(f"应下发：{should_send:.2f} (USDT)")
    lines.append(f"已下发：{total_out} (USDT)")
    lines.append(f"未下发：{not_sent:.2f} (USDT)")

    return "\n".join(lines)

async def start_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        data["admins"].append(user)
        save_data()
    data["running"] = True
    await update.message.reply_text(f"机器人已启用，管理员: @{user}")

async def end_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        return
    data["running"] = False
    data["transactions"] = []  # 下课清空所有记录
    save_data()
    await update.message.reply_text("机器人已关闭，账单已清空")

async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        return
    text = update.message.text
    match = re.search(r"(\d+(\.\d+)?)", text)
    if match:
        data["rate"] = float(match.group(1))
        save_data()
        await update.message.reply_text(f"设置费率 {data['rate']}% 成功")
    else:
        await update.message.reply_text("请使用: 设置费率5% 格式")

async def set_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user not in data["admins"]:
        return
    text = update.message.text
    match = re.search(r"(\d+(\.\d+)?)", text)
    if match:
        data["exchange"] = float(match.group(1))
        save_data()
        await update.message.reply_text(f"设置汇率 {data['exchange']} 成功")
    else:
        await update.message.reply_text("请使用: 设置汇率 6.5 格式")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if not data["running"]:
        return

    # 管理员操作
    if "action" in context.user_data and context.user_data["action"] in ["add_admin","del_admin"]:
        target = update.message.text.strip().lstrip("@")
        if context.user_data["action"] == "add_admin" and target not in data["admins"]:
            data["admins"].append(target)
            save_data()
            await update.message.reply_text(f"添加管理员 @{target} 成功")
        elif context.user_data["action"] == "del_admin" and target in data["admins"]:
            data["admins"].remove(target)
            save_data()
            await update.message.reply_text(f"删除管理员 @{target} 成功")
        context.user_data["action"] = None
        return

    # 费率汇率操作
    text = update.message.text.strip()
    if text.startswith("设置费率"):
        await set_rate(update, context)
        return
    if text.startswith("设置汇率"):
        await set_exchange(update, context)
        return

    # 交易操作
    if text.startswith("+") or text.startswith("-"):
        if user not in data["admins"]:
            await update.message.reply_text("只有管理员可以操作")
            return
        try:
            amount = float(text[1:])
            bj_now = datetime.utcnow() + timedelta(hours=8)
            time_str = bj_now.strftime("%H:%M:%S")
            if text.startswith("+"):
                actual = amount / data["exchange"] if data["exchange"] else 0
                data["transactions"].append({"type":"in","amount":amount,"exchange":data["exchange"],
                                             "actual":actual,"user":user,"time":time_str,"total_in":sum(t['amount'] for t in data["transactions"] if t.get("type")=="in") + amount})
            else:
                data["transactions"].append({"type":"out","amount":amount,"user":user,"time":time_str,"total_in":sum(t['amount'] for t in data["transactions"] if t.get("type")=="in")})
            save_data()
            await update.message.reply_text(format_message())
        except:
            await update.message.reply_text("格式错误，请输入 +50 或 -30")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("设置费率", callback_data="rate")],
        [InlineKeyboardButton("设置汇率", callback_data="exchange")],
        [InlineKeyboardButton("添加管理员", callback_data="add_admin")],
        [InlineKeyboardButton("删除管理员", callback_data="del_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("请选择操作:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.username
    await query.answer()
    if query.data == "rate":
        await query.message.reply_text("请输入: 设置费率5%")
    elif query.data == "exchange":
        await query.message.reply_text("请输入: 设置汇率 6.5")
    elif query.data == "add_admin":
        if user not in data["admins"]:
            await query.message.reply_text("只有管理员可以添加管理员")
            return
        await query.message.reply_text("请输入要添加的管理员用户名，例如: @username")
        context.user_data["action"] = "add_admin"
    elif query.data == "del_admin":
        if user not in data["admins"]:
            await query.message.reply_text("只有管理员可以删除管理员")
            return
        await query.message.reply_text("请输入要删除的管理员用户名，例如: @username")
        context.user_data["action"] = "del_admin"

# 创建应用
app = ApplicationBuilder().token(TOKEN).build()

# 上课下课
app.add_handler(MessageHandler(filters.Regex("^上课$"), start_class))
app.add_handler(MessageHandler(filters.Regex("^下课$"), end_class))

# 菜单
app.add_handler(CommandHandler("menu", menu))
app.add_handler(MessageHandler(filters.Regex("^菜单$"), menu))
app.add_handler(CallbackQueryHandler(button))

# 处理消息
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 启动 Webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL+TOKEN
)
