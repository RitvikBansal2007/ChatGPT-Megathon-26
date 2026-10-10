import json
from pathlib import Path

from fastapi import HTTPException

from config.settings import settings
from greendash.contracts import CustomerOpportunities

def load_customer_packs(key: str, display_id: str) -> CustomerOpportunities:
    f = Path(f"out/packs/{key}.json")
    if not f.exists() and settings.DEMO_MODE == "fixtures":
        f = Path("fixtures/status.json")
    if not f.exists():
        raise HTTPException(status_code=404, detail="Customer not found")
    data = json.loads(f.read_text())
    import yaml
    from datetime import date
    cfg = yaml.safe_load(Path("config/decisions.yaml").read_text())
    dict_data = {
        "customer_id": display_id,
        "persona": None,
        "opportunities": [v for _, v in sorted(data.items())],
        "cutoff_date": cfg["cutoff_date"],
        "outcome_window_days": cfg["outcome_window_days"],
        "run_manifest": "sha256:352a838558cb95f7961c2d94c4e862ca198bbdb59435c39ad21912452ca9f548"
    }
    return CustomerOpportunities.model_validate_json(json.dumps(dict_data))
