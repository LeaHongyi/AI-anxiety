from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DimensionResult:
    total: int
    intensity_0_10: int
    count: int


def score_dimension(items: List[int]) -> DimensionResult:
    """
    items: Likert responses, each 1..5
    total range: n..5n
    intensity mapping: round((total - n) / (4n) * 10)
    """
    if not items:
        raise ValueError("Dimension items must not be empty.")
    if any((x < 1 or x > 5) for x in items):
        raise ValueError("Each dimension item must be between 1 and 5.")

    n = len(items)
    total = sum(items)
    intensity = round((total - n) / (4 * n) * 10)
    intensity = max(0, min(10, intensity))
    return DimensionResult(total=total, intensity_0_10=intensity, count=n)
