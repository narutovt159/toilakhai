import logging
import tempfile
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Telegram Bot Token
TG_BOT_ACCESS_TOKEN = '7645025545:AAGQNr3XBjsyNDU25f4DgefBDRvjYUHbNLo'  # 🔴 Thay bằng token thật

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Danh sách lưu bài viết đã gửi để tránh trùng lặp
sent_articles = set()

# Hàm dừng các tiến trình Chrome/Chromedriver
def kill_chrome_processes():
    try:
        subprocess.run(["pkill", "-9", "chrome"], check=False)
        subprocess.run(["pkill", "-9", "chromedriver"], check=False)
        time.sleep(1)  # Đợi để đảm bảo tiến trình đã dừng
    except Exception as e:
        logging.warning(f"Không thể dừng tiến trình Chrome: {e}")

# Khởi tạo WebDriver
def init_driver():
    kill_chrome_processes()  # Dừng tiến trình trước khi khởi tạo
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Tắt giao diện đồ họa
    chrome_options.add_argument("--no-sandbox")  # Tắt sandbox để tương thích container
    chrome_options.add_argument("--disable-dev-shm-usage")  # Giảm sử dụng bộ nhớ chia sẻ
    chrome_options.add_argument("--disable-gpu")  # Tắt GPU để giảm tải
    chrome_options.add_argument("--no-cache")  # Vô hiệu hóa cache
    chrome_options.add_argument("--disable-extensions")  # Tắt extensions không cần thiết
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # Tạo thư mục tạm duy nhất
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Lấy tiêu đề và liên kết từ trang tin tức
def get_titles_from_page():
    """Lấy tiêu đề và liên kết từ https://allinstation.com/tin-tuc/"""
    driver = None
    try:
        driver = init_driver()
        logging.info("Đang truy cập trang tin tức...")
        driver.get("https://allinstation.com/tin-tuc/")
        
        # Chờ phần tử aria-live xuất hiện
        logging.info("Đang chờ phần tử aria-live...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-live="polite"]'))
        )

        # Cuộn để tải toàn bộ nội dung
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState;") == "complete"
        )

        # Lấy bài viết
        articles = driver.find_elements(By.CSS_SELECTOR, '[aria-live="polite"] div.post-item a')
        logging.info(f"Số bài viết tìm thấy: {len(articles)}")
        titles_with_links = []

        for article in articles:
            try:
                title = article.text.strip()
                link = article.get_attribute("href")
                if title and link:
                    titles_with_links.append((title, link))
            except Exception as e:
                logging.error(f"Lỗi khi xử lý bài viết: {e}")
                continue

        return titles_with_links
    except Exception as e:
        logging.error(f"Lỗi khi lấy tiêu đề và liên kết: {e}")
        return []
    finally:
        if driver:
            driver.quit()

# Lấy đoạn văn thứ hai từ bài viết
def get_second_paragraph_from_article(link):
    """Lấy đoạn văn thứ hai từ bài viết"""
    driver = None
    try:
        driver = init_driver()
        driver.get(link)
        
        # Chờ nội dung bài viết tải
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-content'))
        )
        
        # Lấy tất cả đoạn văn
        content = driver.find_element(By.CSS_SELECTOR, '.entry-content')
        paragraphs = content.find_elements(By.TAG_NAME, 'p')
        
        # Kiểm tra và lấy đoạn văn thứ hai
        if len(paragraphs) >= 2:
            second_paragraph = paragraphs[1].text.strip()
        else:
            second_paragraph = "Không tìm thấy đoạn văn thứ hai."
        
        return second_paragraph
    except Exception as e:
        logging.error(f"Lỗi khi lấy nội dung bài viết từ {link}: {e}")
        return "Không thể lấy nội dung."
    finally:
        if driver:
            driver.quit()

# Lấy ảnh nổi bật và ảnh nền của bài viết
def get_featured_image_and_background(link):
    """Lấy ảnh nổi bật và ảnh nền của bài viết"""
    driver = None
    try:
        driver = init_driver()
        driver.get(link)
        
        # Chờ nội dung bài viết tải
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-content'))
        )
        
        # Lấy ảnh nổi bật (og:image)
        image_url = None
        try:
            image_meta = driver.find_element(By.XPATH, "//meta[@property='og:image']")
            image_url = image_meta.get_attribute("content")
        except:
            image_url = None
        
        # Lấy ảnh nền
        background_image = None
        try:
            background_element = driver.find_element(By.CSS_SELECTOR, '.entry-content')
            background_image = background_element.value_of_css_property('background-image')
            if background_image and background_image.startswith("url"):
                background_image = background_image.split('(')[1].split(')')[0].replace('"', '').replace("'", "")
        except:
            background_image = None
        
        return image_url, background_image
    except Exception as e:
        logging.error(f"Lỗi khi lấy ảnh nổi bật và ảnh nền: {e}")
        return None, None
    finally:
        if driver:
            driver.quit()

# Gửi bài viết tin tức
async def send_latest_tinvit(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    new_articles = get_titles_from_page()  # Lấy bài viết mới

    # Giới hạn ở 10 bài đầu tiên
    for idx, (title, link) in enumerate(new_articles[:10], 1):
        if title not in sent_articles:
            sent_articles.add(title)  # Đánh dấu bài đã gửi

            # Lấy đoạn văn thứ hai
            second_paragraph = get_second_paragraph_from_article(link)
            
            # Lấy ảnh nổi bật và ảnh nền
            image_url, background_image = get_featured_image_and_background(link)

            # Thêm nút nhấn
            buttons = [
                [InlineKeyboardButton("✍️ ĐĂNG KÝ ONUS NHẬN 270K", url="https://signup.goonus.io/6277729708298887070?utm_campaign=invite")],
                [
                    InlineKeyboardButton("🙋Hướng dẫn", url="https://youtu.be/uS2AsvN1kUY?si=cXWj3prCKLpM6876"),
                    InlineKeyboardButton("Zalo hỗ trợ", url="https://zalo.me/0962804956")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

            # Gửi bài viết mới với mô tả và liên kết
            article_text = f"📰 *{title}*\n\n{second_paragraph}\n[Đọc thêm]({link})\n\n@onusfuture"
            
            # Gửi ảnh (nếu có)
            try:
                if image_url:
                    await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=article_text, parse_mode="Markdown", reply_markup=reply_markup)
                else:
                    await context.bot.send_message(chat_id=chat_id, text=article_text, parse_mode="Markdown", reply_markup=reply_markup)
            except Exception as e:
                logging.error(f"Lỗi khi gửi bài viết lên Telegram: {e}")
                await context.bot.send_message(chat_id=chat_id, text=f"📰 *{title}*\n\nLỗi khi gửi bài viết, vui lòng kiểm tra lại.\n[Đọc thêm]({link})", parse_mode="Markdown")

# Hàm cho lệnh "/tinvit"
async def tinvit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("Bắt đầu lấy bài viết mới...")

    # Kiểm tra bài mới mỗi 10 giây
    context.job_queue.run_repeating(send_latest_tinvit, interval=10, first=1, chat_id=chat_id)

# Chạy bot
if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN).build()

    tinvit_handler = CommandHandler('tinvit', tinvit)
    application.add_handler(tinvit_handler)

    logging.info("Bot đang chạy...")
    application.run_polling()