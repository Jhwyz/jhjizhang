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
        "admins": [],           # 管理员用户名列表
        "transactions": [],     # 最近六笔流水
        "rate": 0.0,
        "exchange": 0.0,
        "total_in": 0.0,
        "total_out": 0.0,
        "running": False
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def format_message():
    bj_now = datetime.utcnow() + timedelta(hours=8)
    date_str = bj_now.strftime("%Y年%-m月%-d日")  # Windows: "%Y年%m月%d日"
    lines = [f"🌟 天 官 记账机器人 @Atianguan 🌟", date_str]

    # 已入款
    in_transactions = [t for t in data["transactions"] if t[0].startswith("+")]
    lines.append(f"已入款（{len(in_transactions)}笔）：")
    for t in in_transactions[-6:]:
        amount_str, user_name = t
        time_prefix = datetime.utcnow() + timedelta(hours=8)
        time_prefix = time_prefix.strftime("%H:%M:%S")
        try:
            amount = float(amount_str[1:])
        except:
            amount = 0.0
        effective_amount = amount * (1 - data["rate"]/100)
        value_usdt = effective_amount / data["exchange"] if data["exchange"] != 0 else 0
        lines.append(f" {time_prefix} {amount} *{1 - data['rate']/100:.2f} / {data['exchange']} = {value_usdt:.2f} by @{user_name}")
    lines.append("")

    # 已下发
    out_transactions = [t for t in data["transactions"] if t[0].startswith("-")]
    lines.append(f"已下发（{len(out_transactions)}笔）：")
    for t in out_transactions[-6:]:
        amount_str, user_name = t
        time_prefix = datetime.utcnow() + timedelta(hours=8)
        time_prefix = time_prefix.strftime("%H:%M:%S")
        try:
            amount = float(amount_str[1:])
        except:
            amount = 0.0
        lines.append(f" {time_prefix} {amount} (USDT) by @{user_name}")

    # 总金额
    total_in = sum(float(t[0][1:]) for t in in_transactions)
    total_out = sum(float(t[0][1:]) for t in out_transactions)
    total_effective = sum(
        (float(t[0][1:]) * (1 - data["rate"]/100) / data["exchange"]) if data["exchange"] != 0 else 0
        for t in in_transactions
    )

    lines.append(f"\n总入款金额：{total_in}")
    lines.append(f"费率：{data['rate']}%")
    lines.append(f"固定汇率：{data['exchange']}")
    lines.append(f"应下发：{total_effective:.2f} (USDT)")
    lines.append(f"已下发：{total_out} (USDT)")
    lines.append(f"未下发：{total_effective - total_out:.2f} (USDT)")
    
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
    # 下课清空流水
    data["transactions"] = []
    data["total_in"] = 0.0
    data["total_out"] = 0.0
    save_data()
    await update.message.reply_text("机器人已关闭，账单记录已清空")

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

# 处理交易和管理员操作
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if not data["running"]:
        return

    # 管理员动作
    if "action" in context.user_data and context.user_data["action"] in ["add_admin", "del_admin"]:
        target = update.message.text.strip().lstrip("@")
        if context.user_data["action"] == "add_admin":
            if target not in data["admins"]:
                data["admins"].append(target)
                save_data()
                await update.message.reply_text(f"添加管理员 @{target} 成功")
        elif context.user_data["action"] == "del_admin":
            if target in data["admins"]:
                data["admins"].remove(target)
                save_data()
                await update.message.reply_text(f"删除管理员 @{target} 成功")
        context.user_data["action"] = None
        return

    # 费率/汇率设置
    text = update.message.text.strip()
    if text.startswith("设置费率"):
        await set_rate(update, context)
        return
    if text.startswith("设置汇率"):
        await set_exchange(update, context)
        return

    # 处理入款/下发
    if text.startswith("+") or text.startswith("-"):
        if user not in data["admins"]:
            await update.message.reply_text("只有管理员可以操作")
            return
        try:
            amount = float(text[1:])
            if text.startswith("+"):
                data["total_in"] += amount
            else:
                data["total_out"] += amount
            data["transactions"].append((text, user))
            if len(data["transactions"]) > 6:
                data["transactions"] = data["transactions"][-6:]
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

# 上课/下课
app.add_handler(MessageHandler(filters.Regex("^上课$"), start_class))
app.add_handler(MessageHandler(filters.Regex("^下课$"), end_class))

# 菜单
app.add_handler(CommandHandler("menu", menu))
app.add_handler(MessageHandler(filters.Regex("^菜单$"), menu))
app.add_handler(CallbackQueryHandler(button))

# 处理交易和管理员动作
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 启动 Webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL+TOKEN
)
