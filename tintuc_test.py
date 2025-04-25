import logging
import tempfile
import subprocess
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from webdriver_manager.chrome import ChromeDriverManager
import atexit
import os

# Telegram Bot Token
TG_BOT_ACCESS_TOKEN = '7370288287:AAEGJlx_o36SifDl5Q1XujSLAocUfysUb4U'  # Thay bằng token thật

# Cấu hình logging chi tiết, ghi vào file
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', mode='a'),
        logging.StreamHandler()
    ]
)

# Danh sách lưu bài viết đã gửi
sent_articles = set()

# Theo dõi thư mục tạm để dọn dẹp
temp_dirs = []

def cleanup_temp_dirs():
    """Dọn dẹp thư mục tạm tạo cho WebDriver."""
    for temp_dir in temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logging.info(f"Đã dọn thư mục tạm: {temp_dir}")
        except Exception as e:
            logging.error(f"Lỗi khi dọn {temp_dir}: {e}")

# Đăng ký hàm dọn dẹp khi chương trình kết thúc
atexit.register(cleanup_temp_dirs)

def kill_chrome_processes():
    """Dừng các tiến trình Chrome và ChromeDriver."""
    try:
        subprocess.run(["pkill", "-9", "chrome"], check=False)
        subprocess.run(["pkill", "-9", "chromedriver"], check=False)
        time.sleep(2)  # Đợi lâu hơn để đảm bảo tiến trình dừng
        logging.info("Đã dừng tiến trình Chrome và ChromeDriver")
    except Exception as e:
        logging.error(f"Lỗi khi dừng tiến trình Chrome: {e}")

def init_driver():
    """Khởi tạo Selenium WebDriver với dọn dẹp hợp lý."""
    kill_chrome_processes()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-cache")
    chrome_options.add_argument("--disable-extensions")
    
    # Tạo thư mục tạm và theo dõi
    user_data_dir = tempfile.mkdtemp()
    temp_dirs.append(user_data_dir)
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        logging.info("Khởi tạo WebDriver thành công")
        return driver
    except Exception as e:
        logging.error(f"Lỗi khởi tạo WebDriver: {e}")
        raise

def get_latest_tintuc():
    """Lấy 10 bài viết mới nhất từ Tapchibitcoin.io."""
    driver = None
    try:
        driver = init_driver()
        driver.get("https://tapchibitcoin.io")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "entry-title"))
        )  # Tăng thời gian chờ

        articles = driver.find_elements(By.CLASS_NAME, "entry-title")[:10]
        latest_articles = []

        for article in articles:
            try:
                title = article.find_element(By.TAG_NAME, "a").get_attribute("title")
                link = article.find_element(By.TAG_NAME, "a").get_attribute("href")

                # Bỏ qua quảng cáo
                if "[QC]" in title or "quảng cáo" in title.lower():
                    logging.info(f"Bỏ qua bài quảng cáo: {title}")
                    continue

                # Bỏ qua bài đã gửi
                if title in sent_articles:
                    continue

                # Lấy chi tiết bài viết
                driver.get(link)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "td-post-content"))
                )

                content_div = driver.find_element(By.CLASS_NAME, "td-post-content")
                description = content_div.find_element(By.TAG_NAME, "p").text if content_div else ""

                # Lấy ảnh
                image_url = None
                try:
                    image_meta = driver.find_element(By.XPATH, "//meta[@property='og:image']")
                    image_url = image_meta.get_attribute("content")
                except:
                    pass

                article_info = f"📰 *{title}*\n\n{description}\n[Đọc thêm]({link})\n\n@onusfuture"
                latest_articles.append((title, article_info, image_url, link))
            except Exception as e:
                logging.error(f"Lỗi xử lý bài viết {title}: {e}")
                continue

        return latest_articles
    except Exception as e:
        logging.error(f"Lỗi lấy tin tức: {e}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("Đã đóng WebDriver")
            except Exception as e:
                logging.error(f"Lỗi đóng WebDriver: {e}")

async def send_latest_tintuc(context: ContextTypes.DEFAULT_TYPE):
    """Gửi bài viết mới đến chat."""
    chat_id = context.job.chat_id
    try:
        new_articles = get_latest_tintuc()
        if not new_articles:
            logging.info("Không tìm thấy bài viết mới")
            return

        for title, article_text, image_url, link in new_articles:
            if title not in sent_articles:
                sent_articles.add(title)
                buttons = [
                    [InlineKeyboardButton("✍️ ĐĂNG KÝ ONUS NHẬN 270K", url="https://signup.goonus.io/6277729708298887070?utm_campaign=invite")],
                    [
                        InlineKeyboardButton("🙋Hướng dẫn", url="https://youtu.be/uS2AsvN1kUY?si=cXWj3prCKLpM6876"),
                        InlineKeyboardButton("Zalo hỗ trợ", url="https://zalo.me/0962804956")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(buttons)

                try:
                    if image_url:
                        await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=article_text, parse_mode="Markdown", reply_markup=reply_markup)
                    else:
                        await context.bot.send_message(chat_id=chat_id, text=article_text, parse_mode="Markdown", reply_markup=reply_markup)
                    logging.info(f"Đã gửi bài viết: {title}")
                    time.sleep(2)  # Tránh giới hạn Telegram
                except Exception as e:
                    logging.error(f"Lỗi gửi bài viết {title}: {e}")
    except Exception as e:
        logging.error(f"Lỗi trong send_latest_tintuc: {e}")

async def tintuc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bắt đầu công việc lấy tin tức."""
    chat_id = update.effective_chat.id
    # Chạy mỗi 5 phút thay vì 10 giây
    context.job_queue.run_repeating(send_latest_tintuc, interval=300, first=1, chat_id=chat_id)
    await update.message.reply_text("Đã bắt đầu lấy tin tức mới mỗi 5 phút.")

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN).build()
        tintuc_handler = CommandHandler('tintuc', tintuc)
        application.add_handler(tintuc_handler)
        logging.info("Bot đã khởi động")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        logging.error(f"Bot gặp sự cố: {e}")
