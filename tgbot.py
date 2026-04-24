import os
import sys
import telebot
from pathlib import Path
from loguru import logger
from stego.funcs import (
    generate_key,
    load_key,
    encrypt_data,
    decrypt_data,
    embed_lsb,
    extract_lsb,
    get_visualized_lsb_blocks,
)
import config


logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<level>{level}\t| {message}</level>",
)
logger.info("Start bot")

TOKEN = config.TELEGRAM_BOT_TOKEN
TEMP_DIR = Path(config.TEMP_DIR_PATH)
KEY_FILE = Path(config.KEY_FILE_PATH)
ADMIN_CHAT_ID = config.ADMIN_CHAT_ID

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


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\nЯ умею шифровать и расшифровывать данные в изображениях.\n\n"
        + "Для шифровки отправь мне фото с подписью текста.\nДля расшифровки отправь мне изображение файлом!",
    )


# ----------------- Обработка документов -----------------
@bot.message_handler(content_types=["document"])
def handle_document(message: telebot.types.Message):
    temp_file = None
    outimg_file = None
    try:
        bot.send_message(message.chat.id, "Принят файл")
        logger.info(
            f"@{message.from_user.username}: document '{message.document.file_name}'"
        )

        file_info = bot.get_file(message.document.file_id)
        data = bot.download_file(file_info.file_path)

        temp_file = save_temp_file(data, message.document.file_name)

        if message.caption:
            bot.send_message(message.chat.id, "Шифрую и маскирую данные...")
            logger.info("Encrypting in progress...")

            outimg_file = TEMP_DIR / (message.document.file_name + "_OUT.png")
            err, p = embed_lsb(
                str(temp_file),
                str(outimg_file),
                encrypt_data(message.caption.encode(), key),
            )
            if err:
                bot.send_message(
                    message.chat.id,
                    f"Сообщение слишком длинное!\nПолучилось вместить лишь {round(p * 100)}% текста.",
                )
                logger.error(f"Embed error: {round(p * 100)}%")
            else:
                images = get_visualized_lsb_blocks(str(outimg_file))
                for img in images:
                    bot.send_document(message.chat.id, open(img, "rb"))
                bot.send_document(message.chat.id, open(outimg_file, "rb"))
                logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровываю данные...")
            logger.info("Decrypting in progress...")
            extracted = extract_lsb(str(temp_file))
            decrypted_text = decrypt_data(extracted, key).decode()
            bot.send_message(message.chat.id, decrypted_text)
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка!")
        error_message_str = f"==== REPORT ====\n\n@{message.from_user.username}\n'{message.text if message.text else ''}'\n\n---- Error ----\n{e.__class__.__name__}: {e.args}"
        bot.send_message(ADMIN_CHAT_ID, error_message_str)
        logger.error(error_message_str)
    finally:
        if temp_file:
            remove_file(temp_file)
        if outimg_file:
            remove_file(outimg_file)
        for img in images:
            if not img:
                continue
            if os.path.exists(img):
                remove_file(img)


# ----------------- Обработка фотографий -----------------
@bot.message_handler(content_types=["photo"])
def handle_photo(message: telebot.types.Message):
    temp_file = None
    outimg_file = None
    images = None
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        data = bot.download_file(file_info.file_path)

        temp_file = save_temp_file(data, f"{message.chat.id}.jpg")
        bot.send_message(message.chat.id, "Принято фото")
        logger.info(f"@{message.from_user.username}: photo '{file_info.file_path}'")

        if message.caption:
            bot.send_message(message.chat.id, "Шифрую и маскирую данные...")
            logger.info("Encrypting in progress...")

            outimg_file = TEMP_DIR / f"{message.chat.id}_OUT.png"
            err, p = embed_lsb(
                str(temp_file),
                str(outimg_file),
                encrypt_data(message.caption.encode(), key),
            )
            if err:
                bot.send_message(
                    message.chat.id,
                    f"Сообщение слишком длинное!\nПолучилось вместить лишь {round(p * 100)}% текста.",
                )
                logger.error(f"Embed error: {round(p * 100)}%")
            else:
                images = get_visualized_lsb_blocks(str(outimg_file))
                for img in images:
                    bot.send_document(message.chat.id, open(img, "rb"))
                bot.send_document(message.chat.id, open(outimg_file, "rb"))
                logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровываю данные...")
            logger.info("Decrypting in progress...")
            extracted = extract_lsb(str(temp_file))
            decrypted_text = decrypt_data(extracted, key).decode()
            bot.send_message(message.chat.id, decrypted_text)
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка!")
        error_message_str = f"==== REPORT ====\n\n@{message.from_user.username}\n'{message.text if message.text else ''}'\n\n---- Error ----\n{e.__class__.__name__}: {e.args}"
        bot.send_message(ADMIN_CHAT_ID, error_message_str)
        logger.error(error_message_str)
    finally:
        if temp_file:
            remove_file(temp_file)
        if outimg_file:
            remove_file(outimg_file)
        for img in images:
            if not img:
                continue
            if os.path.exists(img):
                remove_file(img)


if __name__ == "__main__":
    logger.info("Bot polling...")
    bot.infinity_polling()
