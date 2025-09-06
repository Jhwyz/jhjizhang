from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import re

# -------------------
# 配置
# -------------------
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
ADMIN_USERNAMES = ["你的用户名"]  # 只有这些用户名可以操作

# -------------------
# 全局数据存储
# -------------------
bot_data = {
    "enabled": False,         # 是否启用机器人（上课/下课）
    "transactions": [],       # 最近6笔流水
    "total_in": 0,            # 总入账
    "total_out": 0,           # 已下发
    "rate": 0,                # 费率
    "exchange": 0             # 汇率
}

# -------------------
# 权限检查
# -------------------
def is_admin(update: Update):
    username = update.effective_user.username
    return username in ADMIN_USERNAMES

# -------------------
# 构建状态文本
# -------------------
def build_status_text():
    text = "jhwlkj 记账机器人\n"
    for t in bot_data['transactions']:
        text += t + "\n"
    text += "\n" * (6 - len(bot_data['transactions']))  # 补足6行
    text += f"费率为：{bot_data['rate']}%\n"
    text += f"汇率为：{bot_data['exchange']}\n"
    text += f"总入账：{bot_data['total_in']}\n"
    text += f"已下发：{bot_data['total_out']}\n"
    text += f"未下发：{bot_data['total_in'] - bot_data['total_out']}\n"
    return text

# -------------------
# 消息处理
# -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()

    # 上课/下课控制
    if msg == "上课":
        if not is_admin(update):
            await update.message.reply_text("你没有权限操作机器人")
            return
        bot_data['enabled'] = True
        await update.message.reply_text("机器人已启用")
        return
    elif msg == "下课":
        if not is_admin(update):
            await update.message.reply_text("你没有权限操作机器人")
            return
        bot_data['enabled'] = False
        await update.message.reply_text("机器人已关闭")
        return

    # 如果未启用，忽略
    if not bot_data['enabled']:
        return

    # 权限检查
    if not is_admin(update):
        await update.message.reply_text("你没有权限操作机器人")
        return

    # 处理费率设置
    match_rate = re.match(r"费率(\d+)%", msg)
    if match_rate:
        bot_data['rate'] = int(match_rate.group(1))
        await update.message.reply_text(f"设置费率 {bot_data['rate']}% 成功\n\n" + build_status_text())
        return

    # 处理汇率设置
    match_exchange = re.match(r"汇率(\d+)", msg)
    if match_exchange:
        bot_data['exchange'] = int(match_exchange.group(1))
        await update.message.reply_text(f"设置汇率 {bot_data['exchange']} 成功\n\n" + build_status_text())
        return

    # 处理 + 或 - 记账
    if msg.startswith("+") or msg.startswith("-"):
        try:
            amount = float(msg[1:])
        except ValueError:
            await update.message.reply_text("请输入有效数字，例如 +50 或 -20")
            return

        # 保存前六笔流水
        transactions = bot_data['transactions']
        transactions.insert(0, msg)
        bot_data['transactions'] = transactions[:6]

        # 更新总入账/已下发
        if msg.startswith("+"):
            bot_data['total_in'] += amount
        else:
            bot_data['total_out'] += amount

        # 自动显示最新状态
        await update.message.reply_text(build_status_text())
        return

# -------------------
# 命令处理
# -------------------
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("菜单:\n费率设置\n汇率设置")

# -------------------
# 启动应用
# -------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # 文本消息处理
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # /menu 命令
    app.add_handler(CommandHandler("menu", menu))

    # 启动轮询
    app.run_polling()
