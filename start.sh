#!/bin/bash
set -e

echo "🚀 启动检查中..."

# 检查 Chrome
if ! command -v google-chrome &> /dev/null; then
    echo "❌ 未检测到 Chrome，请检查 Dockerfile 安装部分。"
    exit 1
fi

echo "✅ Chrome 检测成功: $(google-chrome --version)"
echo "✅ ChromeDriver 检测成功: $(chromedriver --version)"

# 启动 Telegram Bot 主程序
python main.py
