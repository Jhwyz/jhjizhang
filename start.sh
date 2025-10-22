#!/usr/bin/env bash

# 安装 Chrome
apt-get update && apt-get install -y wget unzip gnupg ca-certificates
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list
apt-get update && apt-get install -y google-chrome-stable

# 检查 Chrome
if command -v google-chrome > /dev/null; then
  echo "✅ Chrome 已安装"
else
  echo "❌ Chrome 未安装"
  exit 1
fi

# 启动应用
python3 main.py
