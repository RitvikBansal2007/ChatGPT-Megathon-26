import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import yaml

ARTEFACTS = ["data/models", "data/calibration", "out/packs", "data/test_predictions.csv", "data/splits", "out/scenario_results.json",
             "data/features", "data/priors", "config", "greendash/llm/prompts"]

def sha(path: Path) -> str:
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
        df = df.reindex(sorted(df.columns), axis=1)
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype(str)
        return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    files = []
    for a in ARTEFACTS:
        p = Path(a)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files += [f for f in p.rglob("*") if f.is_file() and f.name != ".gitkeep"]
    entries = {str(f): sha(f) for f in sorted(files)}
    dec = yaml.safe_load(open("config/decisions.yaml"))
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    body = {"seed": dec["seed"], "cutoff_date": dec["cutoff_date"], "outcome_window_days": dec["outcome_window_days"],
            "factor_vintage": dec["factor_vintage"], "rules_version": dec["rules_version"],
            "prompt_version": dec["prompt_version"], "artefacts": entries}
    body["manifest_hash"] = "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    body["git_sha"] = git
    Path("out").mkdir(exist_ok=True)
    Path("out/run_manifest.json").write_text(json.dumps(body, indent=1, sort_keys=True))
    print("manifest:", body["manifest_hash"], "|", len(entries), "files")

if __name__ == "__main__":
    main()
