from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Bot Token
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"

# 账目列表，每条记录是 (金额, 描述)
records = []

# 处理消息
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() == "show":
        if not records:
            await update.message.reply_text("暂无账目记录")
            return
        message = ""
        total = 0
        for amt, desc in records:
            message += f"{amt:+} - {desc}\n"
            total += amt
        message += f"\n总余额：{total:+}"
        await update.message.reply_text(message)
        return
    if text.lower() == "clear":
        records.clear()
        await update.message.reply_text("账目已清空")
        return
    if text.startswith(("+", "-")):
        parts = text.split(maxsplit=1)
        try:
            amount = float(parts[0])
        except ValueError:
            await update.message.reply_text("金额格式错误，请发送 +50 午餐 或 -20 工资")
            return
        description = parts[1] if len(parts) > 1 else ""
        records.append((amount, description))
        await update.message.reply_text(f"已添加：{amount:+} - {description}")
        return
    await update.message.reply_text("无法识别的格式，请发送 +50 午餐 或 -20 工资，或发送 show 查看账目，clear 清空账目")

# 创建 Bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    app.run_polling()
