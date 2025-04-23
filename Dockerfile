FROM ubuntu:22.04

# Cài đặt các gói cơ bản
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    chromium-driver \
    --no-install-recommends

# Sao chép và cài đặt các thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "app.py"]
