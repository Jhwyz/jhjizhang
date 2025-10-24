#!/bin/bash
set -euo pipefail

cd /app || exit 1

# === 可选：如果你有 trojan-go 二进制并希望自动启动 ===
if [ -x /usr/local/bin/trojan-go ]; then
    echo "启动 trojan-go..."
    /usr/local/bin/trojan-go -config /app/trojan-go-config.json &
    TROJAN_PID=$!
    # 等待本地 socks5 端口就绪
    for i in $(seq 1 10); do
        if (echo > /dev/tcp/127.0.0.1/1080) >/dev/null 2>&1; then
            echo "socks5 就绪"
            break
        fi
        sleep 1
    done
else
    echo "未检测到 trojan-go，继续启动 Bot（请求将不经过代理）"
fi

# === 创建虚拟环境 ===
python3 -m venv .venv
source .venv/bin/activate

# === 升级 pip & 安装依赖 ===
pip install --upgrade pip
pip install -r requirements.txt

# === 启动 Bot ===
echo "启动 bot.py ..."
exec python bot.py
