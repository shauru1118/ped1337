import dotenv
import os

dotenv.load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
TEMP_DIR_PATH = os.getenv("TEMP_DIR_PATH")
KEY_FILE_PATH = os.getenv("KEY_FILE_PATH")

