from .config import StegoConfig
from .image.pil_adapter import PILImageAdapter
from .image.block_map import BinaryBlockMapHandler
from .core.engine import StegoEngine
from .visualization.visualizer import StegoVisualizer
from .crypto.key_manager import FileKeyManager
from .crypto.transformers import (
    ZlibTransformer,
    AESGCMTransformer,
    CompositePayloadTransformer,
)


class StegoEngineFactory:
    """Factory Pattern for building Stego Engine, Visualizer, KeyManager, and Transformation Strategies."""

    @staticmethod
    def create_config(**kwargs) -> StegoConfig:
        return StegoConfig(**kwargs)

    @staticmethod
    def create_image_adapter() -> PILImageAdapter:
        return PILImageAdapter()

    @staticmethod
    def create_block_map_handler() -> BinaryBlockMapHandler:
        return BinaryBlockMapHandler()

    @classmethod
    def create_engine(cls, config: StegoConfig = None) -> StegoEngine:
        cfg = config or cls.create_config()
        adapter = cls.create_image_adapter()
        map_handler = cls.create_block_map_handler()
        return StegoEngine(cfg, adapter, map_handler)

    @classmethod
    def create_visualizer(cls, config: StegoConfig = None) -> StegoVisualizer:
        cfg = config or cls.create_config()
        adapter = cls.create_image_adapter()
        map_handler = cls.create_block_map_handler()
        return StegoVisualizer(cfg, adapter, map_handler)

    @staticmethod
    def create_key_manager(default_path: str = None) -> FileKeyManager:
        return FileKeyManager(default_path)

    @staticmethod
    def create_encrypted_compressed_transformer(
        key: bytes,
    ) -> CompositePayloadTransformer:
        return CompositePayloadTransformer(
            [
                ZlibTransformer(),
                AESGCMTransformer(key),
            ]
        )
