def conflict_flags(row: dict) -> list[str]:
    flags = []
    if row.get("vehicle_fuel_type") == "BEV" and (row.get("fuel_txn_count_90d") or 0) >= 3:
        flags.append("BEV_RECORD_BUT_FUEL_SPEND")
    return flags
