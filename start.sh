#!/bin/bash
set -euo pipefail

# ========================
# 日本代理节点信息
# ========================
PROXY_NAME="🇯🇵专线VIP1|1x 日本2|ChatGPT"
PROXY_SERVER="jp2.pptv-tv.store"
PROXY_PORT=17722
PROXY_PASSWORD="f6df64bb-9717-4030-8387-0bd5ee1199a4"
PROXY_SNI="data.52daishu.life"
LOCAL_SOCKS_PORT=1080

echo "写入 trojan-go 配置文件 trojan-go-config.json ..."
cat > trojan-go-config.json <<EOF
{
  "run_type": "client",
  "local_addr": "127.0.0.1",
  "local_port": $LOCAL_SOCKS_PORT,
  "remote_addr": "$PROXY_SERVER",
  "remote_port": $PROXY_PORT,
  "password": ["$PROXY_PASSWORD"],
  "ssl": {"sni":"$PROXY_SNI","verify":false},
  "udp": true,
  "transport": {"type":"tcp"}
}
EOF

# ========================
# 启动 trojan-go
# ========================
if [ -x /usr/local/bin/trojan-go ]; then
    echo "启动 trojan-go 代理..."
    /usr/local/bin/trojan-go -config ./trojan-go-config.json &
    TROJAN_PID=$!

    # 等待本地 SOCKS5 就绪（最多 15 秒）
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
else
    echo "⚠️ 未检测到 /usr/local/bin/trojan-go，跳过代理启动，Bot 将直接直连"
    echo "代理节点信息：$PROXY_NAME - $PROXY_SERVER:$PROXY_PORT（未连接）"
fi

# ========================
# 创建虚拟环境并安装依赖
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
