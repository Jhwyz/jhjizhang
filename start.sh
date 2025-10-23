#!/bin/bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 更新 pip 并安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 启动机器人
python bot.py
