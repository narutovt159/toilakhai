import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Token Telegram
TG_BOT_ACCESS_TOKEN1 = '7553105747:AAE9P0yboZrGRlQg9YfyQreNebDCwy4O6cA'  # 🔴 Thay thế bằng Token thật

# Cấu hình logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Lưu trữ các tin đã gửi để tránh trùng lặp
sent_articles = set()

# 📰 Lấy danh sách tin tức mới nhất
def get_latest_tinmoi():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://goonus.io/insights/?tab=newsfeed")

        wait = WebDriverWait(driver, 10)
        articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "insight-title")))

        latest_articles = []
        for article in articles[:3]:  # Chỉ lấy 3 bài mới nhất
            title = article.text.strip()
            parent_div = article.find_element(By.XPATH, "../..")
            actual_link = parent_div.find_element(By.CSS_SELECTOR, 'a.text-xs[href]').get_attribute("href")
            
            if title and actual_link:
                latest_articles.append((title, actual_link))

        driver.quit()
        return latest_articles if latest_articles else []
    except Exception as e:
        logging.error(f"Lỗi khi lấy tin tức: {e}")
        return []

# 📌 Lấy chi tiết bài viết (mô tả & ảnh)
def get_article_details(url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # ✅ Cuộn xuống để tải hết nội dung
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # ✅ Lấy mô tả từ class insight-content
        try:
            content_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "insight-content")))
            paragraphs = content_div.find_elements(By.TAG_NAME, "p") + content_div.find_elements(By.TAG_NAME, "div")
            description = "\n".join([p.text.strip() for p in paragraphs[:2] if p.text.strip()])

            if not description:
                logging.warning(f"⚠️ Nội dung bài viết {url} bị trống!")
                description = None
        except Exception:
            description = None

        # ✅ Lấy ảnh từ bài viết (class: el-image w-full)
        try:
            image_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.el-image.w-full img")))
            image_url = image_element.get_attribute("src")
            if image_url:
                logging.info(f"✅ Ảnh tìm thấy: {image_url}")
            else:
                image_url = None
        except Exception as e:
            logging.warning(f"⚠️ Không tìm thấy ảnh: {e}")
            image_url = None


        driver.quit()
        return description, image_url
    except Exception:
        return None, None

# 📩 Gửi tin tức mới nhất lên Telegram
async def send_latest_tinmoi(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    latest_tinmoi = get_latest_tinmoi()

    if latest_tinmoi:
        for title, link in latest_tinmoi:
            # Bỏ qua bài viết nếu đã gửi trước đó
            if link in sent_articles:
                logging.info(f"🔄 Bỏ qua tin trùng: {title}")
                continue  

            description, image_url = get_article_details(link)

            # Nếu không có mô tả thì bỏ qua bài viết này
            if not description:
                logging.info(f"⚠️ Bỏ qua bài viết không có mô tả: {title}")
                continue  

            # Đánh dấu bài viết đã gửi
            sent_articles.add(link)

            message = f"⭐ *{title}*\n\n{description}\n\n@onusfuture"

            # 🔹 Thêm các nút bấm
            buttons = [
                [InlineKeyboardButton("✍️ ĐĂNG KÝ ONUS NHẬN 270K", url="https://signup.goonus.io/6277729708298887070?utm_campaign=invite")],
                [
                    InlineKeyboardButton("🙋Hướng dẫn", url="https://youtu.be/uS2AsvN1kUY?si=cXWj3prCKLpM6876"),
                    InlineKeyboardButton("ZALO hỗ trợ", url="https://zalo.me/0962804956")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

            # 🔹 Gửi tin nhắn
            if image_url:
                try:
                    await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=message, parse_mode="Markdown", reply_markup=reply_markup)
                except Exception as e:
                    logging.warning(f"Lỗi khi gửi ảnh từ URL: {e}")
                    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", reply_markup=reply_markup)

# 🚀 Khởi chạy bot Telegram
async def tinmoi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(
        send_latest_tinmoi, interval=50, first=1, chat_id=chat_id
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN1).build()
    tinmoi_handler = CommandHandler('tinmoi', tinmoi)
    application.add_handler(tinmoi_handler)
    application.run_polling()
