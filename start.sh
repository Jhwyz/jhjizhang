#!/bin/bash
set -euo pipefail

# ========================
# 配置：VMess 节点信息
# ========================
LOCAL_SOCKS_PORT=1080

# VMess 节点（根据你的链接解码后的信息）
VMESS_ADDRESS="lb1.encuncunba.xyz"
VMESS_PORT=443
VMESS_ID="555340ab-5ec5-4d93-8032-39fd12d5dbb5"
VMESS_PATH="/555340ab-5ec5-4d93-8032-39fd12d5dbb5"
VMESS_ALTERID=0
VMESS_SECURITY="auto"

V2RAY_DIR="./v2ray"
V2RAY_BIN="$V2RAY_DIR/v2ray"

# ========================
# 下载 V2Ray（如果不存在）
# ========================
if [ ! -x "$V2RAY_BIN" ]; then
    echo "🚨 下载 V2Ray..."
    mkdir -p "$V2RAY_DIR"
    curl -L -o "$V2RAY_DIR/v2ray-linux-64.zip" "https://github.com/v2fly/v2ray-core/releases/download/v5.42.0/v2ray-linux-64.zip"
    unzip "$V2RAY_DIR/v2ray-linux-64.zip" -d "$V2RAY_DIR"
    chmod +x "$V2RAY_BIN"
fi

# ========================
# 生成 V2Ray 配置
# ========================
CONFIG_FILE="$V2RAY_DIR/v2ray-config.json"

cat > "$CONFIG_FILE" <<EOF
{
  "inbounds": [
    {
      "port": $LOCAL_SOCKS_PORT,
      "listen": "127.0.0.1",
      "protocol": "socks",
      "settings": { "auth": "noauth" }
    }
  ],
  "outbounds": [
    {
      "protocol": "vmess",
      "settings": {
        "vnext": [
          {
            "address": "$VMESS_ADDRESS",
            "port": $VMESS_PORT,
            "users": [
              {
                "id": "$VMESS_ID",
                "alterId": $VMESS_ALTERID,
                "security": "$VMESS_SECURITY"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "tlsSettings": { "allowInsecure": false },
        "wsSettings": {
          "path": "$VMESS_PATH",
          "headers": { "Host": "$VMESS_ADDRESS" }
        }
      }
    }
  ]
}
EOF

# ========================
# 启动 V2Ray
# ========================
echo "🚀 启动 V2Ray..."
"$V2RAY_BIN" run -c "$CONFIG_FILE" > "$V2RAY_DIR/v2ray.log" 2>&1 &

sleep 3

# ========================
# 检查本地 SOCKS5 是否监听
# ========================
if (echo > /dev/tcp/127.0.0.1/$LOCAL_SOCKS_PORT) >/dev/null 2>&1; then
    echo "✅ 本地 SOCKS5 已就绪: 127.0.0.1:$LOCAL_SOCKS_PORT"
else
    echo "❌ V2Ray 启动失败"
    tail -n 50 "$V2RAY_DIR/v2ray.log"
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
# 启动 Telegram Bot
# ========================
exec python bot.py
