# Chọn image Python chính thức làm base image
FROM python:3.9-slim

# Cài đặt các dependencies cần thiết cho Chrome và Selenium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libepoxy0 \
    gnupg2 \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Thêm kho Google vào hệ thống để cài đặt Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
RUN DISTRO=$(lsb_release -c | awk '{print $2}') && echo "deb [arch=amd64] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Cài đặt Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# Cài đặt ChromeDriver tương thích với phiên bản Chrome
RUN wget -N https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip && mv chromedriver /usr/local/bin/chromedriver

# Cài đặt các thư viện Python cần thiết từ file requirements.txt
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt Selenium và WebDriver Manager
RUN pip install selenium webdriver-manager

# Copy mã nguồn Python của bạn vào container
COPY . /app

# Cài đặt Chromium (Nếu bạn muốn sử dụng Chromium thay vì Google Chrome)
# RUN apt-get install -y chromium

# Chạy script Python của bạn

CMD ["python3", "tintuc_replit.py"]
