import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from greenproof.generator.tables import build_all_tables
from greenproof.generator.personas import inject_personas
from greenproof.generator.labels import generate_labels

def main():
    print("Generating synthetic data...")
    rng = np.random.default_rng(42)
    
    tables = build_all_tables(5000)
    tables = inject_personas(tables, rng)
    
    labels = generate_labels(tables, tables["latent"], rng)
    tables["take_up_labels"] = labels["take_up_labels"]
    tables["transaction_labels"] = labels["transaction_labels"]
    
    out_dir = ROOT / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing to {out_dir}")
    for name, df in tables.items():
        if name == "latent":
            continue
        if "customer_id" in df.columns:
            df = df.sort_values("customer_id")
        path = out_dir / f"{name}.parquet"
        df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
        
    print("Generation complete!")

if __name__ == "__main__":
    main()
