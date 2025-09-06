#!/bin/bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动 Telegram Bot
python main.py
