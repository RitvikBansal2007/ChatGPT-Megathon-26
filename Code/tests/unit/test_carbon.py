import pytest
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from greendash.carbon.formulas import ev_switch, green_home_efficiency, solar_install, paperless
from greendash.carbon.units import fmt_kg, fmt_range_kg, fmt_kwh, fmt_sheets
from greendash.carbon.engine import estimate, load_factors

def test_ev_switch_hand_calc():
    saved, text = ev_switch(10_000, 0.30, 0.30, 0.20)
    assert saved == pytest.approx(2400.0)
    assert "annual_miles" in text

def test_green_home_efficiency_hand_calc():
    kwh, saved, text = green_home_efficiency(10000, 0.15, 0.20)
    assert saved == pytest.approx(300.0)
    assert "gas kWh" in text

def test_solar_install_hand_calc():
    kwh, saved, text = solar_install(4.0, 1000.0, 0.20)
    assert saved == pytest.approx(800.0)
    assert "kWp" in text

def test_paperless_hand_calc():
    sheets, text = paperless(12, 3)
    assert sheets == 36
    assert "paper statements" in text

def test_missing_input_is_insufficient():
    factors = load_factors()
    res = estimate({"has_car": True, "annual_mileage": None}, "GP01", factors)
    assert res.status == "INSUFFICIENT_DATA"
    assert "annual_mileage" in res.missing_inputs

def test_display_strings_are_safe():
    assert fmt_kg(1400) == "1,400 kg CO2e"
    assert fmt_range_kg(1000, 2000) == "1,000 to 2,000 kg CO2e per year"
    assert fmt_kwh(3200) == "3,200 kWh"
    assert fmt_sheets(12) == "12 sheets"
