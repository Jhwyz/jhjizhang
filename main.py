from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import json, os, re
from datetime import datetime, timedelta

TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 8443))
DATA_FILE = "data.json"

# 初始化数据
try:
    with open(DATA_FILE,"r") as f:
        data=json.load(f)
except:
    data = {}

def save_data():
    with open(DATA_FILE,"w") as f:
        json.dump(data,f,default=str)

# 获取群数据
def get_group_data(chat_id):
    if str(chat_id) not in data:
        data[str(chat_id)] = {
            "admins": [],
            "transactions": [],
            "history": [],
            "rate":0.0,
            "exchange":0.0,
            "running":False
        }
        save_data()
    return data[str(chat_id)]

def format_message(group_data):
    bj_now = datetime.utcnow()+timedelta(hours=8)
    date_str = bj_now.strftime("%Y年%-m月%-d日")
    lines=[f"天 官 记账机器人@{group_data['admins'][0] if group_data['admins'] else '未知'}", date_str]
    lines.append("已入款（{}笔）：".format(len([t for t in group_data['transactions'] if t['type']=='in'])))
    for t in group_data['transactions']:
        time_str=t['time'].strftime("%H:%M:%S")
        if t['type']=='in':
            rate=group_data['rate']
            ex=group_data['exchange']
            val=t['amount']*(1-rate/100)/ex if ex>0 else 0
            lines.append(f" {time_str} {t['amount']} *{1-rate/100}/ {ex}={val:.2f} by @{t['user']}")
    lines.append("已下发（{}笔）：".format(len([t for t in group_data['transactions'] if t['type']=='out'])))
    for t in group_data['transactions']:
        if t['type']=='out':
            time_str=t['time'].strftime("%H:%M:%S")
            lines.append(f" {time_str} {t['amount']} by @{t['user']}")
    total_in=sum([t['amount'] for t in group_data['transactions'] if t['type']=='in'])
    total_out=sum([t['amount'] for t in group_data['transactions'] if t['type']=='out'])
    lines.append(f"总入款金额：{total_in}")
    lines.append(f"费率：{group_data['rate']}%")
    lines.append(f"固定汇率：{group_data['exchange']}")
    should_out=sum([t['amount']*(1-group_data['rate']/100)/group_data['exchange'] if group_data['exchange']>0 else 0 for t in group_data['transactions'] if t['type']=='in'])
    lines.append(f"应下发：{should_out:.2f} (USDT)")
    lines.append(f"已下发：{total_out} (USDT)")
    lines.append(f"未下发：{should_out-total_out:.2f} (USDT)")
    return "\n".join(lines)

