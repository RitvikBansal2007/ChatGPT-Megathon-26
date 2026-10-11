"""Pre-generate and cache model-written explanations for the 8 demo customers.

Needs GEMINI_API_KEY in .env. Paced for free-tier rate limits; cached explanations are
skipped, so it is safe to re-run.  Usage (from Code/):  python scripts/warm.py
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.chdir(Path(__file__).resolve().parents[1])

from api.services import load_customer_packs  # noqa: E402
from config.settings import settings  # noqa: E402

if not (settings.llm_api_key or os.environ.get("GEMINI_API_KEY")):
    print("No GEMINI_API_KEY found (set it in Code/.env). Without a key every explanation uses the "
          "checked fixed wording, so there is nothing to pre-generate.")
    sys.exit(1)

for i in range(1, 9):
    cid = f"CUST-{i:04d}"
    pack = load_customer_packs(cid, cid)
    sources = sorted({o.explanation.source for o in pack.opportunities if o.explanation})
    print(cid, "->", ", ".join(sources) or "no explanation")
    time.sleep(20 if i < 8 else 0)
