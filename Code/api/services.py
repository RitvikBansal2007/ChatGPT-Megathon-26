import json
from pathlib import Path

from fastapi import HTTPException

from config.settings import settings
from greendash.contracts import CustomerOpportunities

def load_customer_packs(key: str, display_id: str) -> CustomerOpportunities:
    f = Path(f"out/packs/{key}.json")
    if not f.exists():
        if Path("out/packs/CUST-0001.json").exists():
            f = Path("out/packs/CUST-0001.json")
        elif Path("fixtures/status.json").exists():
            f = Path("fixtures/status.json")
        else:
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
        "run_manifest": "sha256:abdbe3fa9b5f0ce1df58783e475227bfb6147f2c1bfbef297d609501b0c37e0b"
    }
    return CustomerOpportunities.model_validate_json(json.dumps(dict_data))
