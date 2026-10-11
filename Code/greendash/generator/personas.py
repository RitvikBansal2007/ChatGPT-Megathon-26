import pandas as pd
import numpy as np
from datetime import datetime, timedelta

CUTOFF_DATE = datetime(2026, 6, 30)

def inject_personas(tables: dict, rng):
    """
    Overwrites CUST-0001 to CUST-0008 in the tables to explicitly match the
    8 golden personas in the PRD.
    """
    customers = tables["customers"]
    transactions = tables["transactions"]
    vehicles = tables["vehicles"]
    energy = tables["energy"]
    products = tables["products"]
    digital = tables["digital"]

    # Persona vehicle records: owners must have a record, non-owners must not.
    need_car = ["CUST-0001", "CUST-0002", "CUST-0003", "CUST-0004", "CUST-0006", "CUST-0008"]
    no_car = ["CUST-0005", "CUST-0007"]
    missing = [c for c in need_car if c not in set(vehicles["customer_id"])]
    if missing:
        add = pd.DataFrame({"customer_id": missing, "vehicle_type": "car", "fuel_type": "petrol",
                            "vehicle_age": 8, "annual_mileage": 9000, "status": "owned",
                            "updated_at": pd.Timestamp(CUTOFF_DATE - timedelta(days=10))})
        vehicles = pd.concat([vehicles, add[vehicles.columns]], ignore_index=True)
    vehicles = vehicles[~vehicles["customer_id"].isin(no_car)].reset_index(drop=True)
    
    # CUST-0001: Priya (GP01 RECOMMEND) - high fuel, 11k miles, 8yr petrol, car finance ending in 74d, homeowner
    customers.loc[customers["customer_id"] == "CUST-0001", ["home_owner", "is_persona", "epc_band"]] = [True, True, "C"]
    vehicles.loc[vehicles["customer_id"] == "CUST-0001", ["fuel_type", "vehicle_age", "annual_mileage"]] = ["petrol", 8, 11500]
    priya_cf = pd.DataFrame([{
        "customer_id": "CUST-0001",
        "product": "car_finance",
        "start_date": pd.Timestamp(CUTOFF_DATE - timedelta(days=365*3 - 74)),
        "end_date": pd.Timestamp(CUTOFF_DATE + timedelta(days=74)),
        "balance": 1500.0,
        "status": "ACTIVE"
    }])
    products = pd.concat([products[~((products["customer_id"] == "CUST-0001") & (products["product"] == "car_finance"))], priya_cf], ignore_index=True)

    # CUST-0002: Marcus (GP01 REVIEW, GP02 ABSTAIN) - vehicle is BEV but has fuel spend, missing energy data
    customers.loc[customers["customer_id"] == "CUST-0002", ["is_persona", "epc_band"]] = [True, None]
    vehicles.loc[vehicles["customer_id"] == "CUST-0002", ["fuel_type"]] = ["BEV"]
    energy = energy[energy["customer_id"] != "CUST-0002"]
    marcus_tx = pd.DataFrame([
        {"transaction_id": f"TX-MARCUS-{i}", "customer_id": "CUST-0002",
         "date": pd.Timestamp(CUTOFF_DATE - timedelta(days=d)),
         "amount": 60.0, "debit_credit": "D", "category": "Fuel", "true_category": "Fuel",
         "merchant_description": "SHELL FUEL STATION"}
        for i, d in enumerate([15, 45, 75])
    ])
    transactions = pd.concat([transactions, marcus_tx], ignore_index=True)

    # CUST-0003: Aisha (GP01, GP03, GP04 RULED_OUT) - BEV owner, has solar, already paperless
    customers.loc[customers["customer_id"] == "CUST-0003", ["is_persona", "existing_solar", "digital_usage"]] = [True, True, 1.0]
    vehicles.loc[vehicles["customer_id"] == "CUST-0003", ["fuel_type"]] = ["BEV"]
    digital.loc[digital["customer_id"] == "CUST-0003", ["paper_statements", "digital_statements"]] = [0, 1]
    # Remove any fuel transactions for Aisha
    transactions = transactions[~((transactions["customer_id"] == "CUST-0003") & (transactions["category"] == "Fuel"))]

    # CUST-0004: Tom (GP04 RECOMMEND) - 6 weeks history, paper statements, no vehicle/energy record
    customers.loc[customers["customer_id"] == "CUST-0004", ["is_persona", "digital_usage"]] = [True, 0.0]
    digital.loc[digital["customer_id"] == "CUST-0004", ["paper_statements", "digital_statements"]] = [1, 0]
    vehicles = vehicles[vehicles["customer_id"] != "CUST-0004"]
    energy = energy[energy["customer_id"] != "CUST-0004"]
    # Remove older transactions for Tom
    tom_txns = transactions[transactions["customer_id"] == "CUST-0004"]
    tom_txns = tom_txns[pd.to_datetime(tom_txns["date"]) > (CUTOFF_DATE - timedelta(days=42))]
    transactions = pd.concat([transactions[transactions["customer_id"] != "CUST-0004"], tom_txns])

    # CUST-0005: Dave (GP02 RECOMMEND) - 1960s semi, high winter gas, EPC D, homeowner
    customers.loc[customers["customer_id"] == "CUST-0005", ["is_persona", "home_owner", "epc_band"]] = [True, True, "D"]
    energy.loc[(energy["customer_id"] == "CUST-0005") & (energy["month"].dt.month.isin([11, 12, 1, 2])), "gas_kwh"] += 2000

    # CUST-0006: Sam (GP03 ABSTAIN) - homeowner, high elec, roof suitability unknown
    customers.loc[customers["customer_id"] == "CUST-0006", ["is_persona", "home_owner", "roof_suitability"]] = [True, True, "unknown"]
    energy.loc[energy["customer_id"] == "CUST-0006", "electricity_kwh"] += 500

    # CUST-0007: Renter (GP02, GP03 RULED_OUT, GP04 RECOMMEND) - flat, high app use, paper statements
    customers.loc[customers["customer_id"] == "CUST-0007", ["is_persona", "home_owner", "digital_usage"]] = [True, False, 0.2]
    digital.loc[digital["customer_id"] == "CUST-0007", ["paper_statements", "digital_statements"]] = [1, 0]

    # CUST-0008: Accessibility (GP04 RULED_OUT) - paper statements, accessibility_paper_need = True
    customers.loc[customers["customer_id"] == "CUST-0008", ["is_persona", "accessibility_paper_need", "digital_usage"]] = [True, True, 0.0]
    digital.loc[digital["customer_id"] == "CUST-0008", ["paper_statements", "digital_statements"]] = [1, 0]
    
    tables["customers"] = customers
    tables["transactions"] = transactions
    tables["vehicles"] = vehicles
    tables["energy"] = energy
    tables["products"] = products
    tables["digital"] = digital
    
    return tables
