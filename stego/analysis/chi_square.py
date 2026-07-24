"""Chi-square (Westfeld) LSB steganalysis — OOP API.

High χ² p-value under H₀ (equal PoV pair frequencies) indicates that the LSB
plane looks random — typical evidence of embedding, not of a "clean" image.
"""

from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np


class SteganalysisVerdict(str, Enum):
    CLEAN = "clean"
    ANOMALY = "anomaly"
    DETECTED = "detected"


@dataclass
class SteganalysisThresholds:
    """Heuristic thresholds for the Westfeld χ² attack.

    Primary signal is the final χ² p-value (high ≈ random LSB ≈ embedding).
    LSB entropy alone must not imply stego — natural images often have ~1.0 entropy.
    """

    detected_entropy: float = 0.994
    detected_p: float = 0.3
    anomaly_p: float = 0.1
    soft_anomaly_p: float = 0.01
    anomaly_entropy: float = 0.98


@dataclass
class ChannelAnalysisResult:
    p_values: List[Optional[float]] = field(default_factory=list)
    entropies: List[float] = field(default_factory=list)

    @property
    def final_p_value(self) -> float:
        for value in reversed(self.p_values):
            if value is not None and not math.isnan(value):
                return float(value)
        return 0.0

    @property
    def final_entropy(self) -> float:
        return float(self.entropies[-1]) if self.entropies else 0.0

    def to_dict(self) -> Dict[str, List[Optional[float]]]:
        return {
            "p_values": self.p_values,
            "entropies": self.entropies,
        }


@dataclass
class SteganalysisResult:
    red: ChannelAnalysisResult
    green: ChannelAnalysisResult
    blue: ChannelAnalysisResult
    verdict: SteganalysisVerdict
    max_p: float
    avg_p: float
    max_entropy: float
    avg_entropy: float

    def to_dict(self) -> dict:
        return {
            "results": {
                "red": self.red.to_dict(),
                "green": self.green.to_dict(),
                "blue": self.blue.to_dict(),
            },
            "verdict": self.verdict.value,
            "max_entropy": self.max_entropy,
            "avg_entropy": self.avg_entropy,
            "max_p": self.max_p,
            "avg_p": self.avg_p,
            "channels": {
                "red": {
                    "p_value": self.red.final_p_value,
                    "entropy": self.red.final_entropy,
                },
                "green": {
                    "p_value": self.green.final_p_value,
                    "entropy": self.green.final_entropy,
                },
                "blue": {
                    "p_value": self.blue.final_p_value,
                    "entropy": self.blue.final_entropy,
                },
            },
        }


class ChiSquareMath:
    """Statistical helpers for the Westfeld χ² attack."""

    @staticmethod
    def normal_cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @classmethod
    def chi2_sf(cls, chi2_val: float, df: int) -> float:
        """Survival function P(X ≥ χ²) via Wilson–Hilferty approximation."""
        if df <= 0 or chi2_val < 0:
            return float("nan")
        if chi2_val == 0:
            return 1.0
        term1 = (chi2_val / df) ** (1.0 / 3.0)
        term2 = 1.0 - (2.0 / (9.0 * df))
        denom = math.sqrt(2.0 / (9.0 * df))
        z = (term1 - term2) / denom
        return float(cls.normal_cdf(-z))

    @staticmethod
    def shannon_entropy_bits(lsb_array: np.ndarray) -> float:
        n_total = int(len(lsb_array))
        if n_total == 0:
            return 0.0
        n1 = int(np.sum(lsb_array))
        n0 = n_total - n1
        entropy = 0.0
        for count in (n0, n1):
            if count > 0:
                p = count / n_total
                entropy -= p * math.log2(p)
        return float(entropy)


