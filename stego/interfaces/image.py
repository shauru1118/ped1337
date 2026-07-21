from abc import ABC, abstractmethod
from typing import List
import numpy as np


class IImageAdapter(ABC):
    """Adapter pattern interface for loading and saving image pixel matrices."""

    @abstractmethod
    def load(self, path: str) -> np.ndarray:
        """Loads an image from filesystem as an RGB uint8 NumPy array."""
        pass

    @abstractmethod
    def save(self, array: np.ndarray, path: str) -> None:
        """Saves a NumPy array as a lossless image file (e.g. PNG)."""
        pass


class IBlockMapHandler(ABC):
    """Interface for writing and reading binary block maps in stego containers."""

    @abstractmethod
    def append(self, path: str, magic_bytes: bytes, block_map: List[int]) -> None:
        """Appends magic bytes, map size header, and block allocation bytes to image file."""
        pass

    @abstractmethod
    def read(self, path: str, magic_bytes: bytes) -> List[int]:
        """Reads and extracts the block allocation list from image file footer."""
        pass
