from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 初始化全局变量
bot_enabled = False
admin_username = None
transactions = []  # 保存最近六笔
fee_rate = 0
exchange_rate = 0
total_income = 0
total_expense = 0

# 主消息处理函数
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled, admin_username, transactions, fee_rate, exchange_rate
    global total_income, total_expense

    text = update.message.text

    # 设置管理员
    if text.startswith("设置管理员"):
        admin_username = text.split()[1]
        await update.message.reply_text(f"管理员设置为 @{admin_username}")
        return

    # 机器人启用/禁用
    if text == "上课":
        bot_enabled = True
        await update.message.reply_text("机器人已启用，开始记账！")
        return
    if text == "下课":
        bot_enabled = False
        await update.message.reply_text("机器人已禁用，停止记账！")
        return

    # 如果机器人未启用，忽略消息
    if not bot_enabled:
        return

    # 只允许管理员操作
    if admin_username and update.message.from_user.username != admin_username:
        await update.message.reply_text("你不是管理员，无权限操作！")
        return

    # 记账逻辑
    if text.startswith("+") or text.startswith("-"):
        try:
            amount = float(text)
            transactions.append(amount)
            if len(transactions) > 6:
                transactions.pop(0)

            if amount > 0:
                total_income += amount
            else:
                total_expense += -amount

            # 构建回复
            msg = "jhwlkj 记账机器人\n"
            for t in transactions:
                msg += f"{t}\n"
            msg += f"费率: {fee_rate}%\n"
            msg += f"汇率: {exchange_rate}\n"
            msg += f"总入账: {total_income}\n"
            msg += f"已下发: {total_expense}\n"
            msg += f"未下发: {total_income - total_expense}\n"

            await update.message.reply_text(msg)
        except ValueError:
            await update.message.reply_text("请输入正确的数字，例如 +50 或 -20")
        return

    # 菜单
    if text == "菜单":
        keyboard = [
            [InlineKeyboardButton("费率设置", callback_data="set_fee")],
            [InlineKeyboardButton("汇率设置", callback_data="set_exchange")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("请选择菜单项：", reply_markup=reply_markup)
        return

# 回调处理（菜单按钮）
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "set_fee":
        await query.edit_message_text("请输入费率，例如 5%")
    elif query.data == "set_exchange":
        await query.edit_message_text("请输入汇率，例如 6.8")

# 启动机器人
if __name__ == "__main__":
    application = ApplicationBuilder().token("7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c").build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.MESSAGE, handle_message))
    application.run_polling()
