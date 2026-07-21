from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, List


class IStegoEngine(ABC):
    """Core Steganography Engine Interface."""

    @abstractmethod
    def embed(
        self, image_path: str, output_path: str, payload: bytes
    ) -> Tuple[int, Optional[float]]:
        """Embeds raw payload into image. Returns (status_code, overflow_percentage)."""
        pass

    @abstractmethod
    def extract(self, image_path: str) -> bytes:
        """Extracts raw payload from image."""
        pass

    @abstractmethod
    def calculate_capacity(self, image_path: str) -> Dict[str, int]:
        """Calculates image capacity metrics (bits, bytes, symbols)."""
        pass


class IVisualizer(ABC):
    """Interface for generating block allocation visualization overlays."""

    @abstractmethod
    def visualize(
        self,
        image_path: str,
        output_path: str,
        colors: Dict[int, List[int]],
        strength: float = 0.5,
    ) -> str:
        """Generates a single color overlay image."""
        pass

    @abstractmethod
    def generate_all_views(self, image_path: str) -> Tuple[str, str, str, str]:
        """Generates all 4 visual overlay images."""
        pass
