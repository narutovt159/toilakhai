FROM ubuntu:22.04

# Cài đặt các gói cơ bản và thư viện cần thiết cho Chromium và ChromeDriver
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libvulkan1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    chromium-browser \
    --no-install-recommends

# Cài đặt Selenium và WebDriver Manager
RUN pip install selenium webdriver-manager

# Sao chép và cài đặt các thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Cài đặt các ứng dụng khác nếu có
COPY . .

CMD ["python3", "tintuc_replit.py"]
