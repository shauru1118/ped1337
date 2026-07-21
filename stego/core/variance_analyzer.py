import math
import numpy as np
from ..config import StegoConfig


class VarianceAnalyzer:
    """Calculates texture variance for image pixel blocks to determine bits per channel."""

    def __init__(self, config: StegoConfig):
        self.config = config

    def calculate_variance(self, block: np.ndarray) -> float:
        return float(np.var(block))

    def determine_bits_per_channel(self, block: np.ndarray) -> int:
        var = self.calculate_variance(block)
        if var < self.config.var_low:
            return 0
        elif var < self.config.var_high:
            return 1
        else:
            return 2

    def calculate_rmse(self, original: np.ndarray, modified: np.ndarray) -> float:
        diff = original.astype(np.float32) - modified.astype(np.float32)
        return math.sqrt(np.mean(diff**2))
