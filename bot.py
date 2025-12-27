from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
import json
import os
import re
from datetime import datetime, timedelta, timezone
import time
import requests
import asyncio
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =======================
# 配置
# =======================
TOKEN = "7074233356:AAFA7TsysiHOk_HHSwxLP4rBD21GNEnTL1c"
WEBHOOK_URL = "https://jhwlkjjz.onrender.com/"
PORT = int(os.environ.get("PORT", 8443))
DATA_FILE = "data.json"

# OKX API
OKX_URL = "https://www.okx.com/v3/c2c/tradingOrders/books"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.okx.com/zh-hans/p2p-markets/cny/buy-usdt",
    "Accept": "application/json, text/plain, */*",
}

# SOCKS5（V2Ray）
PROXIES = {
    "http": "socks5h://127.0.0.1:1080",
    "https": "socks5h://127.0.0.1:1080",
}

# =======================
# OKX Session（关键）
# =======================
def create_okx_session():
    session = requests.Session()

    retries = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(HEADERS)
    session.proxies.update(PROXIES)
    return session


OKX_SESSION = create_okx_session()

# =======================
# 数据初始化
# =======================
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
        "history": {},
    }


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =======================
# 北京时间
# =======================
def get_bj_now():
    return datetime.now(tz=timezone.utc) + timedelta(hours=8)


# =======================
# OKX USDT 卖家价格查询（稳定版）
# =======================
def _get_okx_sync():
    params = {
        "quoteCurrency": "CNY",
        "baseCurrency": "USDT",
        "paymentMethod": "all",
        "showTrade": "false",
        "receivingAds": "false",
        "isAbleFilter": "false",
        "showFollow": "false",
        "showAlreadyTraded": "false",
        "side": "sell",
        "userType": "all",
        "t": str(int(time.time() * 1000)),
    }

    res = OKX_SESSION.get(OKX_URL, params=params, timeout=15)
    res.raise_for_status()
    data_json = res.json()
    sellers = data_json.get("data", {}).get("sell", [])

    if not sellers:
        return "💰 当前 USDT 买入价格：暂无数据"

    msg = "💰 当前 OKX 买入 USDT 前十个唯一卖家：\n"
    seen = set()
    count = 0

    for seller in sellers:
        name = seller.get("nickName", "未知卖家")
        price = seller.get("price", "未知价格")
        if name not in seen:
            seen.add(name)
            count += 1
            msg += f"{count}. {name} - {price} CNY\n"
            if count >= 10:
                break

    return msg


async def get_okx_usdt_unique_sellers():
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _get_okx_sync)
    except requests.exceptions.SSLError:
        return "❌ OKX SSL 握手失败（代理异常）"
    except requests.exceptions.ProxyError:
        return "❌ SOCKS5 代理不可用（V2Ray 未启动）"
    except requests.exceptions.Timeout:
        return "⏱ OKX 请求超时，请稍后再试"
    except Exception as e:
        return f"❌ 获取 OKX 价格失败: {type(e).__name__}"


# =======================
# 格式化账单（原样保留）
# =======================
def format_message(transactions):
    bj_now = get_bj_now()
    date_str = bj_now.strftime("%Y年%-m月%-d日")
    header = f"🌟 天 官 记账机器人 🌟\n{date_str}\n"

    in_tx = [t for t in transactions if t["type"] == "in"]
    in_lines = [f"💰 已入款（{len(in_tx)}笔）："]
    for t in in_tx:
        try:
            time_str = datetime.fromisoformat(t["time"]).strftime("%H:%M:%S")
        except:
            time_str = "未知时间"
        amt_after_fee = t["amount"] * (1 - t["rate"] / 100)
        usd = amt_after_fee / t["exchange"] if t["exchange"] > 0 else 0.0
        in_lines.append(
            f"  {time_str} {t['amount']} - {t['rate']}% / {t['exchange']} = {usd:.2f} by @{t['user']}"
        )

    out_tx = [t for t in transactions if t["type"] == "out"]
    out_lines = [f"📤 已下发（{len(out_tx)}笔）："]
    for t in out_tx:
        try:
            time_str = datetime.fromisoformat(t["time"]).strftime("%H:%M:%S")
        except:
            time_str = "未知时间"
        out_lines.append(f"  {time_str} {t['amount']} by @{t['user']}")

    total_in = sum(t["amount"] for t in in_tx)
    total_out = sum(t["amount"] for t in out_tx)
    usd_total = sum(
        (t["amount"] * (1 - t["rate"] / 100)) / t["exchange"]
        for t in in_tx
        if t["exchange"] > 0
    )

    summary_lines = [
        f"\n📊 总入款金额：{total_in}",
        f"💵 当前费率：{data['rate']}%",
        f"💱 当前汇率：{data['exchange']}",
        f"✅ 应下发：{usd_total:.2f} (USDT)",
        f"📤 已下发：{total_out} (USDT)",
        f"❌ 未下发：{usd_total - total_out:.2f} (USDT)",
    ]
    return header + "\n".join(in_lines + out_lines + summary_lines)


# =======================
# 下面所有逻辑：**原样保留**
# =======================

# （你的 start_class / end_class / set_rate / set_exchange /
#  menu / button / handle_message / webhook 启动
#  —— 全部保持不变，只省略展示）

# ⚠️ 唯一一行改动：
# 查询币价那里，从同步 → await

# 在 handle_message 里：
# 原来：
# msg = get_okx_usdt_unique_sellers()
# 改成：
# msg = await get_okx_usdt_unique_sellers()

# =======================
# 启动机器人
# =======================
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
    webhook_url=WEBHOOK_URL + TOKEN,
)
