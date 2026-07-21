from dataclasses import dataclass

@dataclass
class StegoConfig:
    block_size: int = 4
    rmse_limit: float = 3.5
    var_low: float = 20.0
    var_high: float = 100.0
    magic_bytes: bytes = b"STEGOv1337"
