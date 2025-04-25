import logging
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, JobQueue

# Token Telegram của bạn
TG_BOT_ACCESS_TOKEN1 = '7917417588:AAGhjNyuw9_CXXqyb3xY8JBwP60cjkkf_cg'  # 🔴 Thay bằng token thật

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_latest_positions():
    try:
        # Cấu hình Chrome Options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )

        # Khởi tạo ChromeDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        logging.info("Đã khởi tạo ChromeDriver thành công.")

        # Truy cập trang web
        driver.get("https://goonus.io/insights/?tab=master")
        logging.info("Đã truy cập trang web goonus.io.")

        # Đợi tối đa 15 giây (tăng thời gian chờ)
        wait = WebDriverWait(driver, 15)

        # Kiểm tra và lấy các vị thế giao dịch
        try:
            positions = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "flex-grow.text-black")))
            logging.info(f"Tìm thấy {len(positions)} vị thế giao dịch.")
        except Exception as e:
            logging.error(f"Không thể tìm thấy vị thế giao dịch: {e}")
            driver.quit()
            return []

        # Kiểm tra và lấy phần lãi/lỗ
        try:
            profit_loss_elements = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[contains(@class, 'font-semibold') and (contains(@class, 'text-danger') or contains(@class, 'text-success'))]")))
            logging.info(f"Tìm thấy {len(profit_loss_elements)} phần tử lãi/lỗ.")
        except Exception as e:
            logging.error(f"Không thể tìm thấy phần lãi/lỗ: {e}")
            driver.quit()
            return []

        latest_positions = []
        for i, position in enumerate(positions[:8]):  # Lấy tối đa 5 vị thế
            position_text = position.text.strip()
            profit_loss_text = profit_loss_elements[i].text.strip()

            # Trích xuất phần trăm lãi/lỗ
            percentage_match = re.search(r"([-+]?\d+\.?\d*)%", profit_loss_text)
            percentage_value = float(percentage_match.group(1)) if percentage_match else 0

            # Kiểm tra điều kiện lãi > 40%
            if "text-success" in profit_loss_elements[i].get_attribute("class") and percentage_value > 20:
                latest_positions.append(f"{position_text} - Lãi lớn ✅ {profit_loss_text}")
                logging.info(f"Thêm vị thế: {position_text} - {profit_loss_text}")

        driver.quit()
        return latest_positions if latest_positions else []

    except Exception as e:
        logging.error(f"Lỗi tổng quát trong get_latest_positions: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return []
    
async def send_latest_positions(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id  # Lấy chat_id từ job context
    latest_positions = get_latest_positions()  # Lấy các vị thế mới nhất
    
    if latest_positions:
        # Xóa các tin nhắn cũ nếu có
        if 'message_ids' in context.bot_data:
            for msg_id in context.bot_data['message_ids']:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except Exception as e:
                    logging.error(f"Lỗi khi xóa tin nhắn cũ: {e}")

        # Danh sách để lưu ID của các tin nhắn mới
        new_message_ids = []

        for position in latest_positions:
            # Gửi tin nhắn mới và lưu ID
            message = await context.bot.send_message(chat_id=chat_id, text=position)
            new_message_ids.append(message.message_id)

        # Cập nhật danh sách ID tin nhắn trong context.bot_data
        context.bot_data['message_ids'] = new_message_ids

async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    latest_positions = get_latest_positions()  # Gọi hàm lấy các vị thế mới nhất

    if latest_positions:
        await context.bot.send_message(chat_id=chat_id, text="\n".join(latest_positions))

    # Cập nhật vị thế mới mỗi 100 giây
    context.job_queue.run_repeating(send_latest_positions, interval=20, first=20, chat_id=chat_id)

if __name__ == '__main__':
    # Khởi tạo bot Telegram
    application = ApplicationBuilder().token(TG_BOT_ACCESS_TOKEN1).build()

    # Thêm handler cho lệnh /positions
    positions_handler = CommandHandler('positions', positions)
    application.add_handler(positions_handler)

    # Chạy bot
    application.run_polling()