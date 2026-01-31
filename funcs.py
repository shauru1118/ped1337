import os
from os import path
from cryptography.fernet import Fernet

from PIL import Image


#! encrypt text


KEY_FILE_NAME = "KEY.KEY"

if path.exists(KEY_FILE_NAME):
    key = open(KEY_FILE_NAME, "r").read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE_NAME, "wb") as key_file:
        key_file.write(key)

crypter = Fernet(key)

def encrypt(text:str) -> str:
    return crypter.encrypt(text.encode("utf-8")).decode("utf-8")

def decrypt(text:str) -> str:
    return crypter.decrypt(text).decode("utf-8")


#! hide text in image


def text_to_bits(text):
    return ''.join(format(b, '08b') for b in text.encode('utf-8')) + '00000000'

def bits_to_text(bits):
    data = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if byte == '00000000':
            break
        data.append(int(byte, 2))
    return bytes(data).decode('utf-8', errors='ignore')

def encode(image_path, text, out_path):
    img = Image.open(image_path)
    img = img.convert('RGB')  # оставляем RGB, без дополнительных операций
    pixels = list(img.getdata())  # getdata() вместо get_flattened_data()
    bits = text_to_bits(text)
    idx = 0
    new_pixels = []

    for r, g, b in pixels:
        if idx < len(bits):
            r = (r & ~1) | int(bits[idx]); idx += 1
        if idx < len(bits):
            g = (g & ~1) | int(bits[idx]); idx += 1
        if idx < len(bits):
            b = (b & ~1) | int(bits[idx]); idx += 1
        new_pixels.append((r, g, b))

    img.putdata(new_pixels)
    img.save(out_path, format=img.format)

def decode(image_path):
    img = Image.open(image_path).convert('RGB')
    pixels = list(img.get_flattened_data())
    bits = ''

    for r, g, b in pixels:
        bits += str(r & 1)
        bits += str(g & 1)
        bits += str(b & 1)

    return bits_to_text(bits)

#! 