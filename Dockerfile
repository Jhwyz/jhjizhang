# 使用官方 Python 3.13 slim 镜像
FROM python:3.13-slim

# 安装基础依赖（注意：这里没有 root 限制问题）
RUN apt-get update && apt-get install -y wget gnupg unzip fonts-liberation libnss3 libxss1 libappindicator3-1 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 xdg-utils --no-install-recommends

# 安装 Google Chrome（使用官方独立包）
RUN wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome.deb \
    && rm google-chrome.deb

# 安装 ChromeDriver（自动匹配 Chrome 版本）
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') \
    && echo "安装 ChromeDriver 版本: $CHROME_VERSION" \
    && wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip" || true \
    && unzip -o /tmp/chromedriver.zip -d /usr/local/bin/ || true \
    && chmod +x /usr/local/bin/chromedriver || true \
    && rm -rf /tmp/chromedriver.zip

# 设置工作目录
WORKDIR /app
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 给启动脚本执行权限
RUN chmod +x start.sh

# 运行程序
CMD ["bash", "start.sh"]
