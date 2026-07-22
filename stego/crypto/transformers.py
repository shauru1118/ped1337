import secrets
import zlib
from typing import List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ..interfaces.crypto import IPayloadTransformer
from ..exceptions import TransformationError, InvalidKeyError


class ZlibTransformer(IPayloadTransformer):
    """Strategy implementation for Zlib data compression/decompression."""

    def __init__(self, level: int = 6):
        self.level = level

    def transform(self, payload: bytes) -> bytes:
        try:
            return zlib.compress(payload, self.level)
        except Exception as e:
            raise TransformationError(f"Zlib compression failed: {e}") from e

    def inverse_transform(self, transformed_payload: bytes) -> bytes:
        try:
            return zlib.decompress(transformed_payload)
        except Exception as e:
            raise TransformationError(f"Zlib decompression failed: {e}") from e


from .kuznechik.gost import gost2015


class KuznyechikCBCTransformer(IPayloadTransformer):
    """
    Strategy implementation for Kuznyechik (GOST R 34.12-2015)
    in CBC mode (GOST R 34.13-2015, section 5.4 "Режим простой замены с зацеплением")
    using a shift register of size m = n * z (default z=2, meaning register size m = 32 bytes).
    """

    BLOCK_SIZE = 16  # n = 16 bytes (128 bits)

    def __init__(self, key: bytes, z: int = 2):
        if not key or len(key) != 32:
            raise InvalidKeyError("Kuznyechik key must be 32 bytes (256 bits).")
        self.key = key
        self.z = z
        self.m = self.BLOCK_SIZE * self.z  # m = n * z
        try:
            self._cipher = gost2015(list(key))
        except Exception as e:
            raise InvalidKeyError(f"Failed to initialize Kuznyechik cipher: {e}")

    def transform(self, payload: bytes) -> bytes:
        try:
            # 1. Apply PKCS#7 padding to align payload to BLOCK_SIZE (16 bytes)
            pad_len = self.BLOCK_SIZE - (len(payload) % self.BLOCK_SIZE)
            padded = payload + bytes([pad_len] * pad_len)

            # 2. Generate random m-byte IV (m = BLOCK_SIZE * z)
            iv = secrets.token_bytes(self.m)
            
            # Initialize shift register R of size z blocks (R_1 = IV)
            r = [list(iv[i*self.BLOCK_SIZE:(i+1)*self.BLOCK_SIZE]) for i in range(self.z)]
            
            ciphertext = bytearray()

            for offset in range(0, len(padded), self.BLOCK_SIZE):
                block = list(padded[offset:offset + self.BLOCK_SIZE])
                # XOR plaintext block with MSB_n(R) which is the first block in our register list
                xored = [b ^ r_val for b, r_val in zip(block, r[0])]
                
                # Encrypt block: C_i = e_K(P_i ^ MSB_n(R_i))
                encrypted_block = self._cipher.encryption(xored)
                ciphertext.extend(encrypted_block)
                
                # Shift register: R_{i+1} = LSB_{m-n}(R_i) || C_i
                r = r[1:] + [encrypted_block]

            encrypted_bytes = iv + bytes(ciphertext)

            # 3. Calculate GOST R 34.13 Section 5.6 MAC
            mac = self._compute_gost_mac(encrypted_bytes)

            return encrypted_bytes + mac
        except Exception as e:
            raise TransformationError(f"Kuznyechik CBC encryption failed: {e}") from e

    def inverse_transform(self, transformed_payload: bytes) -> bytes:
        # Expected size: at least IV (m bytes) + 1 block (16 bytes) + MAC (16 bytes)
        if len(transformed_payload) < self.m + self.BLOCK_SIZE + 16:
            raise TransformationError("Ciphertext payload too short.")
        try:
            # Extract trailing 16-byte MAC
            received_mac = transformed_payload[-16:]
            encrypted_bytes = transformed_payload[:-16]

            # Verify MAC
            expected_mac = self._compute_gost_mac(encrypted_bytes)
            if not secrets.compare_digest(received_mac, expected_mac):
                raise TransformationError("Ошибка проверки имитовставки (данные повреждены или изменены)!")

            iv = encrypted_bytes[:self.m]
            ciphertext = encrypted_bytes[self.m:]

            if len(ciphertext) % self.BLOCK_SIZE != 0:
                raise TransformationError("Invalid ciphertext size.")

            # Initialize shift register R with IV
            r = [list(iv[i*self.BLOCK_SIZE:(i+1)*self.BLOCK_SIZE]) for i in range(self.z)]
            
            plaintext = bytearray()

            for offset in range(0, len(ciphertext), self.BLOCK_SIZE):
                block = list(ciphertext[offset:offset + self.BLOCK_SIZE])
                
                # Decrypt block: d_K(C_i)
                decrypted_block = self._cipher.decryption(block)
                # XOR decrypted block with MSB_n(R)
                plain_block = [d ^ r_val for d, r_val in zip(decrypted_block, r[0])]
                plaintext.extend(plain_block)
                
                # Shift register: R_{i+1} = LSB_{m-n}(R_i) || C_i
                r = r[1:] + [block]

            # Strip PKCS#7 padding
            pad_len = plaintext[-1]
            if pad_len < 1 or pad_len > self.BLOCK_SIZE:
                raise TransformationError("Invalid padding value.")
            for i in range(len(plaintext) - pad_len, len(plaintext)):
                if plaintext[i] != pad_len:
                    raise TransformationError("Invalid padding bytes.")

            return bytes(plaintext[:-pad_len])
        except Exception as e:
            raise TransformationError(f"Kuznyechik CBC decryption failed: {e}") from e

    def _compute_gost_mac(self, data: bytes) -> bytes:
        """
        Computes GOST R 34.13-2015 Section 5.6 Message Authentication Code (MAC)
        for the given data.
        """
        # 1. Derive subkeys K1, K2
        r_list = self._cipher.encryption([0] * 16)
        r_bytes = bytes(r_list)

        def shift_left_1(b: bytes) -> bytes:
            val = int.from_bytes(b, byteorder='big')
            shifted = (val << 1) & 0xffffffffffffffffffffffffffffffff
            return shifted.to_bytes(16, byteorder='big')

        # Derive K1
        msb_r = (r_bytes[0] & 0x80) >> 7
        shifted_r = shift_left_1(r_bytes)
        if msb_r == 0:
            k1 = shifted_r
        else:
            k1 = bytes(a ^ b for a, b in zip(shifted_r, b"\x00"*15 + b"\x87"))

        # Derive K2
        msb_k1 = (k1[0] & 0x80) >> 7
        shifted_k1 = shift_left_1(k1)
        if msb_k1 == 0:
            k2 = shifted_k1
        else:
            k2 = bytes(a ^ b for a, b in zip(shifted_k1, b"\x00"*15 + b"\x87"))

        # 2. Divide data into 16-byte blocks
        block_size = self.BLOCK_SIZE
        blocks = []
        if not data:
            blocks = [b""]
        else:
            for offset in range(0, len(data), block_size):
                blocks.append(data[offset:offset+block_size])

        q = len(blocks)
        c_prev = [0] * 16

        # Process all blocks except the last one
        for i in range(q - 1):
            block = list(blocks[i])
            xored = [b ^ c for b, c in zip(block, c_prev)]
            c_prev = self._cipher.encryption(xored)

        # Process the last block
        last_block = blocks[-1]
        if len(last_block) == block_size:
            k_star = k1
            last_block_padded = last_block
        else:
            k_star = k2
            pad_len = block_size - len(last_block)
            last_block_padded = last_block + b"\x80" + b"\x00" * (pad_len - 1)

        # MAC calculation: e_K(P_q_star ^ C_{q-1} ^ K_star)
        xored_last = [
            p ^ c ^ k
            for p, c, k in zip(last_block_padded, c_prev, k_star)
        ]
        mac = self._cipher.encryption(xored_last)
        return bytes(mac)


# Backward compatibility alias
AESGCMTransformer = KuznyechikCBCTransformer


class CompositePayloadTransformer(IPayloadTransformer):
    """Composite Pattern for chaining multiple payload transformation strategies in sequence."""

    def __init__(self, transformers: List[IPayloadTransformer]):
        self.transformers = transformers

    def transform(self, payload: bytes) -> bytes:
        result = payload
        for t in self.transformers:
            result = t.transform(result)
        return result

    def inverse_transform(self, transformed_payload: bytes) -> bytes:
        result = transformed_payload
        for t in reversed(self.transformers):
            result = t.inverse_transform(result)
        return result
