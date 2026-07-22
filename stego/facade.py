import struct
from typing import Dict, Tuple, Optional
from .config import StegoConfig
from .factory import StegoEngineFactory
from .interfaces.crypto import IPayloadTransformer
from .exceptions import CapacityExceededError


class StegoFacade:
    """Facade Pattern: Providing a unified, simple, high-level API for all steganography operations."""

    ENVELOPE_SIGNATURE = b"STEGO_ENV_v1"

    def __init__(self, config: Optional[StegoConfig] = None):
        self.config = config or StegoEngineFactory.create_config()
        self.engine = StegoEngineFactory.create_engine(self.config)
        self.visualizer = StegoEngineFactory.create_visualizer(self.config)
        self.key_manager = StegoEngineFactory.create_key_manager()

    def generate_key_file(self, path: str) -> bytes:
        """Generates and saves a new 256-bit AES key to specified path."""
        key = self.key_manager.generate()
        self.key_manager.save(path, key)
        return key

    def load_key(self, path: str) -> bytes:
        """Loads a 256-bit AES key from path."""
        return self.key_manager.load(path)

    def embed_raw(
        self, image_path: str, output_path: str, payload: bytes
    ) -> Tuple[int, Optional[float]]:
        """Embeds raw payload into image."""
        status = self.engine.embed(image_path, output_path, payload)
        if status[0] != 0:
            raise CapacityExceededError(status[1])
        return status

    def embed_encrypted(
        self,
        image_path: str,
        output_path: str,
        data: bytes,
        key: bytes,
        transformer: Optional[IPayloadTransformer] = None,
    ) -> Tuple[int, Optional[float]]:
        """Compresses, encrypts, and embeds payload into image."""
        t = (
            transformer
            or StegoEngineFactory.create_encrypted_compressed_transformer(key)
        )
        encrypted_payload = t.transform(data)
        return self.embed_raw(image_path, output_path, encrypted_payload)

    def extract_raw(self, image_path: str) -> bytes:
        """Extracts raw payload from image."""
        return self.engine.extract(image_path)

    def extract_decrypted(
        self,
        image_path: str,
        key: bytes,
        transformer: Optional[IPayloadTransformer] = None,
    ) -> bytes:
        """Extracts, decrypts, and decompresses payload from image."""
        raw_payload = self.extract_raw(image_path)
        t = (
            transformer
            or StegoEngineFactory.create_encrypted_compressed_transformer(key)
        )
        return t.inverse_transform(raw_payload)

    def calculate_capacity(self, image_path: str) -> Dict[str, int]:
        """Calculates image embedding capacity."""
        return self.engine.calculate_capacity(image_path)

    def generate_visualization(self, image_path: str) -> Tuple[str, str, str, str]:
        """Generates visual analysis maps."""
        return self.visualizer.generate_all_views(image_path)

    @classmethod
    def create_text_envelope(cls, text: str) -> bytes:
        """Creates a structured text envelope."""
        return cls.ENVELOPE_SIGNATURE + b"\x00" + text.encode("utf-8")

    @classmethod
    def create_file_envelope(cls, filename: str, content: bytes) -> bytes:
        """Creates a structured binary file envelope."""
        filename_bytes = filename.encode("utf-8")
        header = cls.ENVELOPE_SIGNATURE + b"\x01" + struct.pack(">H", len(filename_bytes))
        return header + filename_bytes + content

    @classmethod
    def parse_envelope(cls, data: bytes) -> Tuple[str, dict]:
        """Parses envelope structure.

        Returns:
            Tuple[str, dict]: ("text", {"text": str}) or ("file", {"filename": str, "content": bytes})
                              or ("legacy", {"text": str})
        """
        sig_len = len(cls.ENVELOPE_SIGNATURE)
        if len(data) >= sig_len + 1 and data.startswith(cls.ENVELOPE_SIGNATURE):
            mode = data[sig_len]
            payload = data[sig_len + 1:]
            if mode == 0:  # Text mode
                try:
                    return "text", {"text": payload.decode("utf-8")}
                except UnicodeDecodeError:
                    return "legacy", {"text": data.decode("utf-8", errors="replace")}
            elif mode == 1:  # File mode
                if len(payload) >= 2:
                    fn_len = struct.unpack(">H", payload[:2])[0]
                    if len(payload) >= 2 + fn_len:
                        filename = payload[2:2 + fn_len].decode("utf-8", errors="replace")
                        content = payload[2 + fn_len:]
                        return "file", {"filename": filename, "content": content}

        # Legacy fallback
        try:
            return "legacy", {"text": data.decode("utf-8")}
        except UnicodeDecodeError:
            return "legacy", {"text": data.decode("utf-8", errors="replace")}
