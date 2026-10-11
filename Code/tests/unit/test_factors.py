import csv
import pytest
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent.parent
WB = next((ROOT / "data" / "public" / "desnz_ghg_factors").glob("*.xlsx"), None)

@pytest.mark.skipif(WB is None, reason="workbook not downloaded")
def test_each_factor_matches_workbook():
    wb = load_workbook(WB, data_only=True)
    for r in csv.DictReader(open(ROOT / "config" / "factors.csv")):
        cell = wb[r["sheet"]][f'{r["col"]}{r["row"]}'].value
        assert float(cell) == pytest.approx(float(r["kg_co2e_per_unit"]))
