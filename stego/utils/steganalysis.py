import numpy as np
import math
from typing import List, Dict

def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function (approximation)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def chi2_sf(chi2_val: float, df: int) -> float:
    """Survival function (1 - CDF) of Chi-Square distribution using Wilson-Hilferty approximation."""
    if df <= 0 or chi2_val <= 0:
        return 1.0
    term1 = (chi2_val / df) ** (1.0 / 3.0)
    term2 = 1.0 - (2.0 / (9.0 * df))
    denom = math.sqrt(2.0 / (9.0 * df))
    z = (term1 - term2) / denom
    return normal_cdf(-z)

def calculate_shannon_entropy(lsb_array: np.ndarray) -> float:
    """Calculates the Shannon entropy of the binary LSB array."""
    n_total = len(lsb_array)
    if n_total == 0:
        return 0.0
    n1 = np.sum(lsb_array)
    n0 = n_total - n1
    p0 = n0 / n_total
    p1 = n1 / n_total
    
    entropy = 0.0
    if p0 > 0:
        entropy -= p0 * math.log2(p0)
    if p1 > 0:
        entropy -= p1 * math.log2(p1)
    return entropy

def analyze_channel(channel_data: np.ndarray, num_points: int = 50) -> Dict[str, List[float]]:
    """Performs Chi-Square and Shannon Entropy steganalysis on a single color channel."""
    n_total = len(channel_data)
    step = max(1, n_total // num_points)
    p_values = []
    entropies = []
    
    counts = np.zeros(256, dtype=int)
    lsbs = channel_data & 1
    
    current_index = 0
    for step_idx in range(1, num_points + 1):
        target_index = min(step_idx * step, n_total)
        if target_index > current_index:
            chunk = channel_data[current_index:target_index]
            unique, u_counts = np.unique(chunk, return_counts=True)
            counts[unique] += u_counts
            current_index = target_index
        
        chi2_val = 0.0
        df = 0
        for i in range(128):
            n0 = counts[2 * i]
            n1 = counts[2 * i + 1]
            total = n0 + n1
            if total > 0:
                expected = total / 2.0
                chi2_val += ((n0 - expected) ** 2) / expected
                df += 1
        
        df = df - 1
        p_val = chi2_sf(chi2_val, df) if df > 0 else 0.0
        p_values.append(round(p_val, 4))
        
        entropy_val = calculate_shannon_entropy(lsbs[:target_index])
        entropies.append(round(entropy_val, 4))
        
    return {
        "p_values": p_values,
        "entropies": entropies
    }

def perform_chi_square_analysis(image_array: np.ndarray, num_points: int = 50) -> Dict[str, dict]:
    """
    Performs multi-channel RGB steganalysis.
    """
    r_channel = image_array[:, :, 0].flatten()
    g_channel = image_array[:, :, 1].flatten()
    b_channel = image_array[:, :, 2].flatten()
    
    r_results = analyze_channel(r_channel, num_points)
    g_results = analyze_channel(g_channel, num_points)
    b_results = analyze_channel(b_channel, num_points)
    
    return {
        "red": r_results,
        "green": g_results,
        "blue": b_results
    }