class ChiSquareChannelAnalyzer:
    """Analyzes a single color channel with progressive χ² + LSB entropy."""

    def __init__(self, math_helper: Optional[ChiSquareMath] = None) -> None:
        self._math = math_helper or ChiSquareMath()

    def analyze(
        self, channel_data: np.ndarray, num_points: int = 50
    ) -> ChannelAnalysisResult:
        flat = np.asarray(channel_data, dtype=np.uint8).ravel()
        n_total = int(flat.size)
        if n_total == 0 or num_points < 1:
            return ChannelAnalysisResult()

        step = max(1, n_total // num_points)
        p_values: List[Optional[float]] = []
        entropies: List[float] = []
        counts = np.zeros(256, dtype=np.int64)
        lsbs = flat & 1
        current_index = 0
        ones = 0

        for step_idx in range(1, num_points + 1):
            target_index = min(step_idx * step, n_total)
            if target_index > current_index:
                chunk = flat[current_index:target_index]
                counts += np.bincount(chunk, minlength=256)
                ones += int(np.sum(lsbs[current_index:target_index]))
                current_index = target_index

            even = counts[0::2]
            odd = counts[1::2]
            totals = even + odd
            mask = totals > 0
            pairs_used = int(np.count_nonzero(mask))
            if pairs_used > 1:
                expected = totals[mask] * 0.5
                diff = even[mask] - expected
                chi2_val = float(np.sum((diff * diff) / expected))
                computed = self._math.chi2_sf(chi2_val, pairs_used - 1)
                p_val: Optional[float] = None if math.isnan(computed) else computed
            else:
                p_val = None
            p_values.append(p_val)

            scanned = target_index
            if scanned == 0:
                entropies.append(0.0)
            else:
                p1 = ones / scanned
                p0 = 1.0 - p1
                entropy = 0.0
                if p0 > 0:
                    entropy -= p0 * math.log2(p0)
                if p1 > 0:
                    entropy -= p1 * math.log2(p1)
                entropies.append(float(entropy))

        return ChannelAnalysisResult(p_values=p_values, entropies=entropies)


class SteganalysisEngine:
    """Multi-channel RGB steganalysis with verdict classification."""

    def __init__(
        self,
        channel_analyzer: Optional[ChiSquareChannelAnalyzer] = None,
        thresholds: Optional[SteganalysisThresholds] = None,
    ) -> None:
        self._analyzer = channel_analyzer or ChiSquareChannelAnalyzer()
        self._thresholds = thresholds or SteganalysisThresholds()

    def analyze(
        self, image_array: np.ndarray, num_points: int = 50
    ) -> SteganalysisResult:
        if image_array.ndim < 3 or image_array.shape[2] < 3:
            raise ValueError("Expected an RGB image array with shape (H, W, 3+).")

        channels = (
            image_array[:, :, 0],
            image_array[:, :, 1],
            image_array[:, :, 2],
        )
        # NumPy releases the GIL in hot loops — parallel channel scans help on large images.
        with ThreadPoolExecutor(max_workers=3) as pool:
            red, green, blue = list(
                pool.map(
                    lambda ch: self._analyzer.analyze(ch, num_points),
                    channels,
                )
            )

        finals_p = [red.final_p_value, green.final_p_value, blue.final_p_value]
        finals_e = [red.final_entropy, green.final_entropy, blue.final_entropy]
        max_p = max(finals_p)
        avg_p = sum(finals_p) / 3.0
        max_entropy = max(finals_e)
        avg_entropy = sum(finals_e) / 3.0

        t = self._thresholds
        if max_p >= t.detected_p and max_entropy >= t.detected_entropy:
            verdict = SteganalysisVerdict.DETECTED
        elif max_p >= t.anomaly_p or (
            max_p >= t.soft_anomaly_p and max_entropy >= t.anomaly_entropy
        ):
            verdict = SteganalysisVerdict.ANOMALY
        else:
            verdict = SteganalysisVerdict.CLEAN

        return SteganalysisResult(
            red=red,
            green=green,
            blue=blue,
            verdict=verdict,
            max_p=max_p,
            avg_p=avg_p,
            max_entropy=max_entropy,
            avg_entropy=avg_entropy,
        )
