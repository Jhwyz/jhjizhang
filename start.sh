#!/bin/bash
set -euo pipefail

# === 启动 trojan-go（如果存在） ===
if [ -x ./trojan-go ]; then
    echo "启动 trojan-go..."
    ./trojan-go -config ./trojan-go-config.json &
fi

# === 创建虚拟环境（如果还没创建） ===
python3 -m venv .venv
source .venv/bin/activate

# === 升级 pip 并安装依赖 ===
pip install --upgrade pip
pip install -r requirements.txt

# === 启动 bot ===
echo "启动 bot.py ..."
python bot.py
