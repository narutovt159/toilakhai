import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# Telegram Bot Token
TG_BOT_ACCESS_TOKEN = '7231655061:AAEwNdGdNKWDT7LQ4dv52OLYqx7DcNfZmos'  # 🔴 Thay bằng token thật

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

# Lưu message_id của tin nhắn giá coin cuối cùng
last_message_id = {}


# Configure Selenium WebDriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-cache")  # Vô hiệu hóa cache
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


# Hàm lấy giá coin từ crypto.com
def get_coin_data():
    try:
        driver = init_driver()
        driver.get("https://crypto.com/price")

        # Làm mới trang để đảm bảo dữ liệu mới
        driver.refresh()
        time.sleep(2)

        # Chờ trang tải hoàn toàn
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".chakra-text.css-1jj7b1a")))
        except Exception as e:
            logging.error(f"Timeout: Không tìm thấy phần tử tên coin: {e}")
            driver.quit()
            return []

        # Cuộn trang để tải dữ liệu
        for _ in range(3):
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Giảm thời gian chờ để tối ưu

        coin_rows = driver.find_elements(By.TAG_NAME, "tr")
        coins = []
        count = 0

        for row in coin_rows:
            try:
                coin_name = row.find_element(By.CSS_SELECTOR,
                                             ".chakra-text.css-1jj7b1a")
                if coin_name and count < 5:
                    coin_name_text = coin_name.text.strip()

                    if coin_name_text == 'USDT':
                        continue

                    all_text = " ".join([
                        col.text.strip()
                        for col in row.find_elements(By.TAG_NAME, "td")
                        if col.text.strip()
                    ])

                    price_text = "N/A"
                    change_text = "N/A"

                    price_match = re.search(
                        r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?', all_text)
                    if price_match:
                        price_text = price_match.group(0)

                    change_match = re.search(r'[+-]?\d*\.?\d+%', all_text)
                    if change_match:
                        change_text = change_match.group(0)

                    coins.append(
                        f"{coin_name_text} - giá {price_text}, {change_text}")
                    count += 1

            except Exception as e:
                logging.error(f"Lỗi khi xử lý hàng: {e}")
                continue

            if count == 5:
                break

        driver.quit()
        return coins
    except Exception as e:
        logging.error(f"Lỗi khi lấy giá coin: {e}")
        return []


# Hàm gửi giá coin qua Telegram và xóa tin nhắn cũ
async def send_coin_prices(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    coins = get_coin_data()

    # Thêm nút nhấn
    buttons = [[
        InlineKeyboardButton("🙋 Follow master nhận LÌ XÌ",
                             url="https://t.me/onusfuture/70917")
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Chuẩn bị nội dung tin nhắn
    if coins:
        message = "\n".join([f"{i+1}. {coin}" for i, coin in enumerate(coins)])
        caption = f"🔥 *Giá Coin Mới Nhất*\n\n{message}"

        # Xóa tin nhắn cũ nếu tồn tại
        if chat_id in last_message_id and last_message_id[chat_id] is not None:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id, message_id=last_message_id[chat_id])
                # Đợi một chút để đảm bảo tin nhắn cũ được xóa trước khi gửi tin mới
                await asyncio.sleep(0.5)
            except Exception as e:
                logging.warning(f"Không thể xóa tin nhắn cũ: {e}")

        # Gửi tin nhắn mới với ảnh từ file cục bộ
        # Trong phần gửi tin nhắn mới với ảnh từ URL
        try:
            sent_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=
                "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhRcTWgFGruUEAFjrf9QOwd4v9Ks0YzkZ-o2ALerFSSSUJDKhyIF6Uf7qYPNoCTLHLT99CSKgSEvdoA9NtEBw7NhEJQi5dz3UaLEnawoA_Na_dmeNZnjo4WOt48qVIFRdbZeRSzsCnZ4nNbQlDDTY__Y0o1NY3GlniOWkfQzl3kaX0R_d1e5nBVlFpBmC4/s1279/z6528522093337_835d781400610f3264538bd3e4acd00d.jpg",
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup)
            last_message_id[chat_id] = sent_message.message_id
        except Exception as e:
            logging.error(f"Lỗi khi gửi ảnh: {e}")
            sent_message = await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup)
            last_message_id[chat_id] = sent_message.message_id

        except Exception as e:
            logging.error(f"Lỗi khi gửi ảnh: {e}")
            sent_message = await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup)
            last_message_id[chat_id] = sent_message.message_id


# Lệnh /giacoin để kích hoạt gửi giá coin định kỳ
async def giacoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in last_message_id:
        last_message_id[chat_id] = None
    await update.message.reply_text(
        "Bắt đầu lấy giá coin mỗi 30 giây... Nhấn /stop để dừng.",
        parse_mode="Markdown")

    # Chạy định kỳ mỗi 30 giây
    context.job_queue.run_repeating(send_coin_prices,
                                    interval=5,
                                    first=5,
                                    chat_id=chat_id)


# Lệnh /stop để dừng gửi giá coin
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.job_queue.jobs():
        for job in context.job_queue.jobs():
            job.schedule_removal()
        chat_id = update.effective_chat.id
        if chat_id in last_message_id and last_message_id[chat_id] is not None:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id, message_id=last_message_id[chat_id])
                last_message_id[chat_id] = None
            except Exception as e:
                logging.warning(
                    f"Không thể xóa tin nhắn cuối cùng khi dừng: {e}")
        await update.message.reply_text("Đã dừng gửi giá coin!",
                                        parse_mode="Markdown")
    else:
        await update.message.reply_text("Không có tác vụ nào đang chạy!",
                                        parse_mode="Markdown")


if __name__ == '__main__':
    import asyncio  # Thêm import asyncio
    application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN).build()

    giacoin_handler = CommandHandler('giacoin', giacoin)
    stop_handler = CommandHandler('stop', stop)

    application.add_handler(giacoin_handler)
    application.add_handler(stop_handler)

    application.run_polling()
