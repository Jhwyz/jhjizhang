import os
import json
import re
import asyncio
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# === 基础设置 ===
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "data.json"

app = Flask(__name__)

# === 数据存储初始化 ===
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
except:
    data = {"admins": [], "transactions": [], "rate": 0.0, "exchange": 0.0, "running": False}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === 获取 OKX P2P 价格 ===
def get_okx_price():
    try:
        url = "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        prices = [span.get_text(strip=True) for span in soup.select("span") if re.search(r"^\d+\.\d+$", span.get_text(strip=True))]
        if prices:
            return prices[0]
        return "获取失败"
    except Exception as e:
        print("[ERROR] 获取 OKX P2P 失败:", e)
        return "获取失败"

# === 格式化账单 ===
def format_message(transactions):
    bj_now = datetime.utcnow() + timedelta(hours=8)
    date_str = bj_now.strftime("%Y年%-m月%-d日")
    header = f"🌟 天官记账机器人 🌟\n{date_str}\n"

    in_tx = [t for t in transactions if t["type"] == "in"]
    out_tx = [t for t in transactions if t["type"] == "out"]

    total_in = sum(t["amount"] for t in in_tx)
    total_out = sum(t["amount"] for t in out_tx)
    usd_total = sum((t["amount"] * (1 - t["rate"] / 100)) / t["exchange"] for t in in_tx if t["exchange"] > 0)

    lines = [
        f"💰 入款：{len(in_tx)}笔，总计 {total_in}",
        f"📤 下发：{len(out_tx)}笔，总计 {total_out}",
        f"💱 汇率：{data['exchange']}",
        f"💵 费率：{data['rate']}%",
        f"✅ 应下发：{usd_total:.2f} (USDT)",
        f"❌ 未下发：{usd_total - total_out:.2f} (USDT)"
    ]
    return header + "\n".join(lines)

# === Telegram 消息处理 ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user.username or "未知用户"
    text = update.message.text.strip()

    print(f"[INFO] 收到消息: {text} 来自 @{user}")

    if text in ["/price", "价格"]:
        await update.message.reply_text("⏳ 正在获取价格...")
        price = get_okx_price()
        await update.message.reply_text(f"💹 当前 OKX P2P 买入 USDT 价格: {price}")
        return

    if text == "上课":
        if user not in data["admins"]:
            data["admins"].append(user)
        data["running"] = True
        data["transactions"] = []
        save_data()
        await update.message.reply_text(f"✅ 已启动记账，管理员：@{user}")
        return

    if text == "下课":
        data["running"] = False
        save_data()
        await update.message.reply_text("📘 记账结束，数据已保存。")
        return

    if text.startswith("设置费率"):
        match = re.search(r"(\d+(\.\d+)?)", text)
        if match:
            data["rate"] = float(match.group(1))
            save_data()
            await update.message.reply_text(f"✅ 费率已设置为 {data['rate']}%")
        return

    if text.startswith("设置汇率"):
        match = re.search(r"(\d+(\.\d+)?)", text)
        if match:
            data["exchange"] = float(match.group(1))
            save_data()
            await update.message.reply_text(f"✅ 汇率已设置为 {data['exchange']}")
        return

    if text == "账单":
        if data["running"]:
            await update.message.reply_text(format_message(data["transactions"]))
        else:
            await update.message.reply_text("📋 当前没有进行中的账单。")
        return

    if text.startswith("+") or text.startswith("-"):
        try:
            amount = float(text[1:])
            t_type = "in" if text.startswith("+") else "out"
            data["transactions"].append({
                "user": user,
                "amount": amount,
                "type": t_type,
                "time": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                "rate": data["rate"],
                "exchange": data["exchange"]
            })
            save_data()
            await update.message.reply_text(format_message(data["transactions"]))
        except:
            await update.message.reply_text("⚠️ 格式错误，请输入 +50 或 -30")
        return

# === 初始化 Telegram 应用 ===
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)

    async def process():
        if not application.initialized:
            await application.initialize()
        await application.process_update(update)

    asyncio.run(process())
    return "OK", 200

@app.route("/")
def home():
    return "✅ Bot is running!"

# === 启动入口 ===
if __name__ == "__main__":
    print(f"🚀 启动 Telegram Bot，端口：{PORT}")

    async def init_webhook():
        if not application.initialized:
            await application.initialize()
        await application.bot.set_webhook(url=WEBHOOK_URL + TOKEN)

    asyncio.run(init_webhook())
    app.run(host="0.0.0.0", port=PORT)
