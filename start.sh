#!/bin/bash
set -euo pipefail

# ========================
# 日本节点配置
# ========================
PROXY_NAME="🇯🇵专线VIP1|1x 日本2|ChatGPT"
PROXY_SERVER="jp2.pptv-tv.store"
PROXY_PORT=17722
PROXY_PASSWORD="f6df64bb-9717-4030-8387-0bd5ee1199a4"
PROXY_SNI="data.52daishu.life"
LOCAL_SOCKS_PORT=1080

# ========================
# trojan-go 二进制路径
# ========================
TROJAN_BIN="./trojan-go"
GITHUB_RAW_URL="https://github.com/Jhwyz/jhjizhang/raw/main/trojan-go-linux-amd64/trojan-go"  # 已解压的可执行文件

# ========================
# 下载 trojan-go（如果不存在）
# ========================
if [ ! -x "$TROJAN_BIN" ]; then
    echo "未检测到 trojan-go，开始从 GitHub 下载..."
    curl -L -o "$TROJAN_BIN" "$GITHUB_RAW_URL"
    chmod +x "$TROJAN_BIN"
    echo "✅ trojan-go 下载完成并赋予执行权限（已解压）"
fi

# ========================
# 动态生成 trojan-go 配置文件
# ========================
cat > trojan-go-config.json <<EOF
{
  "run_type": "client",
  "local_addr": "127.0.0.1",
  "local_port": $LOCAL_SOCKS_PORT,
  "remote_addr": "$PROXY_SERVER",
  "remote_port": $PROXY_PORT,
  "password": ["$PROXY_PASSWORD"],
  "ssl": {
    "verify": false,
    "sni": "$PROXY_SNI"
  },
  "udp": true,
  "transport": {"type":"tcp"}
}
EOF

echo "✅ trojan-go 配置文件已生成"

# ========================
# 启动 trojan-go
# ========================
echo "启动 trojan-go 代理..."
$TROJAN_BIN -config ./trojan-go-config.json &
TROJAN_PID=$!

# ========================
# 检测本地 SOCKS5 是否可用
# ========================
ready=0
for i in $(seq 1 15); do
    if (echo > /dev/tcp/127.0.0.1/$LOCAL_SOCKS_PORT) >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done

if [ "$ready" -eq 1 ]; then
    echo "✅ 代理就绪：127.0.0.1:$LOCAL_SOCKS_PORT"
    echo "代理节点信息：$PROXY_NAME - $PROXY_SERVER:$PROXY_PORT"
else
    echo "⚠️ 代理未就绪，Bot 将尝试直连"
    echo "代理节点信息：$PROXY_NAME - $PROXY_SERVER:$PROXY_PORT（未连接）"
fi

# ========================
# 安装 Python 依赖
# ========================
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ========================
# 启动 Bot
# ========================
echo "启动 bot.py ..."
exec python bot.py
