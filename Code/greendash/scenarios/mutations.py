from __future__ import annotations

import copy
from datetime import date

import numpy as np
import pandas as pd

from greenproof.contracts import Mutation

Rows = dict[str, pd.DataFrame]

def _cid(rows: Rows) -> str:
    return rows["customers"]["customer_id"].iloc[0]

def set_vehicle_bev(rows: Rows, cutoff: date) -> Rows:
    rows["vehicles"] = rows["vehicles"].assign(fuel_type="BEV")
    tx, cut = rows["transactions"], pd.Timestamp(cutoff)
    recent_fuel = (tx["category"] == "Fuel") & (tx["date"] >= cut - pd.Timedelta(days=180))
    rows["transactions"] = tx[~recent_fuel]
    return rows

def remove_mileage(rows: Rows, cutoff: date) -> Rows:
    rows["vehicles"] = rows["vehicles"].assign(annual_mileage=np.nan)
    return rows

def remove_energy(rows: Rows, cutoff: date) -> Rows:
    rows["energy"] = rows["energy"].iloc[0:0]
    return rows

def add_conflict_fuel(rows: Rows, cutoff: date) -> Rows:
    rows = set_vehicle_bev(rows, cutoff)
    cid, cut = _cid(rows), pd.Timestamp(cutoff)
    extra = pd.DataFrame({
        "transaction_id": [f"SCN-{i}" for i in range(3)], "customer_id": cid,
        "date": [cut - pd.Timedelta(days=d) for d in (15, 45, 75)],
        "merchant_description": "SHELL 4821 LONDON", "amount": 60.0, "debit_credit": "D", "category": "Fuel"})
    rows["transactions"] = pd.concat([rows["transactions"], extra], ignore_index=True)
    return rows

def make_stale(rows: Rows, cutoff: date) -> Rows:
    shift = pd.Timedelta(days=200)
    rows["transactions"] = rows["transactions"].assign(date=rows["transactions"]["date"] - shift)
    for t in ("energy", "digital"):
        if rows[t].empty:
            continue
        m = (rows[t]["month"] - shift).dt.to_period("M").dt.to_timestamp()
        rows[t] = rows[t].assign(month=m)
    rows["vehicles"] = rows["vehicles"].assign(updated_at=rows["vehicles"]["updated_at"] - shift)
    return rows

def set_renter(rows: Rows, cutoff: date) -> Rows:
    rows["customers"] = rows["customers"].assign(home_owner=False)
    return rows

def sell_car(rows: Rows, cutoff: date) -> Rows:
    rows["vehicles"] = rows["vehicles"].assign(status="sold")
    tx, cut = rows["transactions"], pd.Timestamp(cutoff)
    recent_fuel = (tx["category"] == "Fuel") & (tx["date"] >= cut - pd.Timedelta(days=180))
    rows["transactions"] = tx[~recent_fuel]
    return rows

REGISTRY = {
    Mutation.SET_VEHICLE_BEV: set_vehicle_bev, Mutation.REMOVE_MILEAGE: remove_mileage,
    Mutation.REMOVE_ENERGY: remove_energy, Mutation.ADD_CONFLICT_FUEL: add_conflict_fuel,
    Mutation.MAKE_STALE: make_stale, Mutation.SET_RENTER: set_renter, Mutation.SELL_CAR: sell_car,
}

def apply_mutations(rows: Rows, mutations: list[Mutation], cutoff: date) -> Rows:
    rows = {k: v.copy(deep=True) for k, v in rows.items()}
    for m in mutations:
        rows = REGISTRY[m](rows, cutoff)
    return rows
