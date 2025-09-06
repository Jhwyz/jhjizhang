#!/bin/bash

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install python-telegram-bot[webhooks]

# 启动机器人
python main.py
