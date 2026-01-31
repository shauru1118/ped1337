import os
import sys
import telebot
import funcs
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<level>{level}\t| {message}</level>"
)
logger.info("start program")


TOKEN = ""

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=["document"])
def encrypt_document(message: telebot.types.Message):
    try:
        bot.send_message(message.chat.id, f"Принят файл")
        logger.info(f"{message.from_user.username}: document '{message.document.file_name}'")

        file_info = bot.get_file(message.document.file_id)
        data = bot.download_file(file_info.file_path)
        outimg_file: str = None

        with open(message.document.file_name, "wb") as f:
            f.write(data)

        if message.caption:
            bot.send_message(message.chat.id, "Шифрую и маскирую данные...")
            logger.info("Encrypting in progress...")
            outimg_file = message.document.file_name + "_OUT.png"
            funcs.encode(message.document.file_name, funcs.encrypt(message.caption), outimg_file)
            bot.send_document(message.chat.id, open(outimg_file, "rb"))
            logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровыаю данные...")
            logger.info("Decrypting in progress...")
            bot.send_message(message.chat.id, funcs.decrypt(funcs.decode(message.document.file_name)))
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка! Возможно вы отправили не тот файли и т.д.")
        logger.error(f"{e}")
    finally:
        os.remove(message.document.file_name)
        if outimg_file:
            os.remove(outimg_file)



@bot.message_handler(content_types=["photo"])
def encrypt_photo(message: telebot.types.Message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        data = bot.download_file(file_info.file_path)
        outimg_file: str = None

        bot.send_message(message.chat.id, "Принято фото")
        logger.info(f"{message.from_user.username}: photo '{file_info.file_path}'")

        with open(str(message.chat.id) + ".jpg", "wb") as f:
            f.write(data)

        if message.caption:
            bot.send_message(message.chat.id, "Шифрую и маскирую данные...")
            logger.info("Encrypting in progress...")
            outimg_file = str(message.chat.id) + "_OUT.png"
            funcs.encode(str(message.chat.id) + ".jpg", funcs.encrypt(message.caption), outimg_file)
            bot.send_document(message.chat.id, open(outimg_file, "rb"))
            logger.success(f"Encrypting done: {outimg_file}")
        else:
            bot.send_message(message.chat.id, "Расшифровыаю данные...")
            logger.info("Decrypting in progress...")
            bot.send_message(message.chat.id, funcs.decrypt(funcs.decode(str(message.chat.id) + ".jpg")))
            logger.success("Decrypting done")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка! Возможно вы отправили не тот файли и т.д.")
        logger.error(f"{e}")
    finally:
        os.remove(str(message.chat.id) + ".jpg")
        if outimg_file:
            os.remove(outimg_file)

logger.info("start bot")
bot.infinity_polling()
