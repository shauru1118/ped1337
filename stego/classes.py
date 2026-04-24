import numpy as np
import os
from PIL import Image
import struct
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import math

MAGIC = b"STEGOv1337"

BLOCK_SIZE = 4  # размер блока для анализа дисперсии
RMSE_LIMIT = 3.5  # максимально допустимая ошибка
VAR_LOW = 20  # порог низкой дисперсии
VAR_HIGH = 100  # порог высокой дисперсии


class KeyManager:
    def __init__(self, key_path: str):
        self.key_path = key_path
        self.key = self._load_key()

    def _generate_key(self):
        return self._generate_key(self.key_path)

    def _load_key(self):
        if not os.path.exists(self.key_path):
            return self._generate_key(self.key_path)
        with open(self.key_path, "rb") as f:
            return f.read()

    def __repr__(self):
        return self.key


class Crypter:
    @classmethod
    def encrypt_data(self, data: bytes, key: bytes):
        aes = AESGCM(key)
        nonce = secrets.token_bytes(12)
        ciphertext = aes.encrypt(nonce, data, None)
        return nonce + ciphertext

    @classmethod
    def decrypt_data(self, data: bytes, key: bytes):
        nonce = data[:12]
        ciphertext = data[12:]
        aes = AESGCM(key)
        return aes.decrypt(nonce, ciphertext, None)


class Converter:
    @classmethod
    def bytes_to_bits(self, data: bytes):
        return "".join(f"{b:08b}" for b in data)

    @classmethod
    def bits_to_bytes(self, bits: str):
        return bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))


class Imager:
    @classmethod
    def load_image(image_path: str) -> np.ndarray:
        img = Image.open(image_path).convert("RGB")
        return np.array(img)

    @classmethod
    def save(arr, path):
        Image.fromarray(arr).save(path, "PNG")


class Stego:
    def __init__(self, key_path: str, image_path: str):
        self.key: KeyManager = KeyManager(key_path)
        self.image: np.ndarray = Imager.load_image(image_path)

    # rmse and var
    def _rmse_block(self, original: np.ndarray, modified: np.ndarray):
        diff = original.astype(np.float32) - modified.astype(np.float32)
        return math.sqrt(np.mean(diff**2))

    def _local_variance(self, block: np.ndarray):
        return np.var(block)

    # embed
    def embed_lsb(self, output_path: str, payload: bytes):
        self.image
        h, w, _ = self.image.shape

        payload = struct.pack(">I", len(payload)) + payload
        bits = Converter.bytes_to_bits(payload)
        bit_idx = 0

        data = self.image.copy()
        block_map = []

        for y in range(0, h, BLOCK_SIZE):
            for x in range(0, w, BLOCK_SIZE):
                if bit_idx >= len(bits):
                    block_map.append(3)
                    continue

                block = data[y : y + BLOCK_SIZE, x : x + BLOCK_SIZE].copy()
                modified = block.copy()

                variance = self._local_variance(block)

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
                        for c in range(block.shape[2]):
                            for b in range(bits_per_channel):
                                if bit_idx >= len(bits):
                                    break
                                mask = 0xFF ^ (1 << b)
                                modified[i, j, c] = (int(modified[i, j, c]) & mask) | (
                                    int(bits[bit_idx]) << b
                                )
                                bit_idx += 1
                                local_bits_count += 1

                if self._rmse_block(block, modified) < RMSE_LIMIT:
                    data[y : y + BLOCK_SIZE, x : x + BLOCK_SIZE] = modified
                    block_map.append(bits_per_channel)
                else:
                    bit_idx -= local_bits_count
                    block_map.append(0)

        if bit_idx < len(bits):
            return (1, bit_idx / len(bits))

        Imager.save(data, output_path)

        with open(output_path, "ab") as f:
            f.write(MAGIC)
            f.write(struct.pack(">I", len(block_map)))
            f.write(bytes(block_map))

        return (0, None)
