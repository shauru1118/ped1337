"""
GOST R 34.12-2015 "Kuznyechik" Block Cipher Implementation.

This module provides a clean, object-oriented, type-hinted implementation
of the Russian Federal Standard block cipher Kuznyechik (128-bit block size, 256-bit key size).
"""

import pickle
from os.path import dirname, join
from typing import List, Union


class gost2015:
    """
    Kuznyechik Block Cipher (GOST R 34.12-2015).
    
    Provides 128-bit block encryption and decryption using a 256-bit key.
    """

    _multtable_cache = None

    @classmethod
    def _load_multtable(cls):
        if cls._multtable_cache is None:
            tables_path = join(dirname(__file__), "gost_tables")
            with open(tables_path, "rb") as f:
                cls._multtable_cache = pickle.load(f)
        return cls._multtable_cache

    # S-box (Pi table) permutation values
    PI: List[int] = [
        252, 238, 221, 17, 207, 110, 49, 22, 251, 196, 250, 218, 35, 197, 4, 77,
        233, 119, 240, 219, 147, 46, 153, 186, 23, 54, 241, 187, 20, 205, 95, 193,
        249, 24, 101, 90, 226, 92, 239, 33, 129, 28, 60, 66, 139, 1, 142, 79,
        5, 132, 2, 174, 227, 106, 143, 160, 6, 11, 237, 152, 127, 212, 211, 31,
        235, 52, 44, 81, 234, 200, 72, 171, 242, 42, 104, 162, 253, 58, 206, 204,
        181, 112, 14, 86, 8, 12, 118, 18, 191, 114, 19, 71, 156, 183, 93, 135,
        21, 161, 150, 41, 16, 123, 154, 199, 243, 145, 120, 111, 157, 158, 178, 177,
        50, 117, 25, 61, 255, 53, 138, 126, 109, 84, 198, 128, 195, 189, 13, 87,
        223, 245, 36, 169, 62, 168, 67, 201, 215, 121, 214, 246, 124, 34, 185, 3,
        224, 15, 236, 222, 122, 148, 176, 188, 220, 232, 40, 80, 78, 51, 10, 74,
        167, 151, 96, 115, 30, 0, 98, 68, 26, 184, 56, 130, 100, 159, 38, 65,
        173, 69, 70, 146, 39, 94, 85, 47, 140, 163, 165, 125, 105, 213, 149, 59,
        7, 88, 179, 64, 134, 172, 29, 247, 48, 55, 107, 228, 136, 217, 231, 137,
        225, 27, 131, 73, 76, 63, 248, 254, 141, 83, 170, 144, 202, 216, 133, 97,
        32, 113, 103, 164, 45, 43, 9, 91, 203, 155, 37, 208, 190, 229, 108, 82,
        89, 166, 116, 210, 230, 244, 180, 192, 209, 102, 175, 194, 57, 75, 99, 182
    ]

    # Inverse S-box (Pi-Inverse table) values
    PI_INV: List[int] = [
        165, 45, 50, 143, 14, 48, 56, 192, 84, 230, 158, 57, 85, 126, 82, 145,
        100, 3, 87, 90, 28, 96, 7, 24, 33, 114, 168, 209, 41, 198, 164, 63,
        224, 39, 141, 12, 130, 234, 174, 180, 154, 99, 73, 229, 66, 228, 21, 183,
        200, 6, 112, 157, 65, 117, 25, 201, 170, 252, 77, 191, 42, 115, 132, 213,
        195, 175, 43, 134, 167, 177, 178, 91, 70, 211, 159, 253, 212, 15, 156, 47,
        155, 67, 239, 217, 121, 182, 83, 127, 193, 240, 35, 231, 37, 94, 181, 30,
        162, 223, 166, 254, 172, 34, 249, 226, 74, 188, 53, 202, 238, 120, 5, 107,
        81, 225, 89, 163, 242, 113, 86, 17, 106, 137, 148, 101, 140, 187, 119, 60,
        123, 40, 171, 210, 49, 222, 196, 95, 204, 207, 118, 44, 184, 216, 46, 54,
        219, 105, 179, 20, 149, 190, 98, 161, 59, 22, 102, 233, 92, 108, 109, 173,
        55, 97, 75, 185, 227, 186, 241, 160, 133, 131, 218, 71, 197, 176, 51, 250,
        150, 111, 110, 194, 246, 80, 255, 93, 169, 142, 23, 27, 151, 125, 236, 88,
        247, 31, 251, 124, 9, 13, 122, 103, 69, 135, 220, 232, 79, 29, 78, 4,
        235, 248, 243, 62, 61, 189, 138, 136, 221, 205, 11, 19, 152, 2, 147, 128,
        144, 208, 36, 52, 203, 237, 244, 206, 153, 16, 68, 64, 146, 58, 1, 38,
        18, 26, 72, 104, 245, 129, 139, 199, 214, 32, 10, 8, 0, 76, 215, 116
    ]

    # Round constants C for key generation schedule
    C_CONSTANTS: List[List[int]] = [
        [110, 162, 118, 114, 108, 72, 122, 184, 93, 39, 189, 16, 221, 132, 148, 1],
        [220, 135, 236, 228, 216, 144, 244, 179, 186, 78, 185, 32, 121, 203, 235, 2],
        [178, 37, 154, 150, 180, 216, 142, 11, 231, 105, 4, 48, 164, 79, 127, 3],
        [123, 205, 27, 11, 115, 227, 43, 165, 183, 156, 177, 64, 242, 85, 21, 4],
        [21, 111, 109, 121, 31, 171, 81, 29, 234, 187, 12, 80, 47, 209, 129, 5],
        [167, 74, 247, 239, 171, 115, 223, 22, 13, 210, 8, 96, 139, 158, 254, 6],
        [201, 232, 129, 157, 199, 59, 165, 174, 80, 245, 181, 112, 86, 26, 106, 7],
        [246, 89, 54, 22, 230, 5, 86, 137, 173, 251, 161, 128, 39, 170, 42, 8],
        [152, 251, 64, 100, 138, 77, 44, 49, 240, 220, 28, 144, 250, 46, 190, 9],
        [42, 222, 218, 242, 62, 149, 162, 58, 23, 181, 24, 160, 94, 97, 193, 10],
        [68, 124, 172, 128, 82, 221, 216, 130, 74, 146, 165, 176, 131, 229, 85, 11],
        [141, 148, 45, 29, 149, 230, 125, 44, 26, 103, 16, 192, 213, 255, 63, 12],
        [227, 54, 91, 111, 249, 174, 7, 148, 71, 64, 173, 208, 8, 123, 171, 13],
        [81, 19, 193, 249, 77, 118, 137, 159, 160, 41, 169, 224, 172, 52, 212, 14],
        [63, 177, 183, 139, 33, 62, 243, 39, 253, 14, 20, 240, 113, 176, 64, 15],
        [47, 178, 108, 44, 15, 10, 172, 209, 153, 53, 129, 195, 78, 151, 84, 16],
        [65, 16, 26, 94, 99, 66, 214, 105, 196, 18, 60, 211, 147, 19, 192, 17],
        [243, 53, 128, 200, 215, 154, 88, 98, 35, 123, 56, 227, 55, 92, 191, 18],
        [157, 151, 246, 186, 187, 210, 34, 218, 126, 92, 133, 243, 234, 216, 43, 19],
        [84, 127, 119, 39, 124, 233, 135, 116, 46, 169, 48, 131, 188, 194, 65, 20],
        [58, 221, 1, 85, 16, 161, 253, 204, 115, 142, 141, 147, 97, 70, 213, 21],
        [136, 248, 155, 195, 164, 121, 115, 199, 148, 231, 137, 163, 197, 9, 170, 22],
        [230, 90, 237, 177, 200, 49, 9, 127, 201, 192, 52, 179, 24, 141, 62, 23],
        [217, 235, 90, 58, 233, 15, 250, 88, 52, 206, 32, 67, 105, 61, 126, 24],
        [183, 73, 44, 72, 133, 71, 128, 224, 105, 233, 157, 83, 180, 185, 234, 25],
        [5, 108, 182, 222, 49, 159, 14, 235, 142, 128, 153, 99, 16, 246, 149, 26],
        [107, 206, 192, 172, 93, 215, 116, 83, 211, 167, 36, 115, 205, 114, 1, 27],
        [162, 38, 65, 49, 154, 236, 209, 253, 131, 82, 145, 3, 155, 104, 107, 28],
        [204, 132, 55, 67, 246, 164, 171, 69, 222, 117, 44, 19, 70, 236, 255, 29],
        [126, 161, 173, 213, 66, 124, 37, 78, 57, 28, 40, 35, 226, 163, 128, 30],
        [16, 3, 219, 167, 46, 52, 95, 246, 100, 59, 149, 51, 63, 39, 20, 31],
        [94, 167, 216, 88, 30, 20, 155, 97, 241, 106, 193, 69, 156, 237, 168, 32]
    ]

    def __init__(self, key: Union[bytes, List[int]]):
        """
        Initializes the cipher with a 256-bit key.
        
        Args:
            key: Byte array or integer list containing exactly 32 bytes.
        """
        key_list = list(key)
        if len(key_list) != 32:
            raise ValueError("Kuznyechik key must be exactly 32 bytes (256 bits) long.")

        # Precomputed tables for Galois field GF(2^8) arithmetic (cached class-wide)
        self.multtable = self._load_multtable()

        # Initialize round keys schedule
        initial_keys = [key_list[:16], key_list[16:]]
        self.round_keys = initial_keys + self._generate_round_keys(initial_keys)

        # Backward compatibility mapping
        self.roundkey = self.round_keys
        self.pi = self.PI
        self.piinv = self.PI_INV
        self.C = self.C_CONSTANTS

    def add_field(self, x: int, y: int) -> int:
        """Addition in Finite Field GF(2^8) (equivalent to XOR)."""
        return x ^ y

    def sum_field(self, x: List[int]) -> int:
        """Cumulative XOR sum of all elements in the list."""
        s = 0
        for val in x:
            s ^= val
        return s

    def mult_field(self, x: int, y: int) -> int:
        """Galois Field multiplication using irreducible polynomial x^8 + x^7 + x^6 + x + 1."""
        p = 0
        while x:
            if x & 1:
                p ^= y
            if y & 0x80:
                y = (y << 1) ^ 0x1C3
            else:
                y <<= 1
            x >>= 1
        return p

    def xtransformation(self, x: List[int], k: List[int]) -> List[int]:
        """Performs XOR of two byte blocks (X-transformation)."""
        return [x[i] ^ k[i] for i in range(len(k))]

    def pitransformation(self, x: int) -> int:
        """Applies S-box lookup to a single byte."""
        return self.PI[x]

    def piinvtransformation(self, x: int) -> int:
        """Applies inverse S-box lookup to a single byte."""
        return self.PI_INV[x]

    def stransformation(self, x: List[int]) -> List[int]:
        """S-transformation: applies S-box lookup to all bytes in the block."""
        return [self.PI[b] for b in x]

    def sinvtransformation(self, x: List[int]) -> List[int]:
        """Inverse S-transformation: applies inverse S-box lookup to all bytes in the block."""
        return [self.PI_INV[b] for b in x]

    def l(self, x: List[int]) -> int:
        """L-box helper function calculating the Galois Field linear transformation byte."""
        consts = [148, 32, 133, 16, 194, 192, 1, 251, 1, 192, 194, 16, 133, 32, 148, 1]
        multiplication = [self.multtable[x[i]][consts[i]] for i in range(len(x))]
        return self.sum_field(multiplication)

    def rtransformation(self, x: List[int]) -> List[int]:
        """R-transformation: shifts the block and appends the calculated L-transformation byte."""
        return [self.l(x)] + x[:-1]

    def rinvtransformation(self, x: List[int]) -> List[int]:
        """Inverse R-transformation: performs inverse shifting on the block."""
        return x[1:] + [self.l(x[1:] + [x[0]])]

    def ltransformation(self, x: List[int]) -> List[int]:
        """L-transformation: applies full linear transformation to the block."""
        state = list(x)
        for _ in range(len(state)):
            state = self.rtransformation(state)
        return state

    def linvtransformation(self, x: List[int]) -> List[int]:
        """Inverse L-transformation: applies inverse linear transformation to the block."""
        state = list(x)
        for _ in range(len(state)):
            state = self.rinvtransformation(state)
        return state

    def ftransformation(self, k: List[int], a: List[List[int]]) -> List[List[int]]:
        """Feistel-like transformation round used for key generation."""
        tmp = self.xtransformation(k, a[0])
        tmp = self.stransformation(tmp)
        tmp = self.ltransformation(tmp)
        tmp = self.xtransformation(tmp, a[1])
        return [tmp, a[0]]

    def _generate_round_keys(self, initial_keys: List[List[int]]) -> List[List[int]]:
        """Generates all 8 remaining round keys (10 total) based on the first two round keys."""
        round_keys = []
        state = list(initial_keys)
        for i in range(4):
            for k in range(8):
                state = self.ftransformation(self.C_CONSTANTS[8 * i + k], state)
            round_keys.append(state[0])
            round_keys.append(state[1])
        return round_keys

    def keyschedule(self, roundkey: List[List[int]]) -> List[List[int]]:
        """API compatibility method forwarding to the round keys generator."""
        return self._generate_round_keys(roundkey)

    def encryption(self, m: List[int]) -> List[int]:
        """
        Encrypts a single 16-byte block of plaintext.
        
        Args:
            m: Input block of 16 integers (bytes).
            
        Returns:
            Encrypted block of 16 integers (bytes).
        """
        state = list(m)
        for i in range(9):
            state = self.xtransformation(state, self.round_keys[i])
            state = self.stransformation(state)
            state = self.ltransformation(state)
        state = self.xtransformation(state, self.round_keys[9])
        return state

    def decryption(self, c: List[int]) -> List[int]:
        """
        Decrypts a single 16-byte block of ciphertext.
        
        Args:
            c: Input block of 16 integers (bytes).
            
        Returns:
            Decrypted block of 16 integers (bytes).
        """
        state = list(c)
        for i in range(9, 0, -1):
            state = self.xtransformation(state, self.round_keys[i])
            state = self.linvtransformation(state)
            state = self.sinvtransformation(state)
        state = self.xtransformation(state, self.round_keys[0])
        return state


