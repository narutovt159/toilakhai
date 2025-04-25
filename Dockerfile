# Chọn image Python chính thức làm base image
FROM python:3.9-slim

# Cài đặt các thư viện Python cần thiết từ file requirements.txt
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt Selenium và WebDriver Manager
RUN pip install selenium webdriver-manager

# Copy mã nguồn Python của bạn vào container
COPY . /app

# Chạy nhiều file Python song song
CMD python3 main.py
