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
    energy = tables["energy_usage"]
    products = tables["products"]
    digital = tables["digital_usage"]
    
    # CUST-0001: Priya (GP01 RECOMMEND) - high fuel, 11k miles, 8yr petrol, car finance ending, homeowner
    customers.loc[customers["customer_id"] == "CUST-0001", ["home_owner", "is_persona", "epc_band"]] = [True, True, "C"]
    vehicles.loc[vehicles["customer_id"] == "CUST-0001", ["fuel_type", "vehicle_age", "annual_mileage"]] = ["petrol", 8, 11500]
    
    # CUST-0002: Marcus (GP01 REVIEW) - vehicle is BEV but has fuel spend, stale EPC
    customers.loc[customers["customer_id"] == "CUST-0002", ["is_persona", "epc_band"]] = [True, "D"]
    vehicles.loc[vehicles["customer_id"] == "CUST-0002", ["fuel_type"]] = ["bev"]
    
    # CUST-0003: Aisha (GP01, GP03, GP04 RULED_OUT) - BEV owner, has solar, already paperless
    customers.loc[customers["customer_id"] == "CUST-0003", ["is_persona", "existing_solar", "digital_usage"]] = [True, True, 1.0]
    vehicles.loc[vehicles["customer_id"] == "CUST-0003", ["fuel_type"]] = ["bev"]
    
    # CUST-0004: Tom (GP04 RECOMMEND) - 6 weeks history, paper statements
    customers.loc[customers["customer_id"] == "CUST-0004", ["is_persona", "digital_usage"]] = [True, 0.0]
    # Remove older transactions for Tom
    tom_txns = transactions[transactions["customer_id"] == "CUST-0004"]
    tom_txns = tom_txns[pd.to_datetime(tom_txns["date"]) > (CUTOFF_DATE - timedelta(days=42))]
    transactions = pd.concat([transactions[transactions["customer_id"] != "CUST-0004"], tom_txns])
    
    # CUST-0005: Dave (GP02 RECOMMEND) - 1960s semi, high winter gas, EPC D, homeowner
    customers.loc[customers["customer_id"] == "CUST-0005", ["is_persona", "home_owner", "epc_band"]] = [True, True, "D"]
    energy.loc[(energy["customer_id"] == "CUST-0005") & (energy["month"].str.endswith(("11", "12", "01", "02"))), "gas_kwh"] += 2000
    
    # CUST-0006: Sam (GP03 ABSTAIN) - homeowner, high elec, roof suitability unknown
    customers.loc[customers["customer_id"] == "CUST-0006", ["is_persona", "home_owner", "roof_suitability"]] = [True, True, "unknown"]
    energy.loc[energy["customer_id"] == "CUST-0006", "electricity_kwh"] += 500
    
    # CUST-0007: Renter (GP02, GP03 RULED_OUT, GP04 RECOMMEND) - flat, high app use, paper statements
    customers.loc[customers["customer_id"] == "CUST-0007", ["is_persona", "home_owner", "digital_usage"]] = [True, False, 0.2]
    
    # CUST-0008: Accessibility (GP04 RULED_OUT) - paper statements, accessibility_paper_need = True
    customers.loc[customers["customer_id"] == "CUST-0008", ["is_persona", "accessibility_paper_need", "digital_usage"]] = [True, True, 0.0]
    
    tables["customers"] = customers
    tables["transactions"] = transactions
    tables["vehicles"] = vehicles
    tables["energy_usage"] = energy
    tables["products"] = products
    tables["digital_usage"] = digital
    
    return tables
