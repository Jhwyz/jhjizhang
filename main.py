import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import pandas as pd
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 账单数据存储
data_file = "expenses.xlsx"
if not os.path.exists(data_file):
    df = pd.DataFrame(columns=["date", "amount"])
    df.to_excel(data_file, index=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用记账机器人！\n命令：\n/add <金额> 添加账单\n/list 今日账单\n/total 总金额\n/export 导出账单")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        date = datetime.now().strftime("%Y-%m-%d")
        df = pd.read_excel(data_file)
        df.loc[len(df)] = [date, amount]
        df.to_excel(data_file, index=False)
        await update.message.reply_text(f"添加成功：{amount} 元")
    except (IndexError, ValueError):
        await update.message.reply_text("用法：/add <金额>")

async def list_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = datetime.now().strftime("%Y-%m-%d")
    df = pd.read_excel(data_file)
    today = df[df['date'] == date]
    if today.empty:
        await update.message.reply_text("今天还没有账单")
    else:
        text = "\n".join([f"{row['amount']} 元" for _, row in today.iterrows()])
        await update.message.reply_text(f"今日账单：\n{text}")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = pd.read_excel(data_file)
    total_amount = df['amount'].sum()
    await update.message.reply_text(f"总金额：{total_amount} 元")

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_document(document=open(data_file, "rb"), filename="expenses.xlsx")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_expenses))
app.add_handler(CommandHandler("total", total))
app.add_handler(CommandHandler("export", export))

if __name__ == "__main__":
    app.run_webhook(listen="0.0.0.0", port=int(os.getenv("PORT", 5000)), url_path=BOT_TOKEN, webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/{BOT_TOKEN}")
