# 使用 Python 3.10 基础镜像
FROM python:3.10-slim

WORKDIR /app
COPY . .

# ---------- 安装系统依赖 ----------
RUN apt-get update && apt-get install -y wget gnupg unzip curl fonts-liberation libnss3 libxss1 libappindicator3-1 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 xdg-utils

# ---------- 添加 Google Chrome 官方源 ----------
RUN mkdir -p /etc/apt/keyrings \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-linux-signing-key.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# ---------- 安装 Chrome ----------
RUN apt-get update && apt-get install -y google-chrome-stable

# ---------- 安装 ChromeDriver ----------
RUN CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9.]+' | cut -d. -f1) \
    && DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver-linux64 chromedriver-linux64.zip

# ---------- 安装 Python 依赖 ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 运行 start.sh ----------
RUN chmod +x /app/start.sh
CMD ["bash", "/app/start.sh"]
