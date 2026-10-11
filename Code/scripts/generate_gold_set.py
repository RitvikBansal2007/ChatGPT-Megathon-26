import sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from greendash.generator.merchants import TEMPLATES, noisy_string

def generate_gold_set():
    rng = np.random.default_rng(42)
    rows = []
    
    # We want ~200 strings total, using random templates
    for _ in range(200):
        tpl = rng.choice(TEMPLATES)
        string_val = noisy_string(tpl, rng)
        rows.append({"string": string_val, "true_category": tpl.true_category})
        
    df = pd.DataFrame(rows)
    out_path = ROOT / "gold_set.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} strings in {out_path}")

if __name__ == "__main__":
    generate_gold_set()
