import secrets
import zlib
from typing import List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ..interfaces.crypto import IPayloadTransformer
from ..exceptions import TransformationError, InvalidKeyError


class ZlibTransformer(IPayloadTransformer):
    """Strategy implementation for Zlib data compression/decompression."""

    def __init__(self, level: int = 6):
        self.level = level

    def transform(self, payload: bytes) -> bytes:
        try:
            return zlib.compress(payload, self.level)
        except Exception as e:
            raise TransformationError(f"Zlib compression failed: {e}") from e

    def inverse_transform(self, transformed_payload: bytes) -> bytes:
        try:
            return zlib.decompress(transformed_payload)
        except Exception as e:
            raise TransformationError(f"Zlib decompression failed: {e}") from e


class AESGCMTransformer(IPayloadTransformer):
    """Strategy implementation for AES-256-GCM authenticated encryption/decryption."""

    def __init__(self, key: bytes):
        if not key or len(key) != 32:
            raise InvalidKeyError("AES key must be 32 bytes.")
        self.key = key
        self._aes = AESGCM(self.key)

    def transform(self, payload: bytes) -> bytes:
        try:
            nonce = secrets.token_bytes(12)
            ciphertext = self._aes.encrypt(nonce, payload, None)
            return nonce + ciphertext
        except Exception as e:
            raise TransformationError(f"AES-GCM encryption failed: {e}") from e

    def inverse_transform(self, transformed_payload: bytes) -> bytes:
        if len(transformed_payload) < 12:
            raise TransformationError("Ciphertext payload too short.")
        try:
            nonce = transformed_payload[:12]
            ciphertext = transformed_payload[12:]
            return self._aes.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise TransformationError(f"AES-GCM decryption failed: {e}") from e


class CompositePayloadTransformer(IPayloadTransformer):
    """Composite Pattern for chaining multiple payload transformation strategies in sequence."""

    def __init__(self, transformers: List[IPayloadTransformer]):
        self.transformers = transformers

    def transform(self, payload: bytes) -> bytes:
        result = payload
        for t in self.transformers:
            result = t.transform(result)
        return result

    def inverse_transform(self, transformed_payload: bytes) -> bytes:
        result = transformed_payload
        for t in reversed(self.transformers):
            result = t.inverse_transform(result)
        return result
