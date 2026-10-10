import json
from datetime import date
import pandas as pd
import pytest
from greenproof.features.build import build_features

CUT = date(2026, 6, 30)

def tiny_raw():
    d = pd.Timestamp
    return {
        "customers": pd.DataFrame({"customer_id": ["CUST-0001", "CUST-0002"], "customer_key": ["k1", "k2"],
            "is_persona": [True, False], "age": [40, 30], "income_band": ["B", "C"], "region": ["N", "S"],
            "postcode": ["X1", "Y2"], "home_owner": [True, False], "digital_usage": [0.5, 0.5],
            "sustainability_preference": [0.5, 0.5], "epc_band": ["D", "C"], "roof_suitability": [None, None],
            "existing_solar": [False, False], "accessibility_paper_need": [False, False],
            "updated_at": [d("2026-05-01")] * 2}),
        "transactions": pd.DataFrame({"transaction_id": ["t1", "t2"], "customer_id": ["CUST-0001"] * 2,
            "date": [d("2026-06-01"), d("2026-06-15")], "merchant_description": ["SHELL 1", "SHELL 2"],
            "amount": [60.0, 60.0], "debit_credit": ["D", "D"], "category": ["Fuel", "Fuel"]}),
        "products": pd.DataFrame({"customer_id": [], "product": [], "start_date": pd.to_datetime([]),
                                  "end_date": pd.to_datetime([]), "balance": [], "status": []}),
        "vehicles": pd.DataFrame({"customer_id": ["CUST-0001"], "vehicle_type": ["car"], "fuel_type": ["petrol"],
                                  "vehicle_age": [8], "annual_mileage": [11000.0], "status": ["owned"],
                                  "updated_at": [d("2026-05-01")]}),
        "energy": pd.DataFrame({"customer_id": ["CUST-0001"], "month": [d("2026-05-01")],
                                "electricity_kwh": [250.0], "gas_kwh": [600.0]}),
        "digital": pd.DataFrame({"customer_id": ["CUST-0001"], "month": [d("2026-05-01")], "digital_statements": [0],
                                 "paper_statements": [1], "digital_transactions": [10], "branch_visits": [0]}),
    }

def test_rows_after_cutoff_never_change_features():
    clean = tiny_raw()
    poisoned = tiny_raw()
    d = pd.Timestamp
    poisoned["transactions"] = pd.concat([poisoned["transactions"], pd.DataFrame({
        "transaction_id": ["leak"], "customer_id": ["CUST-0001"], "date": [d("2026-07-15")],
        "merchant_description": ["SHELL 99"], "amount": [99999.0], "debit_credit": ["D"], "category": ["Fuel"]})])
    poisoned["energy"] = pd.concat([poisoned["energy"], pd.DataFrame({
        "customer_id": ["CUST-0001"], "month": [d("2026-07-01")], "electricity_kwh": [9e6], "gas_kwh": [9e6]})])
    a, _ = build_features(clean, CUT)
    b, _ = build_features(poisoned, CUT)
    pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True))

def test_labels_are_not_in_the_feature_table():
    feats, _ = build_features(tiny_raw(), CUT)
    assert not any(c.startswith("take_up") or c == "label" for c in feats.columns)

def test_sensitive_columns_are_not_model_inputs():
    feats, audit = build_features(tiny_raw(), CUT)
    for c in ("age", "income_band", "region", "postcode"):
        assert c not in feats.columns and (c in audit.columns or c == "postcode")

@pytest.mark.skipif(not __import__("pathlib").Path("out/splits.json").exists(), reason="run make train first")
def test_splits_are_disjoint_and_exclude_personas():
    s = json.load(open("out/splits.json"))
    tr, va, te, pe = set(s["train"]), set(s["validation"]), set(s["test"]), set(s["personas"])
    assert not (tr & va) and not (tr & te) and not (va & te)
    assert not (pe & (tr | va | te))
