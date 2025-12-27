#!/bin/bash
set -euo pipefail

# ========================
# 配置：代理节点信息
# ========================
PROXY_SERVER="203.227.187.106"
PROXY_PORT=1080
PROXY_PASSWORD="666666"
LOCAL_SOCKS_PORT=${PORT:-1080}

# ========================
# Trojan-Go 下载地址
# ========================
TROJAN_BIN="./trojan-go-linux-amd64/trojan-go"
GITHUB_TROJAN_URL="https://github.com/Jhwyz/jhjizhang/raw/main/trojan-go-linux-amd64/trojan-go"

# ========================
# 下载 Trojan-Go
# ========================
if [ ! -x "$TROJAN_BIN" ]; then
    echo "🚨 下载 Trojan-Go..."
    mkdir -p ./trojan-go-linux-amd64
    curl -L -o "$TROJAN_BIN" "$GITHUB_TROJAN_URL"
    chmod +x "$TROJAN_BIN"
fi

# ========================
# 生成 Trojan-Go 配置
# ========================
cat > trojan-go-config.json <<EOF
{
  "run_type": "client",
  "local_addr": "0.0.0.0",
  "local_port": $LOCAL_SOCKS_PORT,
  "remote_addr": "$PROXY_SERVER",
  "remote_port": $PROXY_PORT,
  "password": ["$PROXY_PASSWORD"],
  "udp": true,
  "transport": { "type": "tcp" },
  "socks5": {
    "enabled": true,
    "listen": "0.0.0.0",
    "port": $LOCAL_SOCKS_PORT,
    "username": "666666",
    "password": "666666"
  }
}
EOF

echo "🚀 启动 Trojan-Go..."
$TROJAN_BIN -config trojan-go-config.json > trojan-go.log 2>&1 &

sleep 3

# ========================
# 检查本地 SOCKS5 是否监听
# ========================
if (echo > /dev/tcp/127.0.0.1/$LOCAL_SOCKS_PORT) >/dev/null 2>&1; then
    echo "✅ SOCKS5 已就绪: 127.0.0.1:$LOCAL_SOCKS_PORT"
else
    echo "❌ Trojan-Go 启动失败"
    tail -n 50 trojan-go.log
    exit 1
fi

# ========================
# Python 虚拟环境
# ========================
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ========================
# 启动 bot
# ========================
exec python bot.py
