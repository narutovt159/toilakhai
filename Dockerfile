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
    procps \
    && rm -rf /var/lib/apt/lists/*

# Thêm kho Google vào hệ thống để cài đặt Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
RUN DISTRO=$(lsb_release -c | awk '{print $2}') && echo "deb [arch=amd64] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Cài đặt Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable
RUN pip install --upgrade pip
# Cài đặt các thư viện Python cần thiết từ file requirements.txt
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt Selenium và WebDriver Manager
RUN pip install selenium webdriver-manager

# Đặt quyền cho thư mục làm việc
RUN chown -R root:root /app
RUN chmod -R 755 /app

# Copy mã nguồn Python của bạn vào container
COPY . /app

# Chạy script Python của bạn
# ... (Giữ nguyên phần trên của Dockerfile từ tintuc_replit.py)

# Chạy nhiều file Python song song
CMD python3 bitcoin_news.py
