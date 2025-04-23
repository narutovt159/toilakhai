FROM ubuntu:22.04

# Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    chromium-driver \
    --no-install-recommends

# Cài đặt thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "tintuc_replit.py"]
