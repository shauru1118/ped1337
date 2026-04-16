import numpy as np
from PIL import Image
import struct
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import math

MAGIC = b"STEGOv1337"

BLOCK_SIZE = 4  # размер блока для анализа дисперсии
RMSE_LIMIT = 3.5  # максимально допустимая ошибка
VAR_LOW = 20     # порог низкой дисперсии
VAR_HIGH = 100   # порог высокой дисперсии


def generate_key(path):
    key = secrets.token_bytes(32)
    with open(path, "wb") as f:
        f.write(key)


def load_key(path):
    with open(path, "rb") as f:
        return f.read()


# ----------------- Шифрование -----------------
def encrypt_data(data: bytes, key: bytes):
    aes = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ciphertext = aes.encrypt(nonce, data, None)
    return nonce + ciphertext


def decrypt_data(data: bytes, key: bytes):
    nonce = data[:12]
    ciphertext = data[12:]
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None)


# ----------------- Конвертеры -----------------
def bytes_to_bits(data: bytes):
    return "".join(f"{b:08b}" for b in data)


def bits_to_bytes(bits: str):
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


# ----------------- Изображения -----------------
def load_image(path):
    img = Image.open(path).convert("RGB")
    return np.array(img)


def save_image(arr, path):
    Image.fromarray(arr).save(path, "PNG")


# ----------------- RMSE и дисперсия -----------------
def rmse_block(original, modified):
    diff = original.astype(np.float32) - modified.astype(np.float32)
    return math.sqrt(np.mean(diff ** 2))


def local_variance(block):
    return np.var(block)


# ----------------- Маскировка данных -----------------
def embed_lsb(image_path, output_path, payload: bytes):
    img = load_image(image_path)
    h, w, _ = img.shape

    payload = struct.pack(">I", len(payload)) + payload
    bits = bytes_to_bits(payload)
    bit_idx = 0

    data = img.copy()
    block_map = []

    for y in range(0, h, BLOCK_SIZE):
        for x in range(0, w, BLOCK_SIZE):

            if bit_idx >= len(bits):
                block_map.append(3)
                continue

            block = data[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE].copy()
            modified = block.copy()

            variance = local_variance(block)

            if variance < VAR_LOW:
                bits_per_channel = 0
            elif variance < VAR_HIGH:
                bits_per_channel = 1
            else:
                bits_per_channel = 2

            if bits_per_channel == 0:
                block_map.append(0)
                continue

            local_bits_count = 0

            for i in range(block.shape[0]):
                for j in range(block.shape[1]):
                    for c in range(3):
                        for b in range(bits_per_channel):
                            if bit_idx >= len(bits):
                                break
                            mask = 0xFF ^ (1 << b)
                            modified[i, j, c] = (int(modified[i, j, c]) & mask) | (int(bits[bit_idx]) << b)
                            bit_idx += 1
                            local_bits_count += 1

            if rmse_block(block, modified) <= RMSE_LIMIT:
                data[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE] = modified
                block_map.append(bits_per_channel)
            else:
                bit_idx -= local_bits_count
                block_map.append(0)


    if bit_idx < len(bits):
        return (1, bit_idx / len(bits))

    save_image(data, output_path)

    # ---- сохраняем карту блоков ----
    with open(output_path, "ab") as f:
        f.write(MAGIC)
        f.write(struct.pack(">I", len(block_map)))
        f.write(bytes(block_map))

    return (0, None)

