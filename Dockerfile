FROM python:3.10-slim

# Cài đặt các gói cơ bản và Playwright
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    wget \
    curl \
    --no-install-recommends

# Cài đặt Playwright và các trình duyệt
RUN pip install playwright && playwright install

# Cài đặt các thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python3", "tintuc_replit.py"]
