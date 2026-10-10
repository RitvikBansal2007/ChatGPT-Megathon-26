import json
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

def make_splits(feats: pd.DataFrame, labels: pd.DataFrame, seed: int = 42) -> dict:
    pop = feats[~feats["is_persona"]]
    any_up = labels.set_index("customer_id").max(axis=1)
    y = pop["customer_id"].map(any_up).fillna(0).astype(int)
    train, rest, y_tr, y_rest = train_test_split(pop["customer_id"], y, test_size=0.30, stratify=y, random_state=seed)
    val, test = train_test_split(rest, test_size=0.50, stratify=y_rest, random_state=seed)
    out = {"train": sorted(train), "val": sorted(val), "test": sorted(test),
           "personas": sorted(feats[feats["is_persona"]]["customer_id"])}
    Path("data/splits").mkdir(parents=True, exist_ok=True)
    Path("data/splits/splits.json").write_text(json.dumps(out, sort_keys=True))
    return out
