def conflict_flags(row: dict) -> list[str]:
    flags = []
    fuel_type = str(row.get("vehicle_fuel_type") or "").upper()
    if fuel_type == "BEV" and (row.get("fuel_txn_count_90d") or 0) >= 3:
        flags.append("BEV_RECORD_BUT_FUEL_SPEND")
    return flags

