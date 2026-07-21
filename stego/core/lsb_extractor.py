import struct
from typing import List
import numpy as np
from ..config import StegoConfig
from ..exceptions import CorruptedBlockMapError


class LSBExtractor:
    """Extracts raw payload bit sequences from image pixel matrices using block map allocation."""

    def __init__(self, config: StegoConfig):
        self.config = config

    @staticmethod
    def bits_to_bytes(bits: str) -> bytes:
        return bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))

    def extract(self, image: np.ndarray, block_map: List[int]) -> bytes:
        h, w, _ = image.shape
        bs = self.config.block_size

        bits_list = []
        map_idx = 0

        for y in range(0, h, bs):
            for x in range(0, w, bs):
                if map_idx >= len(block_map):
                    break
                bpc = block_map[map_idx]
                map_idx += 1

                if bpc == 0 or bpc == 3:
                    continue

                block = image[y : y + bs, x : x + bs]
                for i in range(block.shape[0]):
                    for j in range(block.shape[1]):
                        for c in range(3):
                            for b in range(bpc):
                                bits_list.append(str((block[i, j, c] >> b) & 1))

        bits = "".join(bits_list)
        if len(bits) < 32:
            raise CorruptedBlockMapError("Extracted bits too short for payload header.")

        size_bytes = self.bits_to_bytes(bits[:32])
        payload_len = struct.unpack(">I", size_bytes)[0]

        if len(bits) < 32 + payload_len * 8:
            raise CorruptedBlockMapError(
                "Extracted bit sequence truncated or corrupted."
            )

        payload_bits = bits[32 : 32 + payload_len * 8]
        return self.bits_to_bytes(payload_bits)
