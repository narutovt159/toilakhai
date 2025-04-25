# Sử dụng image Python chính thức làm base image
FROM python:3.9-slim


# Nâng cấp pip
RUN pip install --upgrade pip

# Cài đặt các thư viện Python từ requirements.txt
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt Selenium và WebDriver Manager
RUN pip install selenium webdriver-manager

# Copy mã nguồn Python vào container
COPY . /app

# Chạy file Python
CMD ["python3", "tintuc_test.py"]
