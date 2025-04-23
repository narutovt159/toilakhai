FROM ubuntu:22.04

# Cài đặt các thư viện cần thiết cho Chromium và ChromeDriver
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

# Cài đặt Playwright hoặc Selenium và các thư viện Python
RUN pip install playwright
RUN playwright install

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "tintuc_replit.py"]
