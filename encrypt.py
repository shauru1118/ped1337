from funcs import encode, encrypt

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
parser.add_argument("text", type=str, help="text")
parser.add_argument("outimg", type=str, default="", help="output image path")

args = parser.parse_args()

input_image_path:str = args.inimg
output_image_path:str = args.outimg if args.outimg != "" else "OUT_" + args.inimg + ".png"
text:str = args.text

logger.info(f"Шифруую текст, маскирую его в изображение '{input_image_path}' и сохраняю новое в '{output_image_path}'")


#! main part

encrypted_text = encrypt(text)

encode(input_image_path, encrypted_text, output_image_path)

#! main part end


logger.success(f"Готово! Изображение сохранено в '{output_image_path}'!")
