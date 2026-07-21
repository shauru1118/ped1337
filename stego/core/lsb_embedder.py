import struct
from typing import Tuple, List, Optional
import numpy as np
from ..config import StegoConfig
from .variance_analyzer import VarianceAnalyzer


class LSBEmbedder:
    """Embeds bit sequences into image pixel matrices using adaptive LSB modification."""

    def __init__(self, config: StegoConfig, analyzer: VarianceAnalyzer):
        self.config = config
        self.analyzer = analyzer

    @staticmethod
    def bytes_to_bits(data: bytes) -> str:
        return "".join(f"{b:08b}" for b in data)

    def embed(
        self, image: np.ndarray, payload: bytes
    ) -> Tuple[np.ndarray, List[int], Tuple[int, Optional[float]]]:
        h, w, _ = image.shape
        bs = self.config.block_size

        payload_header = struct.pack(">I", len(payload)) + payload
        bits = self.bytes_to_bits(payload_header)
        bit_idx = 0

        data = image.copy()
        block_map = []

        for y in range(0, h, bs):
            for x in range(0, w, bs):
                if bit_idx >= len(bits):
                    block_map.append(3)
                    continue

                block = data[y : y + bs, x : x + bs].copy()
                modified = block.copy()
                bpc = self.analyzer.determine_bits_per_channel(block)

                if bpc == 0:
                    block_map.append(0)
                    continue

                local_bits_count = 0
                for i in range(block.shape[0]):
                    for j in range(block.shape[1]):
                        for c in range(3):
                            for b in range(bpc):
                                if bit_idx >= len(bits):
                                    break
                                mask = 0xFF ^ (1 << b)
                                modified[i, j, c] = (int(modified[i, j, c]) & mask) | (
                                    int(bits[bit_idx]) << b
                                )
                                bit_idx += 1
                                local_bits_count += 1

                if (
                    self.analyzer.calculate_rmse(block, modified)
                    <= self.config.rmse_limit
                ):
                    data[y : y + bs, x : x + bs] = modified
                    block_map.append(bpc)
                else:
                    bit_idx -= local_bits_count
                    block_map.append(0)

        if bit_idx < len(bits):
            return data, block_map, (1, bit_idx / len(bits))

        return data, block_map, (0, None)
