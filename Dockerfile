FROM ubuntu:22.04

# Cài đặt các gói cần thiết
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    chromium-driver

# Sao chép và cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