# 上课
async def start_class(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    group_data=get_group_data(chat_id)
    user=update.effective_user.username
    if user not in group_data['admins']:
        group_data['admins'].append(user)
    group_data['running']=True
    save_data()
    await update.message.reply_text(f"机器人已启用，管理员: @{user}")

# 下课
async def end_class(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    group_data=get_group_data(chat_id)
    user=update.effective_user.username
    if user not in group_data['admins']:
        return
    # 保存历史账单
    if group_data['transactions']:
        record={'date':datetime.utcnow()+timedelta(hours=8),'transactions':group_data['transactions'].copy()}
        group_data['history'].append(record)
        # 保留30天历史
        group_data['history']=[r for r in group_data['history'] if datetime.utcnow()+timedelta(hours=8)-r['date']<=timedelta(days=30)]
    group_data['transactions']=[]
    group_data['running']=False
    save_data()
    await update.message.reply_text("机器人已关闭，本次账单已清空")

# 设置费率
async def set_rate(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    group_data=get_group_data(chat_id)
    user=update.effective_user.username
    if user not in group_data['admins']:
        return
    text=update.message.text
    match=re.search(r"(\d+(\.\d+)?)",text)
    if match:
        group_data['rate']=float(match.group(1))
        save_data()
        await update.message.reply_text(f"设置费率 {group_data['rate']}% 成功")
    else:
        await update.message.reply_text("请使用: 设置费率5% 格式")

# 设置汇率
async def set_exchange(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    group_data=get_group_data(chat_id)
    user=update.effective_user.username
    if user not in group_data['admins']:
        return
    text=update.message.text
    match=re.search(r"(\d+(\.\d+)?)",text)
    if match:
        group_data['exchange']=float(match.group(1))
        save_data()
        await update.message.reply_text(f"设置汇率 {group_data['exchange']} 成功")
    else:
        await update.message.reply_text("请使用: 设置汇率 6.5 格式")

# 入账/下发和管理员操作
async def handle_message(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    group_data=get_group_data(chat_id)
    user=update.effective_user.username
    if not group_data['running']:
        return
    # 管理员动作
    if "action" in context.user_data and context.user_data["action"] in ["add_admin","del_admin"]:
        target=update.message.text.strip().lstrip("@")
        # 检测用户是否在本群
        members=[m.user.username for m in await update.effective_chat.get_members() if m.user]
        if target not in members:
            await update.message.reply_text(f"@{target} 不在本群，无法添加")
            context.user_data["action"]=None
            return
        if context.user_data["action"]=="add_admin":
            if target not in group_data['admins']:
                group_data['admins'].append(target)
                save_data()
                await update.message.reply_text(f"添加管理员 @{target} 成功")
        elif context.user_data["action"]=="del_admin":
            if target in group_data['admins']:
                group_data['admins'].remove(target)
                save_data()
                await update.message.reply_text(f"删除管理员 @{target} 成功")
        context.user_data["action"]=None
        return
    text=update.message.text.strip()
    if text.startswith("设置费率"):
        await set_rate(update,context)
        return
    if text.startswith("设置汇率"):
        await set_exchange(update,context)
        return
    # 交易
    if text.startswith("+") or text.startswith("-"):
        if user not in group_data['admins']:
            await update.message.reply_text("只有管理员可以操作")
            return
        try:
            amount=float(text[1:])
            t_type="in" if text.startswith("+") else "out"
            group_data['transactions'].append({"user":user,"amount":amount,"type":t_type,"time":datetime.utcnow()+timedelta(hours=8)})
            save_data()
            await update.message.reply_text(format_message(group_data))
        except:
            await update.message.reply_text("格式错误，请输入 +50 或 -30")

# 菜单
async def menu(update:Update,context:ContextTypes.DEFAULT_TYPE):
    keyboard=[
        [InlineKeyboardButton("设置费率",callback_data="rate")],
        [InlineKeyboardButton("设置汇率",callback_data="exchange")],
        [InlineKeyboardButton("添加管理员",callback_data="add_admin")],
        [InlineKeyboardButton("删除管理员",callback_data="del_admin")],
        [InlineKeyboardButton("查看历史账单",callback_data="history")],
        [InlineKeyboardButton("清空历史账单",callback_data="clear_history")]
    ]
    reply_markup=InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("请选择操作:",reply_markup=reply_markup)

# 历史账单日期选择
async def show_history_dates(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    group_data=get_group_data(chat_id)
    seen_dates=set()
    date_buttons=[]
    for record in group_data['history']:
        record_date=record['date'].strftime("%Y-%m-%d")
        if datetime.utcnow()+timedelta(hours=8)-record['date']<=timedelta(days=30):
            if record_date not in seen_dates:
                date_buttons.append([InlineKeyboardButton(record_date,callback_data=f"history_date|{record_date}")])
                seen_dates.add(record_date)
    if date_buttons:
        reply_markup=InlineKeyboardMarkup(date_buttons)
        await update.message.reply_text("请选择日期查看账单：",reply_markup=reply_markup)
    else:
        await update.message.reply_text("最近30天无历史账单")

# 按钮回调
async def button(update:Update,context:ContextTypes.DEFAULT_TYPE):
    query=update.callback_query
    chat_id=query.message.chat.id
    group_data=get_group_data(chat_id)
    user=query.from_user.username
    await query.answer()
    if query.data=="rate":
        await query.message.reply_text("请输入: 设置费率5%")
    elif query.data=="exchange":
        await query.message.reply_text("请输入: 设置汇率6.5")
    elif query.data=="add_admin":
        if user not in group_data['admins']:
            await query.message.reply_text("只有管理员可以添加管理员")
            return
        await query.message.reply_text("请输入要添加的管理员用户名，例如: @username")
        context.user_data["action"]="add_admin"
    elif query.data=="del_admin":
        if user not in group_data['admins']:
            await query.message.reply_text("只有管理员可以删除管理员")
            return
        await query.message.reply_text("请输入要删除的管理员用户名，例如: @username")
        context.user_data["action"]="del_admin"
    elif query.data=="history":
        await show_history_dates(query,context)
    elif query.data.startswith("history_date|"):
        selected_date=query.data.split("|")[1]
        lines=[]
        for record in group_data['history']:
            if record['date'].strftime("%Y-%m-%d")==selected_date:
                lines.append(f"上课时间:{record['date'].strftime('%H:%M:%S')}")
                for t in record['transactions']:
                    time_str=t['time'].strftime("%H:%M:%S")
                    if t['type']=='in':
                        rate=group_data['rate']
                        ex=group_data['exchange']
                        val=t['amount']*(1-rate/100)/ex if ex>0 else 0
                        lines.append(f" {time_str} {t['amount']} *{1-rate/100}/ {ex}={val:.2f} by @{t['user']}")
                    else:
                        lines.append(f" {time_str} {t['amount']} by @{t['user']}")
                lines.append(f"下课时间:{(record['date']+timedelta(seconds=1)).strftime('%H:%M:%S')}")
        if lines:
            await query.message.reply_text("\n".join(lines))
        else:
            await query.message.reply_text(f"{selected_date} 无账单记录")
    elif query.data=="clear_history":
        group_data['history']=[]
        save_data()
        await query.message.reply_text("本群历史账单已清空")

# 创建应用
app=ApplicationBuilder().token(TOKEN).build()

# 上课/下课
app.add_handler(MessageHandler(filters.Regex("^上课$"),start_class))
app.add_handler(MessageHandler(filters.Regex("^下课$"),end_class))

# 菜单
app.add_handler(CommandHandler("menu",menu))
app.add_handler(MessageHandler(filters.Regex("^菜单$"),menu))
app.add_handler(CallbackQueryHandler(button))

# 入账/下发/管理员
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_message))

# 启动 webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL+TOKEN
)
