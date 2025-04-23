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
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Chromium thay vì Google Chrome (để tránh lỗi với chrome binary)
RUN apt-get install -y chromium

# Kiểm tra và xuất ra đường dẫn của chromium binary
RUN echo "Chromium binary location:" && which chromium

# Cài đặt ChromeDriver tương thích với Chromium version
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

# Chạy script Python của bạn

CMD ["python3", "tintuc_replit.py"]
