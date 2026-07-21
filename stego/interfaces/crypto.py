from abc import ABC, abstractmethod


class IPayloadTransformer(ABC):
    """Strategy pattern interface for payload transformations (compression, encryption, etc.)."""

    @abstractmethod
    def transform(self, payload: bytes) -> bytes:
        """Transforms input payload (e.g., compress or encrypt)."""
        pass

    @abstractmethod
    def inverse_transform(self, transformed_payload: bytes) -> bytes:
        """Reverses transformation (e.g., decompress or decrypt)."""
        pass


class IKeyManager(ABC):
    """Interface for managing key creation, storage, and retrieval."""

    @abstractmethod
    def generate(self) -> bytes:
        pass

    @abstractmethod
    def save(self, path: str, key: bytes) -> None:
        pass

    @abstractmethod
    def load(self, path: str) -> bytes:
        pass
