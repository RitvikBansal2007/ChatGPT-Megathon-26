import json
from pathlib import Path

from fastapi import HTTPException

from config.settings import settings
from greendash.contracts import CustomerPacks

def load_customer_packs(key: str, display_id: str) -> CustomerPacks:
    f = Path(f"out/packs/{key}.json")
    if not f.exists() and settings.DEMO_MODE == "fixtures":
        f = Path("fixtures/status.json")
    if not f.exists():
        raise HTTPException(status_code=404, detail="Customer not found")
    data = json.loads(f.read_text())
    return CustomerPacks(customer_id=display_id, opportunities=[v for _, v in sorted(data.items())])
