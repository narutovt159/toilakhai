import logging
import time
import tempfile
import subprocess
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from webdriver_manager.chrome import ChromeDriverManager
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Telegram Bot Token
TG_BOT_ACCESS_TOKEN = '7370288287:AAEGJlx_o36SifDl5Q1XujSLAocUfysUb4U'  # 🔴 Thay bằng token thật

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File để lưu danh sách bài viết đã gửi
SENT_ARTICLES_FILE = "sent_articles.json"

# Danh sách lưu bài viết đã gửi
sent_articles = set()

# Hàm đọc danh sách bài viết đã gửi từ file
def load_sent_articles():
    global sent_articles
    if os.path.exists(SENT_ARTICLES_FILE):
        with open(SENT_ARTICLES_FILE, 'r') as f:
            sent_articles.update(json.load(f))

# Hàm lưu danh sách bài viết đã gửi vào file
def save_sent_articles():
    with open(SENT_ARTICLES_FILE, 'w') as f:
        json.dump(list(sent_articles), f)

# Hàm dừng các tiến trình Chrome/Chromedriver
def kill_chrome_processes():
    try:
        subprocess.run(["pkill", "-9", "chrome"], check=False)
        subprocess.run(["pkill", "-9", "chromedriver"], check=False)
        time.sleep(1)
    except Exception as e:
        logger.warning(f"Không thể dừng tiến trình Chrome: {e}")

# Configure Selenium WebDriver
def init_driver():
    kill_chrome_processes()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-cache")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("user-agent=Mozilla/5.0")
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver, user_data_dir
    except Exception as e:
        logger.error(f"Lỗi khởi tạo driver: {e}")
        raise

# Hàm dọn dẹp tài nguyên
def cleanup_driver(driver, user_data_dir):
    try:
        driver.quit()
        import shutil
        shutil.rmtree(user_data_dir, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Lỗi khi dọn dẹp: {e}")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), retry=retry_if_exception_type(Exception))
def get_latest_tintuc():
    """Lấy danh sách 3 bài viết mới nhất từ Tapchibitcoin.io"""
    driver = None
    user_data_dir = None
    try:
        driver, user_data_dir = init_driver()
        driver.get("https://tapchibitcoin.io")
        wait = WebDriverWait(driver, 15)
        articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "entry-title")))[:3]

        latest_articles = []
        for article in articles:
            try:
                title = article.find_element(By.TAG_NAME, "a").get_attribute("title")
                link = article.find_element(By.TAG_NAME, "a").get_attribute("href")

                if "[QC]" in title or "quảng cáo" in title.lower():
                    logger.info(f"🔴 Bỏ qua bài viết quảng cáo: {title}")
                    continue

                if link in sent_articles:
                    continue

                description, image_url = get_article_details(link)
                if not description:
                    logger.info(f"⚠️ Bỏ qua bài viết không có mô tả: {title}")
                    continue

                article_info = f"📰 *{title}*\n\n{description}\n[Đọc thêm]({link})\n\n@onusfuture"
                latest_articles.append((title, article_info, image_url, link))
            except Exception as e:
                logger.error(f"Lỗi khi xử lý bài viết: {e}")
                continue

        return latest_articles
    finally:
        if driver:
            cleanup_driver(driver, user_data_dir)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), retry=retry_if_exception_type(Exception))
def get_article_details(url):
    """Lấy chi tiết bài viết (mô tả và ảnh)"""
    driver = None
    user_data_dir = None
    try:
        driver, user_data_dir = init_driver()
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # Cuộn trang để tải nội dung động
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Lấy mô tả
        try:
            content_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "td-post-content")))
            paragraphs = content_div.find_elements(By.TAG_NAME, "p")
            description = "\n".join([p.text.strip() for p in paragraphs[:2] if p.text.strip()])
            if not description:
                return None, None
        except:
            return None, None

        # Lấy ảnh
        try:
            image_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.attachment-large")))
            image_url = image_element.get_attribute("src")
        except:
            image_url = None

        return description, image_url
    finally:
        if driver:
            cleanup_driver(driver, user_data_dir)

async def send_latest_tintuc(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    try:
        new_articles = get_latest_tintuc()
        for title, article_text, image_url, link in new_articles:
            if link not in sent_articles:
                sent_articles.add(link)
                save_sent_articles()

                buttons = [
                    [InlineKeyboardButton("✍️ ĐĂNG KÝ ONUS NHẬN 270K", url="https://signup.goonus.io/6277729708298887070?utm_campaign=invite")],
                    [
                        InlineKeyboardButton("🙋Hướng dẫn", url="https://youtu.be/uS2AsvN1kUY?si=cXWj3prCKLpM6876"),
                        InlineKeyboardButton("Zalo hỗ trợ", url="https://zalo.me/0962804956")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(buttons)

                if image_url:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=article_text, parse_mode="Markdown", reply_markup=reply_markup)
                    except Exception as e:
                        logger.warning(f"Lỗi khi gửi ảnh: {e}")
                        await context.bot.send_message(chat_id=chat_id, text=article_text, parse_mode="Markdown", reply_markup=reply_markup)
                else:
                    await context.bot.send_message(chat_id=chat_id, text=article_text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Lỗi khi gửi tin tức: {e}")

async def tintuc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    load_sent_articles()
    context.job_queue.run_repeating(send_latest_tintuc, interval=60, first=1, chat_id=chat_id)
    await update.message.reply_text("Đã bắt đầu cập nhật tin tức từ Tapchibitcoin.io!")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN).build()
    tintuc_handler = CommandHandler('tintuc', tintuc)
    application.add_handler(tintuc_handler)
    logger.info("Bot đang khởi động...")
    application.run_polling()
