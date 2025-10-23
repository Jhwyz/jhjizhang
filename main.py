from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ⚠️ 直接写 Token（生产环境请保密）
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"

app = FastAPI()

# 创建 Telegram Bot 应用，禁用 polling
application = ApplicationBuilder().token(TOKEN).post_init(lambda app: None).build()

# 示例命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot 已启动!")

application.add_handler(CommandHandler("start", start))

# FastAPI 接收 Telegram Webhook
@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, Bot(TOKEN))
    await application.process_update(update)
    return {"ok": True}

# 健康检查
@app.get("/")
async def health():
    return {"status": "ok"}

