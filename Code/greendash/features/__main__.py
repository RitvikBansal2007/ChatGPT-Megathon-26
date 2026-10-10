import pandas as pd
from pathlib import Path
import yaml
from datetime import date
from greendash.features.build import build_features

RAW, OUT = Path("data/raw"), Path("data/features")
cutoff = date.fromisoformat(yaml.safe_load(open("config/decisions.yaml"))["cutoff_date"])
raw = {n: pd.read_parquet(RAW / f"{n}.parquet") for n in
       ["customers", "transactions", "products", "vehicles", "energy", "digital"]}
feats, audit = build_features(raw, cutoff)
labels = pd.read_parquet(RAW / "take_up_labels.parquet")
feats = feats.merge(labels, on="customer_id", how="left")
OUT.mkdir(parents=True, exist_ok=True)
feats.sort_values("customer_key").to_parquet(OUT / "features.parquet", index=False)
audit.sort_values("customer_key").to_parquet(OUT / "audit_attrs.parquet", index=False)
print("features:", feats.shape)

from greendash.features.splits import make_splits
splits = make_splits(feats, pd.read_parquet(RAW / "take_up_labels.parquet"))
print({k: len(v) for k, v in splits.items()})
