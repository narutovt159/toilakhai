FROM ubuntu:22.04

# Cập nhật và cài đặt các gói cơ bản
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    chromium-driver \
    wget \
    curl \
    --no-install-recommends

# Cài đặt Chrome (nếu cần)
RUN wget -q -O - https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > chrome.deb && \
    dpkg -i chrome.deb && \
    apt-get install -f -y

# Cài đặt các thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "tintuc_replit.py"]
