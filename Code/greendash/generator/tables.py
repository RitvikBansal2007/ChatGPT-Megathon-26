import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

from .latent import make_latent
from .merchants import noisy_string, TEMPLATES

rng = np.random.default_rng(42)
CUTOFF_DATE = datetime(2026, 6, 30)

ROOT = Path(__file__).resolve().parent.parent.parent

def generate_customers(latent, n=5000):
    ids = [f"CUST-{i:04d}" for i in range(1, n + 1)]
    ages = rng.integers(18, 80, size=n)
    income_bands = rng.choice(["<20k", "20k-40k", "40k-60k", "60k-80k", "80k+"], size=n)
    postcodes = [f"XX{rng.integers(1,99)} {rng.integers(1,9)}XX" for _ in range(n)]
    
    home_owner = (latent["financial_headroom"] > 0) | (rng.random(n) < 0.4)
    digital_usage = latent["digital_propensity"]
    sustainability_preference = np.clip(latent["green_affinity"] + rng.normal(0, 0.1, n), 0, 1)
    
    regions = rng.choice(["London", "South East", "North West", "West Midlands", "South West"], size=n)
    
    return pd.DataFrame({
        "customer_id": ids,
        "customer_key": range(1, n + 1),
        "age": ages,
        "income_band": income_bands,
        "postcode": postcodes,
        "region": regions,
        "home_owner": home_owner,
        "digital_usage": digital_usage,
        "sustainability_preference": sustainability_preference,
        "is_persona": False,
        "epc_band": rng.choice(["A", "B", "C", "D", "E"], size=n),
        "roof_suitability": rng.choice(["suitable", "unsuitable", "unknown"], p=[0.4, 0.2, 0.4], size=n),
        "existing_solar": rng.random(n) < 0.05,
        "accessibility_paper_need": rng.random(n) < 0.02
    })

def generate_vehicles(customers, latent):
    n = len(customers)
    has_car = rng.random(n) < 0.8
    
    fuel_types = np.where(latent["green_affinity"] > 0.7, 
                          rng.choice(["bev", "hybrid", "petrol"], p=[0.4, 0.3, 0.3], size=n),
                          rng.choice(["petrol", "diesel", "hybrid", "bev"], p=[0.58, 0.35, 0.05, 0.02], size=n))
    
    df = pd.DataFrame({
        "customer_id": customers["customer_id"],
        "has_car": has_car,
        "vehicle_type": "car",
        "fuel_type": fuel_types,
        "vehicle_age": rng.integers(1, 15, size=n),
        "annual_mileage": rng.integers(2000, 15000, size=n),
        "status": "owned",
        "updated_at": pd.Timestamp(CUTOFF_DATE - timedelta(days=10))
    })
    return df[df["has_car"]].drop(columns=["has_car"]).reset_index(drop=True)

def generate_energy_usage(customers, latent):
    n = len(customers)
    rows = []
    
    for i, row in customers.iterrows():
        cid = row["customer_id"]
        base_elec = 2700 / 12 * (1 + latent["financial_headroom"][i]*0.1)
        base_gas = 11500 / 12 if row["home_owner"] else 8000 / 12
        
        for m in range(1, 13):
            month_date = CUTOFF_DATE - timedelta(days=30*m)
            is_winter = month_date.month in [11, 12, 1, 2]
            gas_kwh = base_gas * (1.5 if is_winter else 0.6) + rng.normal(0, base_gas*0.1)
            elec_kwh = base_elec + rng.normal(0, base_elec*0.1)
            
            rows.append({
                "customer_id": cid,
                "month": pd.Timestamp(month_date.strftime("%Y-%m-01")),
                "electricity_kwh": max(0, elec_kwh),
                "gas_kwh": max(0, gas_kwh)
            })
            
    return pd.DataFrame(rows)

def generate_transactions(customers, latent):
    n = len(customers)
    n_trans = 10
    total_trans = n * n_trans
    
    cids = np.repeat(customers["customer_id"].values, n_trans)
    dates = [CUTOFF_DATE - timedelta(days=int(d)) for d in rng.integers(1, 365, size=total_trans)]
    templates = rng.choice(TEMPLATES, size=total_trans)
    
    merchants = [noisy_string(t, rng) for t in templates]
    categories = [t.true_category for t in templates]
    amounts = [rng.uniform(t.amount_range[0], t.amount_range[1]) for t in templates]
    
    df = pd.DataFrame({
        "transaction_id": [f"TXN-{i:06d}" for i in range(1, total_trans + 1)],
        "customer_id": cids,
        "date": pd.to_datetime([d.strftime("%Y-%m-%d") for d in dates]),
        "merchant_description": merchants,
        "amount": amounts,
        "debit_credit": "debit",
        "true_category": categories
    })
    return df

