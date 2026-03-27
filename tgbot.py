import os
import sys
import telebot
from pathlib import Path
from loguru import logger
from stego import generate_key, load_key, encrypt_data, decrypt_data, embed_lsb, extract_lsb
import config


logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<level>{level}\t| {message}</level>"
)
logger.info("Start bot")

TOKEN = config.TELEGRAM_BOT_TOKEN
TEMP_DIR = Path(config.TEMP_DIR_PATH)
KEY_FILE = Path(config.KEY_FILE_PATH)

bot = telebot.TeleBot(TOKEN)
TEMP_DIR.mkdir(exist_ok=True)
if not os.path.exists(KEY_FILE):
    generate_key(KEY_FILE)
    logger.info(f"Generated new key: {KEY_FILE}")
key = load_key(KEY_FILE)


def save_temp_file(file_bytes, filename):
    path = TEMP_DIR / filename
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def remove_file(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


# ----------------- Обработка документов -----------------
@bot.message_handler(content_types=["document"])
def handle_document(message: telebot.types.Message):
    temp_file = None
    outimg_file = None
    try:
        bot.send_message(message.chat.id, "Принят файл")
        logger.info(f"{message.from_user.username}: document '{message.document.file_name}'")

        file_info = bot.get_file(message.document.file_id)
        data = bot.download_file(file_info.file_path)

        temp_file = save_temp_file(data, message.document.file_name)

        if message.caption:
            bot.send_message(message.chat.id, "Шифрую и маскирую данные...")
            logger.info("Encrypting in progress...")

            outimg_file = TEMP_DIR / (message.document.file_name + "_OUT.png")
            embed_lsb(str(temp_file), str(outimg_file), encrypt_data(message.caption.encode(), key))
            bot.send_document(message.chat.id, open(outimg_file, "rb"))
            logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровываю данные...")
            logger.info("Decrypting in progress...")
            extracted = extract_lsb(str(temp_file))
            decrypted_text = decrypt_data(extracted, key).decode(errors="ignore")
            bot.send_message(message.chat.id, decrypted_text)
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка! {e}")
        logger.error(f"{e}")
    finally:
        if temp_file:
            remove_file(temp_file)
        if outimg_file:
            remove_file(outimg_file)


# ----------------- Обработка фотографий -----------------
@bot.message_handler(content_types=["photo"])
def handle_photo(message: telebot.types.Message):
    temp_file = None
    outimg_file = None
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        data = bot.download_file(file_info.file_path)

        temp_file = save_temp_file(data, f"{message.chat.id}.jpg")
        bot.send_message(message.chat.id, "Принято фото")
        logger.info(f"{message.from_user.username}: photo '{file_info.file_path}'")

        if message.caption:
            bot.send_message(message.chat.id, "Шифрую и маскирую данные...")
            logger.info("Encrypting in progress...")

            outimg_file = TEMP_DIR / f"{message.chat.id}_OUT.png"
            embed_lsb(str(temp_file), str(outimg_file), encrypt_data(message.caption.encode(), key))
            bot.send_document(message.chat.id, open(outimg_file, "rb"))
            logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровываю данные...")
            logger.info("Decrypting in progress...")
            extracted = extract_lsb(str(temp_file))
            decrypted_text = decrypt_data(extracted, key).decode(errors="ignore")
            bot.send_message(message.chat.id, decrypted_text)
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка! {e}")
        logger.error(f"{e}")
    finally:
        if temp_file:
            remove_file(temp_file)
        if outimg_file:
            remove_file(outimg_file)


if __name__ == "__main__":
    logger.info("Bot polling...")
    bot.infinity_polling()

