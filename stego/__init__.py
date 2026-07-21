<<<<<<< HEAD
from .funcs import *
from .classes import Stego, Crypter
=======
from .config import StegoConfig
from .facade import StegoFacade
from .factory import StegoEngineFactory
from .exceptions import (
    StegoError,
    CapacityExceededError,
    InvalidKeyError,
    CorruptedBlockMapError,
    TransformationError,
)

_facade = StegoFacade()


def generate_key(path: str) -> bytes:
    return _facade.generate_key_file(path)


def load_key(path: str) -> bytes:
    return _facade.load_key(path)


def encrypt_data(data: bytes, key: bytes) -> bytes:
    t = StegoEngineFactory.create_encrypted_compressed_transformer(key)
    return t.transform(data)


def decrypt_data(data: bytes, key: bytes) -> bytes:
    t = StegoEngineFactory.create_encrypted_compressed_transformer(key)
    return t.inverse_transform(data)


def embed_lsb(image_path: str, output_path: str, payload: bytes):
    return _facade.engine.embed(image_path, output_path, payload)


def extract_lsb(image_path: str) -> bytes:
    return _facade.engine.extract(image_path)


def max_capacity(image_path: str):
    return _facade.calculate_capacity(image_path)


def get_visualized_lsb_blocks(image_path: str):
    return _facade.generate_visualization(image_path)


def visualize_lsb_blocks(
    image_path: str, output_path: str, colors: dict, strength: float = 0.25
):
    return _facade.visualizer.visualize(image_path, output_path, colors, strength)


__all__ = [
    "StegoFacade",
    "StegoEngineFactory",
    "StegoConfig",
    "StegoError",
    "CapacityExceededError",
    "InvalidKeyError",
    "CorruptedBlockMapError",
    "TransformationError",
    "generate_key",
    "load_key",
    "encrypt_data",
    "decrypt_data",
    "embed_lsb",
    "extract_lsb",
    "max_capacity",
    "get_visualized_lsb_blocks",
    "visualize_lsb_blocks",
]
>>>>>>> 045529e (v0.2.0 done app; OOP code)
