import json
import shutil
from pathlib import Path

from greendash.contracts import Mutation
from greendash.scenarios.run import run

CACHE = Path("out/cache")

def main() -> None:
    (CACHE / "packs").mkdir(parents=True, exist_ok=True)
    for f in Path("out/packs").glob("*.json"):
        if f.name != "index.json":
            shutil.copy(f, CACHE / "packs" / f.name)

    scen = {}
    for i in range(1, 9):
        cid = f"CUST-{i:04d}"
        for m in Mutation:
            scen[f"{cid}|{m.value}"] = json.loads(run(cid, [m]).model_dump_json(by_alias=True))
    (CACHE / "scenarios.json").write_text(json.dumps(scen, sort_keys=True))
    print("cached packs:", len(list((CACHE / 'packs').glob('*.json'))), "scenarios:", len(scen))

if __name__ == "__main__":
    main()
