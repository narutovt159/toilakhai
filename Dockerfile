# Chọn image python chính thức làm base image
FROM python:3.9-slim

# Cài đặt các phụ thuộc cần thiết
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

# Cài đặt Chrome và ChromeDriver
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb || apt-get install -f -y
RUN wget -N https://chromedriver.storage.googleapis.com/112.0.5615.49/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip && mv chromedriver /usr/local/bin/chromedriver

# Cài đặt các thư viện Python cần thiết
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt Selenium
RUN pip install selenium

# Cài đặt ChromeDriverManager (Nếu bạn không muốn dùng ChromeDriver tĩnh)
RUN pip install webdriver-manager

# Chạy một script Python (chạy file script Python của bạn ở đây)
COPY . /app
CMD ["python3", "tintuc_replit.py"]
