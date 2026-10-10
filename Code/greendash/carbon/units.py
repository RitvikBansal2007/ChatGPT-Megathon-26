import re

SAFE = re.compile(r"^[A-Za-z0-9 £%.,/:()–\-]{1,60}$")

def fmt_kg(x: float) -> str:
    import math
    if math.isnan(x):
        return "Unknown"
    s = f"{round(x):,} kg CO2e"
    if not SAFE.match(s):
        raise ValueError(f"Unsafe string: {s}")
    return s

def fmt_range_kg(low: float, high: float) -> str:
    import math
    if math.isnan(low) or math.isnan(high):
        return "Unknown"
    s = f"{round(low):,} to {round(high):,} kg CO2e per year"
    if not SAFE.match(s):
        raise ValueError(f"Unsafe string: {s}")
    return s

def fmt_kwh(x: float) -> str:
    import math
    if math.isnan(x):
        return "Unknown"
    s = f"{round(x):,} kWh"
    if not SAFE.match(s):
        raise ValueError(f"Unsafe string: {s}")
    return s

def fmt_sheets(x: float) -> str:
    import math
    if math.isnan(x):
        return "Unknown"
    s = f"{round(x):,} sheets"
    if not SAFE.match(s):
        raise ValueError(f"Unsafe string: {s}")
    return s
