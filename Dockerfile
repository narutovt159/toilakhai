FROM ubuntu:22.04

# Cài đặt các gói cơ bản và thư viện cần thiết cho Chrome
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
    chromium-driver \
    --no-install-recommends

# Cài đặt Google Chrome
RUN wget -q -O - https://dl.google.com/linux/direct/google-chrome-stable_113.0.5672.92-1_amd64.deb > chrome.deb && \
    dpkg -i chrome.deb && \
    apt-get install -f -y


# Cài đặt các thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .
CMD ["python3", "tintuc_replit.py"]
