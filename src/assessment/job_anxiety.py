from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class JobAnxietyResult:
    total: int
    intensity_0_10: int

def score_job_anxiety(items: List[int]) -> JobAnxietyResult:
    """
    items: 4 Likert responses, each 1..5
    total range: 4..20
    intensity mapping: round((total - 4) / 16 * 10)
    """
    if len(items) != 4:
        raise ValueError("Job anxiety requires exactly 4 items.")
    if any((x < 1 or x > 5) for x in items):
        raise ValueError("Each job anxiety item must be between 1 and 5.")

    total = sum(items)
    intensity = round((total - 4) / 16 * 10)
    intensity = max(0, min(10, intensity))
    return JobAnxietyResult(total=total, intensity_0_10=intensity)
