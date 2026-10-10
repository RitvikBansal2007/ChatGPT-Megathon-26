import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = ROOT / "data" / "eval"

def generate_eval():
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    
    customers = pd.read_parquet(ROOT / "data" / "raw" / "customers.parquet")
    take_up = pd.read_parquet(ROOT / "data" / "raw" / "take_up_labels.parquet")
    
    merged = customers.merge(take_up, on="customer_id")
    
    gp01_pos = merged[merged["take_up_GP01"] == 1].head(3)
    gp01_neg = merged[merged["take_up_GP01"] == 0].head(3)
    
    sample = pd.concat([gp01_pos, gp01_neg])
    
    records = []
    for _, row in sample.iterrows():
        records.append({
            "customer_id": row["customer_id"],
            "profile": {
                "age": row["age"],
                "income_band": row["income_band"],
                "home_owner": bool(row["home_owner"])
            },
            "ground_truth_GP01": int(row["take_up_GP01"])
        })
        
    with open(EVAL_DIR / "prompt_eval.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            
    few_shot = {
        "GP01": [
            {"input": "High mileage petrol, car finance ending", "output": "RECOMMEND"},
            {"input": "Low mileage BEV, no finance", "output": "RULED_OUT"}
        ]
    }
    with open(EVAL_DIR / "few_shot_context.json", "w") as f:
        json.dump(few_shot, f, indent=2)

if __name__ == "__main__":
    generate_eval()
