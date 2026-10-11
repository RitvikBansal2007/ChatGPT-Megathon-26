"""Unit tests for user login, backend JWT auth, customer memory, and portfolio/eval summaries."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from greendash.security.authz import issue_token, verify_token, hash_password, verify_password
from greendash.db import repo

client = TestClient(app)

def test_password_hashing():
    pwd = "secret_password_123"
    h = hash_password(pwd)
    assert h != pwd
    assert verify_password(h, pwd) is True
    assert verify_password(h, "wrong_password") is False

def test_jwt_issuance_and_verification():
    tok = issue_token(role="CUSTOMER", customer_id="CUST-0001", sub="CUST-0001", display_name="Priya")
    payload = verify_token(tok)
    assert payload is not None
    assert payload["role"] == "CUSTOMER"
    assert payload["customer_id"] == "CUST-0001"
    assert payload["display_name"] == "Priya"

def test_login_endpoint_success():
    resp = client.post("/api/auth/login", json={"username": "priya@greenproof.bank", "password": "password123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "CUSTOMER"
    assert data["user"]["customer_id"] == "CUST-0001"

def test_login_endpoint_invalid_password():
    resp = client.post("/api/auth/login", json={"username": "priya@greenproof.bank", "password": "bad_password"})
    assert resp.status_code == 401

def test_demo_token_and_me_endpoint():
    tok_resp = client.post("/api/auth/demo-token", json={"role": "RELATIONSHIP_MANAGER", "customer_id": "rm_user"})
    assert tok_resp.status_code == 200
    token = tok_resp.json()["access_token"]
    
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "RELATIONSHIP_MANAGER"

def test_unauthenticated_request_is_401():
    resp = client.get("/api/portfolio/summary")
    assert resp.status_code == 401

def test_customer_accessing_other_customer_is_403():
    # Customer Priya trying to view Marcus CUST-0002
    priya_tok = client.post("/api/auth/demo-token", json={"role": "CUSTOMER", "customer_id": "CUST-0001"}).json()["access_token"]
    resp = client.get("/api/customers/CUST-0002/opportunities", headers={"Authorization": f"Bearer {priya_tok}"})
    assert resp.status_code == 403

def test_customer_accessing_own_is_200():
    priya_tok = client.post("/api/auth/demo-token", json={"role": "CUSTOMER", "customer_id": "CUST-0001"}).json()["access_token"]
    resp = client.get("/api/customers/CUST-0001/opportunities", headers={"Authorization": f"Bearer {priya_tok}"})
    assert resp.status_code == 200

def test_customer_memory_crud():
    rm_tok = client.post("/api/auth/demo-token", json={"role": "RELATIONSHIP_MANAGER"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {rm_tok}"}
    
    # 1. Get memory
    get_resp = client.get("/api/customers/CUST-0001/memory", headers=headers)
    assert get_resp.status_code == 200
    initial_count = len(get_resp.json()["items"])
    
    # 2. Add memory
    add_resp = client.post("/api/customers/CUST-0001/memory", headers=headers, json={
        "key": "test_goal",
        "value": "Wants to evaluate solar panels next month",
        "category": "goal",
        "source": "rm_note"
    })
    assert add_resp.status_code == 200
    mem_id = add_resp.json()["item"]["id"]
    
    # 3. Check memory was added
    get2_resp = client.get("/api/customers/CUST-0001/memory", headers=headers)
    assert len(get2_resp.json()["items"]) == initial_count + 1
    
    # 4. Delete memory
    del_resp = client.delete(f"/api/customers/CUST-0001/memory/{mem_id}", headers=headers)
    assert del_resp.status_code == 200
    
    # 5. Check memory was removed
    get3_resp = client.get("/api/customers/CUST-0001/memory", headers=headers)
    assert len(get3_resp.json()["items"]) == initial_count

def test_portfolio_summary_structure():
    analyst_tok = client.post("/api/auth/demo-token", json={"role": "PORTFOLIO_ANALYST"}).json()["access_token"]
    resp = client.get("/api/portfolio/summary", headers={"Authorization": f"Bearer {analyst_tok}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "tiles" in data
    assert "funnel" in data
    assert "quadrant" in data
    assert "segments" in data
    assert "regions" in data
    assert "trends" in data
    assert "rm_book" in data

def test_eval_summary_has_measured_and_terciles():
    eval_tok = client.post("/api/auth/demo-token", json={"role": "EVALUATOR"}).json()["access_token"]
    resp = client.get("/api/eval/summary", headers={"Authorization": f"Bearer {eval_tok}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("measured") is True
    terciles = data["terciles"]
    assert len(terciles) == 3
    # Monotonic falling Brier score: Low conf > Mid conf > High conf
    briers = [t["brier"] for t in terciles]
    assert briers[0] > briers[1] > briers[2]
