# 使用官方 Python 基础镜像
FROM python:3.11-slim

# 让 Python 输出不缓存
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（包含 Chrome 与驱动）
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Google Chrome（稳定版）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装 ChromeDriver（自动匹配 Chrome 版本）
RUN CHROME_VERSION=$(google-chrome --version | grep -oE "[0-9]+.[0-9]+.[0-9]+") && \
    DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE") && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（Render 要求）
EXPOSE 8443

# 启动脚本
RUN chmod +x /app/start.sh
CMD ["bash", "/app/start.sh"]

