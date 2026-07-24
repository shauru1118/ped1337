"""Backward-compatible procedural wrappers around the OOP steganalysis engine."""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from stego.analysis import SteganalysisEngine


def perform_chi_square_analysis(
    image_array: np.ndarray, num_points: int = 50
) -> Dict[str, Dict[str, List[Optional[float]]]]:
    """Performs multi-channel RGB steganalysis (legacy dict shape)."""
    result = SteganalysisEngine().analyze(image_array, num_points=num_points)
    return result.to_dict()["results"]
