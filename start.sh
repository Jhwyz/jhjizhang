#!/usr/bin/env bash
echo "🚀 启动检查中..."

# 检查 Chrome 是否安装
if command -v google-chrome > /dev/null 2>&1; then
  CHROME_VERSION=$(google-chrome --version)
  echo "✅ 检测到 Chrome: $CHROME_VERSION"
else
  echo "❌ 未检测到 Chrome，请检查 Dockerfile 安装部分。"
  exit 1
fi

# 检查 ChromeDriver 是否安装
if command -v chromedriver > /dev/null 2>&1; then
  DRIVER_VERSION=$(chromedriver --version)
  echo "✅ 检测到 ChromeDriver: $DRIVER_VERSION"
else
  echo "❌ 未检测到 ChromeDriver，请检查 Dockerfile 安装部分。"
  exit 1
fi

# 检查 Python 文件是否存在
if [ ! -f "main.py" ]; then
  echo "❌ main.py 未找到，请确保文件存在于项目根目录。"
  exit 1
fi

# 延迟启动，给 Render 一点时间加载环境
sleep 2

# 启动 Python 应用
echo "🌐 启动天官 OKX 价格机器人..."
python3 main.py
