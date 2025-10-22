from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import json, os, re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 8443))

DATA_FILE = "data.json"

# ---------- 初始化数据 ----------
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

# ---------- 格式化账单 ----------
def format_message(transactions):
    bj_now = datetime.utcnow() + timedelta(hours=8)
    date_str = bj_now.strftime("%Y年%-m月%-d日")
    header = f"🌟 天 官 记账机器人 🌟\n{date_str}\n"

    # 已入款
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

    # 已下发
    out_tx = [t for t in transactions if t['type'] == 'out']
    out_lines = [f"📤 已下发（{len(out_tx)}笔）："]
    for t in out_tx:
        try:
            time_dt = datetime.fromisoformat(t['time'])
            time_str = time_dt.strftime("%H:%M:%S")
        except:
            time_str = "未知时间"
        out_lines.append(f"  {time_str} {t['amount']} by @{t['user']}")

    # 总结
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

# ---------- 上课/下课 ----------
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

# ---------- 设置费率/汇率 ----------
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

# ---------- z0 抓取 OKX P2P ----------
async def z0(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ 正在获取 OKX C2C 实时报价，请稍候...")
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.binary_location = "/usr/bin/chromium"

        driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=chrome_options)
        driver.get("https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt")

        orders = []
        elems = driver.find_elements("css selector", ".css-1pnsb8f")  # 根据实际页面类名调整
        for elem in elems[:10]:
            orders.append(elem.text.strip())
        driver.quit()

        if not orders:
            await update.message.reply_text("❌ 获取 OKX C2C 实时报价失败")
            return

        msg = "💱 OKX C2C USDT 实时报价（CNY）\n\n"
        for i, price in enumerate(orders, 1):
            msg += f"{i}️⃣ {price}\n"

        await update.message.reply_text(msg.strip())
    except Exception as e:
        print("z0 获取失败:", e)
        await update.message.reply_text("❌ 获取数据失败，请稍后再试。")

# ---------- 消息处理 ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    text = update.message.text.strip()

    # 实时账单
    if text == "账单":
        if data["running"]:
            if data["transactions"]:
                await update.message.reply_text(format_message(data['transactions']))
            else:
                await update.message.reply_text("当前账单没有任何交易记录")
        else:
            await update.message.reply_text("当前没有进行中的账单，请先发送“上课”开始新账单")
        return

    # 管理员列表
    if text == "管理员":
        if data["admins"]:
            await update.message.reply_text("当前管理员列表:\n" + "\n".join([f"@{a}" for a in data["admins"]]))
        else:
            await update.message.reply_text("当前没有管理员")
        return

    # z0 指令
    if text.lower() == "z0":
        await z0(update, context)
        return

    # 入账/下发
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
                "time": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                "rate": data["rate"],
                "exchange": data["exchange"]
            })
            save_data()
            await update.message.reply_text(format_message(data['transactions']))
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

# ---------- 菜单 ----------
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

# ---------- 按钮回调 ----------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.username
    chat_id = query.message.chat.id
    await query.answer()

    if query.data == "rate":
        await query.message.reply_text("请输入: 设置费率5%")
    elif query.data == "exchange":
        await query.message.reply_text("请输入: 设置汇率 6.5")
    elif query.data == "add_admin":
        if user not in data["admins"]:
            await query.message.reply_text("只有管理员可以添加管理员")
            return
        await update.message.reply_text("请回复要添加管理员的用户消息")
        context.user_data["action"] = "add_admin"
    elif query.data == "del_admin":
        if user not in data["admins"]:
            await update.message.reply_text("只有管理员可以删除管理员")
            return
        await update.message.reply_text("请回复要删除管理员的用户名，例如 @username")
        context.user_data["action"] = "del_admin"
    elif query.data == "show_history":
        if chat_id not in data['history'] or not data['history'][chat_id]:
            await update.message.reply_text("本群没有历史账单")
        else:
            msgs = []
            for idx, h in enumerate(data['history'][chat_id], 1):
                dt = datetime.fromisoformat(h['date']).strftime("%Y-%m-%d %H:%M:%S")
                detail = "\n".join(
                    [f"  {t['type']} {t['amount']} @{t['user']} {t['rate']}% / {t['exchange']}"
                     for t in h['transactions']]
                )
                msgs.append(f"{idx}. {dt} 上课账单 {len(h['transactions'])} 笔\n{detail}")
            await query.message.reply_text("\n\n".join(msgs))
    elif query.data == "clear_history":
        data['history'][chat_id] = []
        save_data()
        await query.message.reply_text("本群历史账单已清空")

# ---------- 应用 ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.Regex("^上课$"), start_class))
app.add_handler(MessageHandler(filters.Regex("^下课$"), end_class))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(MessageHandler(filters.Regex("^菜单$"), menu))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL + TOKEN
)
