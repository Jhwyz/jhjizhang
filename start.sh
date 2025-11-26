#!/bin/bash
set -euo pipefail

# ========================
# 日本节点配置
# ========================
PROXY_NAME="🇸🇬专线VIP1|1x 新加坡1"
PROXY_SERVER="mf2c0plk8d.14y.top"
PROXY_PORT=17722
PROXY_PASSWORD="7fd81dac-48fc-47b8-a230-170174ac6a8d"
PROXY_SNI="data.52daishu.life"
LOCAL_SOCKS_PORT=1080

# ========================
# trojan-go 二进制路径
# ========================
TROJAN_BIN="./trojan-go"
GITHUB_RAW_URL="https://github.com/Jhwyz/jhjizhang/raw/main/trojan-go-linux-amd64/trojan-go"  # 已解压的可执行文件

# ========================
# Render 环境变量 (如果需要)
# ========================
# 如果你希望通过环境变量配置代理，可以通过 Render 配置这些
# 这里假设你在 Render 控制台设置了环境变量，或可以直接在命令行中修改

# 获取 Render 环境中的端口设置（如果有）
RENDER_PORT=${PORT:-1080}

# ========================
# 检查 Trojan-Go 是否已经运行
# ========================
if pgrep -f "$TROJAN_BIN" > /dev/null; then
    echo "Trojan-Go 已经在运行，跳过启动..."
else
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
      "local_port": $RENDER_PORT,
      "remote_addr": "$PROXY_SERVER",
      "remote_port": $PROXY_PORT,
      "password": ["$PROXY_PASSWORD"],
      "ssl": {
        "verify": true,
        "sni": "$PROXY_SNI"
      },
      "udp": true,
      "transport": {"type":"tcp"}
    }
    EOF

    echo "✅ trojan-go 配置文件已生成"

    # ========================
    # 启动 trojan-go (确保在前台运行)
    # ========================
    echo "启动 trojan-go 代理..."
    $TROJAN_BIN -config ./trojan-go-config.json -verbose >> trojan-go.log 2>&1
    echo "✅ Trojan-Go 启动成功"
fi

# ========================
# 检测本地 SOCKS5 是否可用
# ========================
ready=0
for i in $(seq 1 30); do
    if (echo > /dev/tcp/127.0.0.1/$RENDER_PORT) >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 2  # 延长等待时间
done

if [ "$ready" -eq 1 ]; then
    echo "✅ 代理就绪：127.0.0.1:$RENDER_PORT"
    echo "代理节点信息：$PROXY_NAME - $PROXY_SERVER:$PROXY_PORT"
else
    echo "⚠️ 代理未就绪，Bot 将尝试直连"
    echo "代理节点信息：$PROXY_NAME - $PROXY_SERVER:$PROXY_PORT（未连接）"
fi

# ========================
# 安装 Python 依赖
# ========================
if [ ! -d ".venv" ]; then
    echo "未检测到虚拟环境，创建新的虚拟环境..."
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip

# 检查 requirements.txt 是否存在
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 文件不存在，请检查！"
    exit 1
fi
pip install -r requirements.txt

# ========================
# 启动 Bot
# ========================
echo "启动 bot.py ..."
exec python bot.py >> bot.log 2>&1
