import math

import numpy as np

from ..config import StegoConfig


class VarianceAnalyzer:
    """Calculates texture variance for image pixel blocks to determine bits per channel."""

    def __init__(self, config: StegoConfig):
        self.config = config

    def calculate_variance(self, block: np.ndarray) -> float:
        return float(np.var(block.astype(np.float32, copy=False)))

    def determine_bits_per_channel(self, block: np.ndarray) -> int:
        var = self.calculate_variance(block)
        if var < self.config.var_low:
            return 0
        if var < self.config.var_high:
            return 1
        return 2

    def calculate_rmse(self, original: np.ndarray, modified: np.ndarray) -> float:
        diff = original.astype(np.float32, copy=False) - modified.astype(
            np.float32, copy=False
        )
        return float(math.sqrt(np.mean(diff * diff)))

    def compute_bpc_grid(self, image: np.ndarray) -> tuple[np.ndarray, int, int]:
        """Vectorized bits-per-channel map for full blocks (H//bs, W//bs)."""
        h, w, _ = image.shape
        bs = self.config.block_size
        nh, nw = h // bs, w // bs
        if nh == 0 or nw == 0:
            return np.zeros((0, 0), dtype=np.uint8), nh, nw

        cropped = image[: nh * bs, : nw * bs]
        blocks = (
            cropped.reshape(nh, bs, nw, bs, 3)
            .swapaxes(1, 2)
            .astype(np.float32, copy=False)
        )
        variances = np.var(blocks, axis=(2, 3, 4))
        bpc = np.zeros(variances.shape, dtype=np.uint8)
        bpc[variances >= self.config.var_low] = 1
        bpc[variances >= self.config.var_high] = 2
        return bpc, nh, nw
