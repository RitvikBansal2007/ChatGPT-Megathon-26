import hashlib
import datetime
import yaml
import requests
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "ingest" / "sources.yaml"
OUT = ROOT / "data" / "public"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch_one(src: dict) -> Path:
    url = src["url"]
    if not url.startswith("https://"):
        raise ValueError(f"{src['id']}: HTTPS only")
    folder = OUT / src["id"]
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / url.split("/")[-1].split("?")[0]
    
    print(f"Fetching {src['id']} from {url}...")
    try:
        r = requests.get(url, timeout=60, verify=True)
        r.raise_for_status()
        dest.write_bytes(r.content)
    except Exception as e:
        print(f"Failed downloading {src['id']}: {e}")
        raise

    digest = sha256_file(dest)
    if src.get("sha256") and src["sha256"] != digest:
        raise RuntimeError(f"{src['id']}: file changed (hash mismatch). Expected {src['sha256']}, got {digest}")
    
    src["sha256"] = digest
    src["retrieved_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Read-only
    os.chmod(dest, 0o444)
    return dest

def main():
    if not SOURCES.exists():
        print("sources.yaml not found.")
        return
        
    with open(SOURCES, "r") as f:
        sources = yaml.safe_load(f)
        
    for src in sources:
        try:
            fetch_one(src)
        except Exception as e:
            print(f"FAILED {src['id']}: {e}")
            
    with open(SOURCES, "w") as f:
        yaml.safe_dump(sources, f, sort_keys=False)

if __name__ == "__main__":
    main()
