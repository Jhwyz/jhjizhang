#!/usr/bin/env bash
echo "🚀 启动检查中..."

# 检查 Chrome
if command -v google-chrome > /dev/null; then
  echo "✅ Chrome 已安装: $(google-chrome --version)"
else
  echo "❌ Chrome 未安装"
  exit 1
fi

# 检查 ChromeDriver
if command -v chromedriver > /dev/null; then
  echo "✅ ChromeDriver 已安装: $(chromedriver --version)"
else
  echo "❌ ChromeDriver 未安装"
  exit 1
fi

# 启动 Python 应用
python3 main.py
