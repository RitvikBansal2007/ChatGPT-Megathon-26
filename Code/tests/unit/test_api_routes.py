from fastapi.testclient import TestClient
from types import SimpleNamespace

from api.main import app
from api import deps

def as_role(role, sub="k1"):
    app.dependency_overrides[deps.get_principal] = lambda: SimpleNamespace(role=role, sub=sub)

def test_bad_customer_id_is_422_not_sql():
    as_role("EVALUATOR")
    r = TestClient(app).get("/api/customers/CUST-0001'%3B%20DROP%20TABLE%20users--/opportunities")
    assert r.status_code == 422

def test_analyst_cannot_open_scenario():
    as_role("PORTFOLIO_ANALYST")
    r = TestClient(app).post("/api/scenario", json={"customer_id": "CUST-0001", "mutations": ["SELL_CAR"]})
    assert r.status_code == 403

def test_unknown_fields_are_rejected():
    as_role("EVALUATOR")
    r = TestClient(app).post("/api/scenario", json={"customer_id": "CUST-0001", "mutations": ["SELL_CAR"], "x": 1})
    assert r.status_code == 422
