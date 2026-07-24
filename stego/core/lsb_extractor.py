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
    def bits_to_bytes(bits: np.ndarray) -> bytes:
        if bits.size % 8 != 0:
            pad = 8 - (bits.size % 8)
            bits = np.pad(bits, (0, pad), constant_values=0)
        return np.packbits(bits.astype(np.uint8, copy=False)).tobytes()

    @staticmethod
    def _read_bits_from_block(block: np.ndarray, bpc: int) -> np.ndarray:
        vals = block.reshape(-1).astype(np.uint8, copy=False)
        if bpc == 1:
            return (vals & np.uint8(1)).astype(np.uint8, copy=False)

        # bpc == 2: emit bit0 then bit1 for each channel byte
        out = np.empty(vals.size * 2, dtype=np.uint8)
        out[0::2] = vals & np.uint8(1)
        out[1::2] = (vals >> np.uint8(1)) & np.uint8(1)
        return out

    def extract(self, image: np.ndarray, block_map: List[int]) -> bytes:
        h, w, _ = image.shape
        bs = self.config.block_size

        chunks: List[np.ndarray] = []
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
                chunks.append(self._read_bits_from_block(block, int(bpc)))

        if not chunks:
            raise CorruptedBlockMapError("Extracted bits too short for payload header.")

        bits = np.concatenate(chunks)
        if bits.size < 32:
            raise CorruptedBlockMapError("Extracted bits too short for payload header.")

        size_bytes = self.bits_to_bytes(bits[:32])
        payload_len = struct.unpack(">I", size_bytes)[0]
        needed = 32 + payload_len * 8
        if bits.size < needed:
            raise CorruptedBlockMapError(
                "Extracted bit sequence truncated or corrupted."
            )

        return self.bits_to_bytes(bits[32:needed])
