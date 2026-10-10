import pandas as pd
import pytest
from datetime import date
from greendash.contracts import Mutation
from greendash.features.build import build_features
from greendash.packs import evaluate_customer
from greendash.carbon.engine import load_factors
from greendash.scenarios import run as lab
from greendash.scenarios.mutations import apply_mutations

CUT = date(2026, 6, 30)

@pytest.mark.parametrize("m", list(Mutation))
def test_lab_equals_fresh_run_on_mutated_data(m):
    cid = "CUST-0001"
    resp = lab.run(cid, [m], CUT)
    mutated = apply_mutations(lab.load_customer_rows(cid), [m], CUT)
    feats, _ = build_features(mutated, CUT)
    fresh = evaluate_customer(feats.iloc[0].to_dict(), load_factors(), CUT)
    for pid, o in fresh.items():
        assert resp.after[pid].status == o.status
        assert resp.after[pid].eligibility == o.eligibility.result

def test_lab_never_mutates_stored_data():
    before = lab.load_customer_rows("CUST-0001")["vehicles"].copy()
    lab.run("CUST-0001", [Mutation.SET_VEHICLE_BEV], CUT)
    pd.testing.assert_frame_equal(before, lab.load_customer_rows("CUST-0001")["vehicles"])
