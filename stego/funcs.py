"""Backward compatibility module forwarding to stego OOP package."""
from stego import (
    generate_key,
    load_key,
    encrypt_data,
    decrypt_data,
    embed_lsb,
    extract_lsb,
    max_capacity,
    get_visualized_lsb_blocks,
    visualize_lsb_blocks,
)

__all__ = [
    "generate_key",
    "load_key",
    "encrypt_data",
    "decrypt_data",
    "embed_lsb",
    "extract_lsb",
    "max_capacity",
    "get_visualized_lsb_blocks",
    "visualize_lsb_blocks",
]
