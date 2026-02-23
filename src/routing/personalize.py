from typing import Dict, Any, List

DRIVERS = ("job_loss", "value_threat", "skill_erosion")

def pick_two_actions(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # MVP: deterministic pick first two; later can diversify by tags
    return candidates[:2] if len(candidates) >= 2 else candidates

def route(driver: str, band: str, library_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Inputs:
      driver: job_loss | value_threat | skill_erosion
      band: low | mid | high
      library_data: loaded from src/interventions/library.json

    Output:
      list of 0..2 intervention dicts
    """
    if driver not in DRIVERS:
        raise ValueError(f"Invalid driver: {driver}")
    if band not in ("low", "mid", "high"):
        raise ValueError(f"Invalid band: {band}")

    from interventions.loader import filter_interventions

    candidates = filter_interventions(library_data, driver=driver, band=band)

    # Fallback 1: mid band same driver
    if not candidates and band != "mid":
        candidates = filter_interventions(library_data, driver=driver, band="mid")

    # Fallback 2: any intervention
    if not candidates:
        candidates = library_data.get("interventions", [])

    return pick_two_actions(candidates)
