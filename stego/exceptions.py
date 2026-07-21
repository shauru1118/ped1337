class StegoError(Exception):
    """Base exception class for all domain errors in the Steganography system."""


class CapacityExceededError(StegoError):
    """Raised when the payload exceeds maximum embedding capacity of an image."""

    def __init__(self, required_ratio: float):
        message = f"Payload exceeds image capacity. Fits only {round(required_ratio * 100, 2)}%."
        super().__init__(message)
        self.required_ratio = required_ratio


class InvalidKeyError(StegoError):
    """Raised when an invalid AES key format or key file is encountered."""


class CorruptedBlockMapError(StegoError):
    """Raised when the steganography block map is missing or corrupted."""


class TransformationError(StegoError):
    """Raised when data compression or encryption/decryption fails."""
