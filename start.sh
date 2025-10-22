#!/bin/bash

# 检查 Chrome 是否安装成功
if ! command -v google-chrome &> /dev/null
then
    echo "❌ Chrome 未安装"
    exit 1
fi

# 可选：输出版本信息
google-chrome --version
chromedriver --version

# 启动 Python 应用（改成你的启动命令）
python main.py