# ----------------- Извлечение данных -----------------
def extract_lsb(image_path: str):
    # ---- читаем карту ----
    with open(image_path, "rb") as f:
        data = f.read()

    marker = MAGIC
    idx = data.rfind(marker)
    if idx == -1:
        raise ValueError("No map found")

    map_start = idx + len(marker)
    map_len = struct.unpack(">I", data[map_start:map_start+4])[0]
    block_map = list(data[map_start+4:map_start+4+map_len])

    # ---- читаем изображение ----
    img = load_image(image_path)
    h, w, _ = img.shape

    bits = ""
    map_idx = 0

    for y in range(0, h, BLOCK_SIZE):
        for x in range(0, w, BLOCK_SIZE):
            bits_per_channel = block_map[map_idx]
            map_idx += 1

            if bits_per_channel == 0:
                continue

            block = img[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE]

            for i in range(block.shape[0]):
                for j in range(block.shape[1]):
                    for c in range(3):
                        for b in range(bits_per_channel):
                            bits += str((block[i, j, c] >> b) & 1)

    # ---- читаем размер ----
    size_bytes = bits_to_bytes(bits[:32])
    size = struct.unpack(">I", size_bytes)[0]

    payload_bits = bits[32:32 + size * 8]
    return bits_to_bytes(payload_bits)

# ----------------- Максимальная вместимость -----------------
def max_capacity(image_path):
    img = load_image(image_path)
    h, w, _ = img.shape
    bits = 0
    for y in range(0, h, BLOCK_SIZE):
        for x in range(0, w, BLOCK_SIZE):
            block = img[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE]
            var = local_variance(block)
            if var < VAR_LOW:
                bits_per_channel = 0
            elif var < VAR_HIGH:
                bits_per_channel = 1
            else:
                bits_per_channel = 2
            bits += block.shape[0] * block.shape[1] * 3 * bits_per_channel
    return {
        "bits": bits,
        "bytes": bits // 8,
        "symbols": bits // 8  # можно грубо приравнять байт к символу
    }

# ----------------- Визуализация -----------------
def visualize_lsb_blocks(image_path: str, output_path: str, colors:dict, strength=0.25):
    # ---- читаем карту ----
    with open(image_path, "rb") as f:
        raw = f.read()

    marker = MAGIC
    idx = raw.rfind(marker)
    if idx == -1:
        raise ValueError("No map found")

    map_start = idx + len(marker)
    map_len = struct.unpack(">I", raw[map_start:map_start+4])[0]
    block_map = list(raw[map_start+4:map_start+4+map_len])

    # ---- читаем изображение ----
    img = load_image(image_path)
    h, w, _ = img.shape

    result = img.astype(np.float32)
    map_idx = 0

    for y in range(0, h, BLOCK_SIZE):
        for x in range(0, w, BLOCK_SIZE):
            if map_idx >= len(block_map):
                raise ValueError("Corrupted block map")

            bits_per_channel = block_map[map_idx]
            map_idx += 1

            if bits_per_channel not in colors:
                continue

            block = result[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE]

            target_color = colors[bits_per_channel]

            # мягкое смешивание цвета
            block[:] = block * (1 - strength) + target_color * strength

    # клип и сохранение
    result = np.clip(result, 0, 255).astype(np.uint8)
    save_image(result, output_path)

def get_visualized_lsb_blocks(image_path: str):
    visualize_lsb_blocks(image_path, f"{image_path}_output.png", {
    0: np.array([255, 000, 0]),
    1: np.array([255, 255, 0]),
    2: np.array([000, 255, 0]),
    3: np.array([000, 000, 0]),
    }, 0.5)

    visualize_lsb_blocks(image_path, f"{image_path}_output_0.png", {
    0: np.array([255, 0, 0]),
    1: np.array([000, 0, 0]),
    2: np.array([000, 0, 0]),
    3: np.array([000, 000, 0]),
    }, 0.5)

    visualize_lsb_blocks(image_path, f"{image_path}_output_1.png", {
    0: np.array([000, 000, 0]),
    1: np.array([255, 255, 0]),
    2: np.array([000, 000, 0]),
    3: np.array([000, 000, 0]),
    }, 0.5)

    visualize_lsb_blocks(image_path, f"{image_path}_output_2.png", {
    0: np.array([0, 000, 0]),
    1: np.array([0, 000, 0]),
    2: np.array([0, 255, 0]),
    3: np.array([000, 000, 0]),
    }, 0.5)

    return (f"{image_path}_output_0.png", f"{image_path}_output_1.png", f"{image_path}_output_2.png", f"{image_path}_output.png")

