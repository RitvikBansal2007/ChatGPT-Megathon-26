"""Make the suite runnable from a fresh clone.

Several tests (scenarios, invariance, leakage) read generated files under data/raw and
data/features, which are not committed. If they are missing, build them once with the
same commands as `make data features` (about 20 seconds, fixed seed) instead of failing
with an opaque KeyError.
"""
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
REQUIRED = [
    CODE / "data" / "raw" / "customers.parquet",
    CODE / "data" / "raw" / "transactions.parquet",
    CODE / "data" / "features" / "features.parquet",
    CODE / "data" / "splits" / "splits.json",
]


def _present(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


@pytest.fixture(scope="session", autouse=True)
def generated_data():
    if all(_present(p) for p in REQUIRED):
        return
    for module in ("greendash.generator", "greendash.features"):
        proc = subprocess.run([sys.executable, "-m", module], cwd=CODE,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            pytest.exit(f"Could not generate test data with `python -m {module}`:\n"
                        f"{proc.stdout[-800:]}\n{proc.stderr[-800:]}", returncode=2)
