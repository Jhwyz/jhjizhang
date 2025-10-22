# 使用官方 Python 3.13 slim 镜像
FROM python:3.13-slim

# 切换到 root 用户安装系统依赖和 Chrome
USER root

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget unzip gnupg ca-certificates fonts-liberation \
    libnss3 libxss1 libappindicator3-1 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 xdg-utils --no-install-recommends

# 安装 Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list' \
    && apt-get update && apt-get install -y google-chrome-stable

# 安装 ChromeDriver（匹配 Chrome 版本）
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') \
    && wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 可选：切换回非 root 用户
# USER render

# 启动命令
CMD ["bash", "start.sh"]

