# 选择 Python 3.10.13 官方镜像
FROM python:3.10.13-slim

# 安装浏览器和驱动
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 设置 Selenium 环境变量
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver

# 设置工作目录
WORKDIR /app

# 拷贝项目代码
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 容器启动时执行机器人
CMD ["python3", "main.py"]
