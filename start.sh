#!/bin/bash
set -e

echo "🚀 启动检查中..."

# 检查 Chrome 是否存在
if ! command -v google-chrome > /dev/null; then
    echo "❌ 未检测到 Chrome，请检查 Dockerfile 安装部分。"
    exit 1
else
    echo "✅ Chrome 检测成功：$(google-chrome --version)"
fi

# 检查 ChromeDriver 是否存在
if ! command -v chromedriver > /dev/null; then
    echo "❌ 未检测到 ChromeDriver，请检查安装路径。"
    exit 1
else
    echo "✅ ChromeDriver 检测成功：$(chromedriver --version)"
fi

# 设置环境变量（防止某些服务器上找不到 Chrome）
export CHROME_BIN="/usr/bin/google-chrome"
export CHROME_DRIVER="/usr/local/bin/chromedriver"

echo "🌐 启动天官记账机器人..."
python main.py