# Keep a global default instance if needed by legacy parts
alg = gost2015([
    177, 203, 115, 159, 219, 251, 146, 61, 147, 181, 41, 86, 199, 32, 27, 192,
    94, 203, 216, 159, 219, 251, 101, 61, 243, 181, 193, 86, 199, 32, 27, 192
])

if __name__ == "__main__":
    print("Testing Kuznyechik implementation...")
    # Example from standard / three rounds validation
    p0 = [38, 108, 39, 171, 99, 196, 138, 238, 139, 33, 16, 72, 26, 190, 248, 255]
    p1 = [38, 110, 39, 171, 99, 196, 138, 238, 139, 33, 16, 72, 26, 190, 248, 255]
    
    c0 = alg.xtransformation(
        alg.ltransformation(alg.xtransformation(alg.ltransformation(alg.xtransformation(p0, alg.roundkey[0])), alg.roundkey[1])),
        alg.roundkey[2]
    )
    c1 = alg.xtransformation(
        alg.ltransformation(alg.xtransformation(alg.ltransformation(alg.xtransformation(p1, alg.roundkey[0])), alg.roundkey[1])),
        alg.roundkey[2]
    )
    print("c0:", c0)
    print("c1:", c1)
    
    dp = alg.xtransformation(
        alg.linvtransformation(alg.linvtransformation(c0)),
        alg.linvtransformation(alg.linvtransformation(c1))
    )
    p1_recovered = alg.xtransformation(p0, dp)
    print("dp:", dp)
    print("p1 (recovered):", p1_recovered)
    assert p1 == p1_recovered, "Recovery match verification failed!"
    print("✅ Kuznyechik standalone tests passed!")
