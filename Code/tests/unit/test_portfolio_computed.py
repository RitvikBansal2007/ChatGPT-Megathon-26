"""Cockpit numbers come from the run's rows, not from the template (hermetic)."""
import json
from pathlib import Path

import pandas as pd

from api.routers import portfolio as pf

ROOT = Path(__file__).resolve().parents[2]


def _rows():
    recs = []
    for i in range(30):                       # region A: 30 customers
        recs.append(dict(customer_key=f"a{i}", product="GP01", region="A", status="RECOMMEND" if i % 2 else "SOFT_SURFACE",
                         propensity=0.4 + i / 100, confidence=0.8, eligibility="ELIGIBLE" if i % 3 else "NEEDS_VERIFICATION",
                         impact_status="ESTIMATED", impact_family="emissions", impact_central=1000.0 + i,
                         impact_low=800.0 + i, impact_high=1200.0 + i, impact_quality="MEDIUM",
                         digital_share=0.2, has_car=True, home_owner=True))
    for i in range(4):                        # region B: too small to show
        recs.append(dict(customer_key=f"b{i}", product="GP01", region="B", status="ABSTAIN", propensity=0.1,
                         confidence=0.3, eligibility="ELIGIBLE", impact_status="INSUFFICIENT_DATA",
                         impact_family=None, impact_central=None, impact_low=None, impact_high=None,
                         impact_quality=None, digital_share=0.9, has_car=False, home_owner=False))
    return pd.DataFrame(recs)


def test_quadrant_cohorts_are_computed_from_rows():
    q = pf._quadrant(_rows())
    shown = [c for c in q["GP01"] if not c.get("suppressed")]
    assert len(shown) == 1 and shown[0]["name"] == "A" and shown[0]["n"] == 30
    c = shown[0]
    assert c["low"] < c["central"] < c["high"]
    assert 0.4 < c["propensity"] < 0.8 and c["conf"] == 0.8
    assert abs(c["eligPass"] + c["eligNeeds"] - 1) < 1e-9
    assert c["quality"] == "MEDIUM"


def test_small_cohorts_are_suppressed_and_carry_no_figures():
    hidden = [c for c in pf._quadrant(_rows())["GP01"] if c["name"] == "B"][0]
    assert hidden["suppressed"] is True and "central" not in hidden and hidden["n"] == 4


def test_segments_ignore_small_groups_and_do_not_mix_families():
    seg = {s["name"]: s for s in pf._segments(_rows())}
    assert "Customers with a car on record" in seg and seg["Customers with a car on record"]["customers"] == 30
    assert "Customers with no car on record" not in seg      # only 4 customers
    assert "kg CO" in seg["Homeowners"]["impact"]


def test_cockpit_template_is_valid_utf8_json():
    """Reading it with the platform default (cp1252 on Windows) used to produce 'COâ‚‚e'."""
    raw = (ROOT / "fixtures" / "portfolio_summary.json").read_bytes()
    text = raw.decode("utf-8")
    assert "\u00e2\u201a" not in text            # no mojibake sequence already baked in
    assert "CO\u2082e" in json.dumps(json.loads(text), ensure_ascii=False)


def test_api_reads_the_template_as_utf8(monkeypatch, tmp_path):
    import os
    monkeypatch.chdir(ROOT)
    src = (ROOT / "api" / "routers" / "portfolio.py").read_text(encoding="utf-8")
    assert 'read_text(encoding="utf-8")' in src and "read_text()" not in src
