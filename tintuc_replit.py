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

# Telegram Bot Token
TG_BOT_ACCESS_TOKEN = '7370288287:AAEGJlx_o36SifDl5Q1XujSLAocUfysUb4U'  # 🔴 Thay bằng token thật

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

# Danh sách lưu bài viết đã gửi để tránh trùng lặp
sent_articles = set()


# Configure Selenium WebDriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_latest_tintuc():
    """Lấy danh sách 10 bài viết mới nhất từ Tapchibitcoin.io bằng Selenium"""
    try:
        driver = init_driver()
        driver.get("https://tapchibitcoin.io")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME,
                 "entry-title")))  # Đợi đến khi các bài viết xuất hiện

        # Lấy danh sách bài viết (chỉ lấy 10 bài đầu tiên)
        articles = driver.find_elements(
            By.CLASS_NAME, "entry-title")[:10]  # Lấy 10 bài đầu tiên
        latest_articles = []

        for article in articles:
            try:
                title = article.find_element(By.TAG_NAME,
                                             "a").get_attribute("title")
                link = article.find_element(By.TAG_NAME,
                                            "a").get_attribute("href")

                # 🔴 **Bỏ qua các bài viết chứa "[QC]" hoặc "quảng cáo" trong tiêu đề**
                if "[QC]" in title or "quảng cáo" in title.lower():
                    logging.info(f"🔴 Bỏ qua bài viết quảng cáo: {title}")
                    continue

                # Nếu bài viết này đã gửi trước đó, bỏ qua
                if title in sent_articles:
                    continue

                # Truy cập bài viết để lấy thông tin thêm
                driver.get(link)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME,
                         "td-post-content")))  # Đợi cho bài viết tải

                # Lấy nội dung bài viết
                content_div = driver.find_element(By.CLASS_NAME,
                                                  "td-post-content")
                description = content_div.find_element(
                    By.TAG_NAME, "p").text if content_div else ""

                # Lấy ảnh đại diện (featured image) của bài viết
                image_url = None
                try:
                    image_meta = driver.find_element(
                        By.XPATH, "//meta[@property='og:image']")
                    image_url = image_meta.get_attribute("content")
                except:
                    pass

                # Tạo nội dung tin nhắn
                article_info = f"📰 *{title}*\n\n{description}\n[Đọc thêm]({link})\n\n@onusfuture"
                latest_articles.append((title, article_info, image_url, link))
            except Exception as e:
                logging.error(f"Lỗi khi bài viết: {e}")
                continue

        driver.quit()  # Đóng trình duyệt

        return latest_articles
    except Exception as e:
        logging.error(f"Lỗi khi lấy tin tức: {e}")
        return []


async def send_latest_tintuc(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    new_articles = get_latest_tintuc()  # Lấy danh sách bài viết mới

    # Kiểm tra bài mới, nếu không có thì bỏ qua
    for title, article_text, image_url, link in new_articles:
        if title not in sent_articles:
            sent_articles.add(title)  # Đánh dấu bài đã gửi

            # Thêm nút nhấn
            buttons = [
                [
                    InlineKeyboardButton(
                        "✍️ ĐĂNG KÝ ONUS NHẬN 270K",
                        url=
                        "https://signup.goonus.io/6277729708298887070?utm_campaign=invite"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🙋Hướng dẫn",
                        url="https://youtu.be/uS2AsvN1kUY?si=cXWj3prCKLpM6876"
                    ),
                    InlineKeyboardButton("Zalo hỗ trợ",
                                         url="https://zalo.me/0962804956")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(buttons)

            # Gửi bài viết mới với ảnh (nếu có)
            if image_url:
                await context.bot.send_photo(chat_id=chat_id,
                                             photo=image_url,
                                             caption=article_text,
                                             parse_mode="Markdown",
                                             reply_markup=reply_markup)
            else:
                await context.bot.send_message(chat_id=chat_id,
                                               text=article_text,
                                               parse_mode="Markdown",
                                               reply_markup=reply_markup)


async def tintuc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Cứ mỗi 5 giây kiểm tra xem có bài mới không
    context.job_queue.run_repeating(send_latest_tintuc,
                                    interval=10,
                                    first=1,
                                    chat_id=chat_id)


if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN).build()

    tintuc_handler = CommandHandler('tintuc', tintuc)
    application.add_handler(tintuc_handler)

    application.run_polling()
