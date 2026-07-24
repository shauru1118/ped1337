import struct
from typing import List, Optional, Tuple

import numpy as np

from ..config import StegoConfig
from .variance_analyzer import VarianceAnalyzer


class LSBEmbedder:
    """Embeds bit sequences into image pixel matrices using adaptive LSB modification."""

    def __init__(self, config: StegoConfig, analyzer: VarianceAnalyzer):
        self.config = config
        self.analyzer = analyzer

    @staticmethod
    def bytes_to_bits(data: bytes) -> np.ndarray:
        return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

    @staticmethod
    def _write_bits_into_block(
        modified: np.ndarray, bits: np.ndarray, bit_idx: int, bpc: int
    ) -> tuple[int, int]:
        """Write payload bits into a block. Returns (bits_written, new_bit_idx)."""
        vals = modified.reshape(-1)
        n_vals = int(vals.size)
        remaining = int(bits.size) - bit_idx
        if remaining <= 0 or bpc <= 0 or n_vals == 0:
            return 0, bit_idx

        if bpc == 1:
            take = min(n_vals, remaining)
            chunk = bits[bit_idx : bit_idx + take]
            vals[:take] = (vals[:take] & np.uint8(0xFE)) | chunk.astype(
                np.uint8, copy=False
            )
            return take, bit_idx + take

        # bpc == 2: for each channel byte write bit0 then bit1 (matches nested loops).
        full_pairs = min(n_vals, remaining // 2)
        written = 0
        if full_pairs:
            chunk = bits[bit_idx : bit_idx + full_pairs * 2].reshape(full_pairs, 2)
            new_lsb = chunk[:, 0].astype(np.uint8, copy=False) | (
                chunk[:, 1].astype(np.uint8, copy=False) << np.uint8(1)
            )
            vals[:full_pairs] = (vals[:full_pairs] & np.uint8(0xFC)) | new_lsb
            written = full_pairs * 2
            bit_idx += written
            remaining -= written

        # Odd leftover bit → only LSB0 of the next byte (bit1 stays original).
        if remaining == 1 and full_pairs < n_vals:
            vals[full_pairs] = (vals[full_pairs] & np.uint8(0xFE)) | np.uint8(
                bits[bit_idx]
            )
            written += 1
            bit_idx += 1

        return written, bit_idx

    def embed(
        self, image: np.ndarray, payload: bytes
    ) -> Tuple[np.ndarray, List[int], Tuple[int, Optional[float]]]:
        h, w, _ = image.shape
        bs = self.config.block_size

        payload_header = struct.pack(">I", len(payload)) + payload
        bits = self.bytes_to_bits(payload_header)
        bit_idx = 0
        n_bits = int(bits.size)

        data = image.copy()
        block_map: List[int] = []
        bpc_grid, nh, nw = self.analyzer.compute_bpc_grid(data)

        for by, y in enumerate(range(0, h, bs)):
            for bx, x in enumerate(range(0, w, bs)):
                if bit_idx >= n_bits:
                    block_map.append(3)
                    continue

                y2 = min(y + bs, h)
                x2 = min(x + bs, w)
                block = data[y:y2, x:x2]
                is_full = (y2 - y == bs) and (x2 - x == bs) and by < nh and bx < nw
                if is_full:
                    bpc = int(bpc_grid[by, bx])
                else:
                    bpc = self.analyzer.determine_bits_per_channel(block)

                if bpc == 0:
                    block_map.append(0)
                    continue

                modified = block.copy()
                written, new_idx = self._write_bits_into_block(
                    modified, bits, bit_idx, bpc
                )

                if written == 0:
                    block_map.append(0)
                    continue

                if (
                    self.analyzer.calculate_rmse(block, modified)
                    <= self.config.rmse_limit
                ):
                    data[y:y2, x:x2] = modified
                    block_map.append(bpc)
                    bit_idx = new_idx
                else:
                    block_map.append(0)

        if bit_idx < n_bits:
            return data, block_map, (1, bit_idx / n_bits)

        return data, block_map, (0, None)