def generate_digital_usage(customers, latent):
    n = len(customers)
    rows = []
    for i, row in customers.iterrows():
        cid = row["customer_id"]
        dp = latent["digital_propensity"][i]
        
        for m in range(1, 4):
            month_date = CUTOFF_DATE - timedelta(days=30*m)
            
            digital_statements = 1 if dp > 0.5 else 0
            paper_statements = 1 - digital_statements
            digital_txns = int(dp * rng.integers(10, 50))
            branch_visits = int((1 - dp) * rng.integers(0, 3))
            
            rows.append({
                "customer_id": cid,
                "month": pd.Timestamp(month_date.strftime("%Y-%m-01")),
                "digital_statements": digital_statements,
                "paper_statements": paper_statements,
                "digital_transactions": digital_txns,
                "branch_visits": branch_visits
            })
    return pd.DataFrame(rows)

def generate_products(customers, latent):
    n = len(customers)
    rows = []
    for i, row in customers.iterrows():
        cid = row["customer_id"]
        
        rows.append({
            "customer_id": cid,
            "product": "current_account",
            "start_date": pd.Timestamp((CUTOFF_DATE - timedelta(days=int(rng.integers(100, 2000)))).strftime("%Y-%m-%d")),
            "end_date": pd.NaT,
            "balance": max(0, rng.normal(1500, 500) + latent["financial_headroom"][i]*1000),
            "status": "ACTIVE"
        })
        
        if latent["car_finance_ending"][i]:
            rows.append({
                "customer_id": cid,
                "product": "car_finance",
                "start_date": pd.Timestamp((CUTOFF_DATE - timedelta(days=int(365*3 - 60))).strftime("%Y-%m-%d")),
                "end_date": pd.Timestamp((CUTOFF_DATE + timedelta(days=60)).strftime("%Y-%m-%d")),
                "balance": 1500.0,
                "status": "ACTIVE"
            })
            
        if row["home_owner"] and rng.random() < 0.3:
            rows.append({
                "customer_id": cid,
                "product": "mortgage",
                "start_date": pd.Timestamp((CUTOFF_DATE - timedelta(days=int(rng.integers(100, 2000)))).strftime("%Y-%m-%d")),
                "end_date": pd.NaT,
                "balance": max(0, rng.normal(150000, 50000)),
                "status": "ACTIVE"
            })
            
    return pd.DataFrame(rows)

def generate_green_products():
    return pd.DataFrame([
        {"product_id": "GP01", "product": "EV Finance", "category": "Transport", "eligibility": "Existing vehicle, good credit", "sustainability_metric": "Emissions Avoided"},
        {"product_id": "GP02", "product": "Green Home Loan", "category": "Home", "eligibility": "Homeowner, high energy usage", "sustainability_metric": "Energy Avoided"},
        {"product_id": "GP03", "product": "Solar Finance", "category": "Home", "eligibility": "Homeowner, suitable roof", "sustainability_metric": "Energy Avoided"},
        {"product_id": "GP04", "product": "Paperless Banking", "category": "Digital", "eligibility": "Paper statements active", "sustainability_metric": "Paper Sheets Avoided"},
    ])

def generate_emissions_factors():
    return pd.read_csv(ROOT / "config" / "factors.csv")

def build_all_tables(n=5000):
    latent = make_latent(n, rng)
    customers = generate_customers(latent, n)
    vehicles = generate_vehicles(customers, latent)
    energy_usage = generate_energy_usage(customers, latent)
    transactions = generate_transactions(customers, latent)
    digital_usage = generate_digital_usage(customers, latent)
    products = generate_products(customers, latent)
    green_products = generate_green_products()
    factors = generate_emissions_factors()
    
    return {
        "latent": latent,
        "customers": customers,
        "vehicles": vehicles,
        "energy": energy_usage,
        "transactions": transactions,
        "digital": digital_usage,
        "products": products,
        "green_products": green_products,
        "emissions_factors": factors
    }
