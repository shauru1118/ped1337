from funcs import decode, decrypt

import argparse
import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<level>{level}\t| {message}</level>"
)

parser = argparse.ArgumentParser()
parser.add_argument("inimg", type=str, help="input image path")

args = parser.parse_args()

input_image_path:str = args.inimg

logger.info(f"Расшифровываю данные из изображения '{input_image_path}' ...")


#! main part

decoded_text = decode(input_image_path)
text = decrypt(decoded_text)

#! main part end


logger.success(f"Готово! Текст: {text}!")

FILE_WITH_TEXT = f"{input_image_path}_TEXT.txt"

with open(FILE_WITH_TEXT, "w", encoding="utf-8") as file:
    file.write(text)

logger.info(f"Текст сохранён в файл '{FILE_WITH_TEXT}'")
