import logging
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
TG_BOT_ACCESS_TOKEN = '7645025545:AAGQNr3XBjsyNDU25f4DgefBDRvjYUHbNLo'  # 🔴 Replace with your real token

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# List to track sent articles to avoid duplicates
sent_articles = set()

# Initialize WebDriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without GUI (suitable for servers)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Fetch titles and links from the news page
def get_titles_from_page():
    """Fetch titles and links from https://allinstation.com/tin-tuc/"""
    driver = None
    try:
        driver = init_driver()
        logging.info("Accessing the news page...")
        driver.get("https://allinstation.com/tin-tuc/")
        
        # Wait for the element with aria-live="polite" to appear
        logging.info("Waiting for aria-live element...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-live="polite"]'))
        )

        # Scroll to load all content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState;") == "complete"
        )

        # Fetch articles
        articles = driver.find_elements(By.CSS_SELECTOR, '[aria-live="polite"] div.post-item a')
        logging.info(f"Number of articles found: {len(articles)}")
        titles_with_links = []

        for article in articles:
            try:
                title = article.text.strip()
                link = article.get_attribute("href")
                if title and link:
                    titles_with_links.append((title, link))
            except Exception as e:
                logging.error(f"Error processing article: {e}")
                continue

        return titles_with_links
    except Exception as e:
        logging.error(f"Error fetching titles and links: {e}")
        return []
    finally:
        if driver:
            driver.quit()

# Fetch the second paragraph from an article
def get_second_paragraph_from_article(link):
    """Fetch the second paragraph from an article"""
    driver = None
    try:
        driver = init_driver()
        driver.get(link)
        
        # Wait for article content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-content'))
        )
        
        # Get all paragraphs
        content = driver.find_element(By.CSS_SELECTOR, '.entry-content')
        paragraphs = content.find_elements(By.TAG_NAME, 'p')
        
        # Check and fetch the second paragraph
        if len(paragraphs) >= 2:
            second_paragraph = paragraphs[1].text.strip()
        else:
            second_paragraph = "Second paragraph not found."
        
        return second_paragraph
    except Exception as e:
        logging.error(f"Error fetching article content from {link}: {e}")
        return "Unable to fetch content."
    finally:
        if driver:
            driver.quit()

# Fetch featured image and background image of an article
def get_featured_image_and_background(link):
    """Fetch the featured image and background image of an article"""
    driver = None
    try:
        driver = init_driver()
        driver.get(link)
        
        # Wait for article content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.entry-content'))
        )
        
        # Fetch featured image (og:image)
        image_url = None
        try:
            image_meta = driver.find_element(By.XPATH, "//meta[@property='og:image']")
            image_url = image_meta.get_attribute("content")
        except:
            image_url = None
        
        # Fetch background image
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
        logging.error(f"Error fetching featured and background images: {e}")
        return None, None
    finally:
        if driver:
            driver.quit()

# Define function to send news articles
async def send_latest_tinvit(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    new_articles = get_titles_from_page()  # Fetch new articles

    # Limit to the first 10 articles
    for idx, (title, link) in enumerate(new_articles[:10], 1):
        if title not in sent_articles:
            sent_articles.add(title)  # Mark article as sent

            # Fetch the second paragraph
            second_paragraph = get_second_paragraph_from_article(link)
            
            # Fetch featured and background images
            image_url, background_image = get_featured_image_and_background(link)

            # Add buttons
            buttons = [
                [InlineKeyboardButton("✍️ ĐĂNG KÝ ONUS NHẬN 270K", url="https://signup.goonus.io/6277729708298887070?utm_campaign=invite")],
                [
                    InlineKeyboardButton("🙋Hướng dẫn", url="https://youtu.be/uS2AsvN1kUY?si=cXWj3prCKLpM6876"),
                    InlineKeyboardButton("Zalo hỗ trợ", url="https://zalo.me/0962804956")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

            # Send new article with description and link
            article_text = f"📰 *{title}*\n\n{second_paragraph}\n[Đọc thêm]({link})\n\n@onusfuture"
            
            # Send image (if available)
            try:
                if image_url:
                    await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=article_text, parse_mode="Markdown", reply_markup=reply_markup)
                else:
                    await context.bot.send_message(chat_id=chat_id, text=article_text, parse_mode="Markdown", reply_markup=reply_markup)
            except Exception as e:
                logging.error(f"Error sending article to Telegram: {e}")
                await context.bot.send_message(chat_id=chat_id, text=f"📰 *{title}*\n\nError sending article, please check again.\n[Đọc thêm]({link})", parse_mode="Markdown")

# Define function for the "/tinvit" command
async def tinvit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("Starting to fetch new articles...")

    # Check for new articles every 10 seconds
    context.job_queue.run_repeating(send_latest_tinvit, interval=10, first=1, chat_id=chat_id)

# Register bot and run
if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN).build()

    tinvit_handler = CommandHandler('tinvit', tinvit)
    application.add_handler(tinvit_handler)

    logging.info("Bot is running...")
    application.run_polling()