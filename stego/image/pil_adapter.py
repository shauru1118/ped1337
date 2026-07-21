import numpy as np
from PIL import Image
from ..interfaces.image import IImageAdapter
from ..exceptions import StegoError


class PILImageAdapter(IImageAdapter):
    """Adapter for Pillow image I/O converting between image files and NumPy arrays."""

    def load(self, path: str) -> np.ndarray:
        try:
            img = Image.open(path).convert("RGB")
            return np.array(img)
        except Exception as e:
            raise StegoError(f"Failed to load image from {path}: {e}") from e

    def save(self, array: np.ndarray, path: str) -> None:
        try:
            Image.fromarray(array).save(path, "PNG")
        except Exception as e:
            raise StegoError(f"Failed to save image to {path}: {e}") from e
