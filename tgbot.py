import os
import telebot
import funcs
from loguru import logger

TOKEN = ""

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=["document"])
def encrypt_document(message: telebot.types.Message):
    try:
        bot.send_message(message.chat.id, "took a document " + message.document.file_name)
        logger.info("took a document " + message.document.file_name)

        file_info = bot.get_file(message.document.file_id)
        data = bot.download_file(file_info.file_path)
        outimg_file: str = None

        with open(message.document.file_name, "wb") as f:
            f.write(data)

        if message.caption:
            bot.send_message(message.chat.id, "encrypting in progress...")
            logger.info("encrypting in progress...")
            outimg_file = message.document.file_name + "_OUT.png"
            funcs.encode(message.document.file_name, funcs.encrypt(message.caption), outimg_file)
            bot.send_document(message.chat.id, open(outimg_file, "rb"))
            logger.success("encrypting done")
        else:
            bot.send_message(message.chat.id, "decrypting in progress...")
            logger.info("decrypting in progress...")
            bot.send_message(message.chat.id, funcs.decrypt(funcs.decode(message.document.file_name)))
            logger.success("decrypting done...")
    except Exception as e:
        bot.send_message(message.chat.id, "a bit error")
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

        logger.info("took a photo " + file_info.file_path)
        bot.send_message(message.chat.id, "took a photo " + file_info.file_path)

        with open(str(message.chat.id) + ".jpg", "wb") as f:
            f.write(data)

        if message.caption:
            bot.send_message(message.chat.id, "encrypting in progress...")
            logger.info("encrypting in progress...")
            outimg_file = str(message.chat.id) + "_OUT.png"
            funcs.encode(str(message.chat.id) + ".jpg", funcs.encrypt(message.caption), outimg_file)
            bot.send_document(message.chat.id, open(outimg_file, "rb"))
            logger.success("encrypting done")
        else:
            bot.send_message(message.chat.id, "decrypting in progress...")
            logger.info("decrypting in progress...")
            bot.send_message(message.chat.id, funcs.decrypt(funcs.decode(str(message.chat.id) + ".jpg")))
            logger.success("decrypting done...")
    except Exception as e:
        bot.send_message(message.chat.id, "a bit error")
        logger.error(f"{e}")
    finally:
        os.remove(str(message.chat.id) + ".jpg")
        if outimg_file:
            os.remove(outimg_file)

logger.info("start bot")
bot.infinity_polling()
