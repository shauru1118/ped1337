import struct
from typing import List
from ..interfaces.image import IBlockMapHandler
from ..exceptions import CorruptedBlockMapError


class BinaryBlockMapHandler(IBlockMapHandler):
    """Handles appending and extraction of binary block map metadata attached to stego images."""

    def append(self, path: str, magic_bytes: bytes, block_map: List[int]) -> None:
        try:
            with open(path, "ab") as f:
                f.write(magic_bytes)
                f.write(struct.pack(">I", len(block_map)))
                f.write(bytes(block_map))
        except Exception as e:
            raise CorruptedBlockMapError(
                f"Failed to append block map to {path}: {e}"
            ) from e

    def read(self, path: str, magic_bytes: bytes) -> List[int]:
        try:
            with open(path, "rb") as f:
                data = f.read()

            idx = data.rfind(magic_bytes)
            if idx == -1:
                raise CorruptedBlockMapError(
                    "Magic signature not found in stego container."
                )

            map_start = idx + len(magic_bytes)
            if len(data) < map_start + 4:
                raise CorruptedBlockMapError("Truncated stego block map header.")

            map_len = struct.unpack(">I", data[map_start : map_start + 4])[0]
            if len(data) < map_start + 4 + map_len:
                raise CorruptedBlockMapError("Truncated stego block map payload.")

            return list(data[map_start + 4 : map_start + 4 + map_len])
        except CorruptedBlockMapError:
            raise
        except Exception as e:
            raise CorruptedBlockMapError(
                f"Failed to read block map from {path}: {e}"
            ) from e
