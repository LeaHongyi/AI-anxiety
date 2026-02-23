import json
from pathlib import Path
from typing import Any, Dict, List

def load_interventions(json_path: str) -> Dict[str, Any]:
    p = Path(json_path)
    if not p.exists():
        raise FileNotFoundError(f"Intervention library not found: {json_path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if "interventions" not in data:
        raise ValueError("Invalid library.json: missing 'interventions'")
    return data

def filter_interventions(data: Dict[str, Any], driver: str, band: str) -> List[Dict[str, Any]]:
    all_items = data.get("interventions", [])
    return [x for x in all_items if x.get("driver") == driver and x.get("neuroticism_band") == band]
