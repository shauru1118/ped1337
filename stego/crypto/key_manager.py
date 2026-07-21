import os
import secrets
from ..interfaces.crypto import IKeyManager
from ..exceptions import InvalidKeyError


class FileKeyManager(IKeyManager):
    """File-backed implementation of key manager for 256-bit AES keys."""

    def __init__(self, default_key_path: str = None):
        self.default_key_path = default_key_path

    def generate(self) -> bytes:
        return secrets.token_bytes(32)

    def save(self, path: str, key: bytes) -> None:
        if not key or len(key) != 32:
            raise InvalidKeyError("Key must be exactly 32 bytes.")
        with open(path, "wb") as f:
            f.write(key)

    def load(self, path: str) -> bytes:
        if not os.path.exists(path):
            raise InvalidKeyError(f"Key file not found at: {path}")
        with open(path, "rb") as f:
            key = f.read()
        if len(key) != 32:
            raise InvalidKeyError(
                f"Invalid key length ({len(key)} bytes). Expected 32 bytes."
            )
        return key

    def load_or_create(self, path: str) -> bytes:
        if os.path.exists(path):
            return self.load(path)
        key = self.generate()
        self.save(path, key)
        return key
