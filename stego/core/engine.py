from typing import Dict, Tuple, Optional
from ..interfaces.stego import IStegoEngine
from ..interfaces.image import IImageAdapter, IBlockMapHandler
from ..config import StegoConfig
from .variance_analyzer import VarianceAnalyzer
from .lsb_embedder import LSBEmbedder
from .lsb_extractor import LSBExtractor


class StegoEngine(IStegoEngine):
    """Implementation of IStegoEngine using Dependency Injection for ImageAdapter and BlockMapHandler."""

    def __init__(
        self,
        config: StegoConfig,
        image_adapter: IImageAdapter,
        block_map_handler: IBlockMapHandler,
    ):
        self.config = config
        self.image_adapter = image_adapter
        self.block_map_handler = block_map_handler
        self.analyzer = VarianceAnalyzer(self.config)
        self.embedder = LSBEmbedder(self.config, self.analyzer)
        self.extractor = LSBExtractor(self.config)

    def calculate_capacity(self, image_path: str) -> Dict[str, int]:
        image = self.image_adapter.load(image_path)
        h, w, _ = image.shape
        total_bits = 0
        bs = self.config.block_size

        for y in range(0, h, bs):
            for x in range(0, w, bs):
                block = image[y : y + bs, x : x + bs]
                bpc = self.analyzer.determine_bits_per_channel(block)
                total_bits += block.shape[0] * block.shape[1] * 3 * bpc

        total_bytes = total_bits // 8
        return {
            "bits": total_bits,
            "bytes": total_bytes,
            "symbols": total_bytes,
        }

    def embed(
        self, image_path: str, output_path: str, payload: bytes
    ) -> Tuple[int, Optional[float]]:
        image = self.image_adapter.load(image_path)
        modified_image, block_map, status = self.embedder.embed(image, payload)

        if status[0] == 0:
            self.image_adapter.save(modified_image, output_path)
            self.block_map_handler.append(
                output_path, self.config.magic_bytes, block_map
            )

        return status

    def extract(self, image_path: str) -> bytes:
        block_map = self.block_map_handler.read(image_path, self.config.magic_bytes)
        image = self.image_adapter.load(image_path)
        return self.extractor.extract(image, block_map)
