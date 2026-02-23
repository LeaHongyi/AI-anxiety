from dataclasses import dataclass
from typing import List, Literal

Band = Literal["low", "mid", "high"]

@dataclass(frozen=True)
class NeuroticismResult:
    total: int
    band: Band

def score_neuroticism(items: List[int]) -> NeuroticismResult:
    """
    items: 6 Likert responses, each 1..5
    """
    if len(items) != 6:
        raise ValueError("Neuroticism requires exactly 6 items.")
    if any((x < 1 or x > 5) for x in items):
        raise ValueError("Each neuroticism item must be between 1 and 5.")

    total = sum(items)  # 6..30

    if total <= 14:
        band: Band = "low"
    elif total <= 22:
        band = "mid"
    else:
        band = "high"

    return NeuroticismResult(total=total, band=band)
