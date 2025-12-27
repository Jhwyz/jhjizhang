#!/bin/bash
set -euo pipefail

# ========================
# 配置：代理节点信息
# ========================
PROXY_NAME="🇯🇵专线VIP1|1x 日本2|ChatGPT"
PROXY_SERVER="203.227.187.106"
PROXY_PORT=1080
PROXY_PASSWORD="666666"
PROXY_SNI=""
LOCAL_SOCKS_PORT=${PORT:-1080}

# ========================
# Trojan-Go 下载地址
# ========================
TROJAN_BIN="./trojan-go-linux-amd64/trojan-go"
GITHUB_TROJAN_URL="https://github.com/Jhwyz/jhjizhang/raw/main/trojan-go-linux-amd64/trojan-go"

# ========================
# 下载并赋予 Trojan-Go 执行权限
# ========================
if [ ! -x "$TROJAN_BIN" ]; then
    echo "🚨 未找到 Trojan-Go 文件，正在从 GitHub 下载..."
    mkdir -p ./trojan-go-linux-amd64

    # 下载 Trojan-Go 文件
    curl -L -o "$TROJAN_BIN" "$GITHUB_TROJAN_URL"
    chmod +x "$TROJAN_BIN"
    echo "✅ Trojan-Go 下载并赋予执行权限成功"
fi

# ========================
# 生成 Trojan-Go 配置文件
# ========================
echo "生成 Trojan-Go 配置文件..."

cat > trojan-go-config.json <<EOF
{
  "run_type": "client",
  "local_addr": "0.0.0.0",
  "local_port": $LOCAL_SOCKS_PORT,
  "remote_addr": "$PROXY_SERVER",
  "remote_port": $PROXY_PORT,
  "password": ["$PROXY_PASSWORD"],
  "ssl": {
    "verify": false,
    "sni": "$PROXY_SNI"
  },
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


# ========================
# 检查代理服务器连接
# ========================
echo "🔍 检查代理服务器 $PROXY_SERVER:$PROXY_PORT 是否可达..."

if ! curl -s --head "https://$PROXY_SERVER:$PROXY_PORT" | head -n 1 | grep -q "HTTP/"; then
    echo "⚠️ 无法连接到代理服务器：$PROXY_SERVER:$PROXY_PORT"
    exit 1
else
    echo "✅ 代理服务器连接正常"
fi

# ========================
# SSL 配置检查
# ========================
echo "🔍 正在检查代理的 SSL 配置..."

SSL_TEST=$(openssl s_client -connect $PROXY_SERVER:$PROXY_PORT -servername $PROXY_SNI </dev/null 2>&1)

if echo "$SSL_TEST" | grep -q "SSL handshake"; then
    echo "✅ SSL 配置正确"
else
    echo "⚠️ SSL 配置或 SNI 错误："
    echo "$SSL_TEST"
    exit 1
fi

# ========================
# 启动 Trojan-Go（前台运行）
# ========================
echo "🚀 启动 Trojan-Go 代理..."

$TROJAN_BIN -config ./trojan-go-config.json -verbose > trojan-go.log 2>&1 &
TG_PID=$!

sleep 3  # 等待 Trojan-Go 启动

# ========================
# 检测代理端口是否已启动
# ========================
echo "🔍 检测代理是否已就绪..."

ready=0
for i in {1..20}; do
    if (echo > /dev/tcp/127.0.0.1/$LOCAL_SOCKS_PORT) >/dev/null 2>&1; then
        ready=1
        break
    fi
    echo "等待代理启动中... ($i/20)"
    sleep 1
done

if [ "$ready" -eq 1 ]; then
    echo "✅ 代理已就绪: 127.0.0.1:$LOCAL_SOCKS_PORT"
else
    echo "⚠️ 代理启动失败，无法连接代理节点。"
    # 增加调试信息，检查是否能连接代理服务器
    echo "尝试连接到代理服务器..."
    curl -v https://$PROXY_SERVER:$PROXY_PORT || echo "无法连接代理服务器"
    echo "检查 Trojan-Go 日志文件..."
    tail -n 20 trojan-go.log
    exit 1
fi

# ========================
# Python 虚拟环境
# ========================
if [ ! -d ".venv" ]; then
    echo "🔧 创建 Python 虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip

# ========================
# 安装 Python 依赖
# ========================
if [ ! -f "requirements.txt" ]; then
    echo "❌ 缺少 requirements.txt 文件"
    exit 1
fi

echo "安装 Python 依赖..."
pip install -r requirements.txt

# ========================
# 启动 bot.py
# ========================
echo "🚀 启动 Bot..."
exec python bot.py
