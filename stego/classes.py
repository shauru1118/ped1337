"""Backward compatibility module forwarding to stego OOP package."""
from stego.facade import StegoFacade as Stego
from stego.crypto.key_manager import FileKeyManager as KeyManager
from stego.crypto.transformers import AESGCMTransformer as Crypter

__all__ = ["Stego", "KeyManager", "Crypter"]
