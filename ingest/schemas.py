import pandera as pa

# Schema for vehicle fuel share table
fuel_share_schema = pa.DataFrameSchema({
    "fuel": pa.Column(str, pa.Check.isin(["petrol", "diesel", "hybrid", "bev", "other"])),
    "count": pa.Column(int, pa.Check.ge(0)),
})

# Schema for NTS mileage
mileage_schema = pa.DataFrameSchema({
    "mileage_band": pa.Column(str),
    "percentage": pa.Column(float, pa.Check.ge(0)),
})

# Schema for Ofgem TDCV
ofgem_tdcv_schema = pa.DataFrameSchema({
    "energy_type": pa.Column(str, pa.Check.isin(["electricity", "gas"])),
    "profile": pa.Column(str, pa.Check.isin(["low", "medium", "high"])),
    "kwh_annual": pa.Column(float, pa.Check.ge(0)),
})

# Schema for UKPN smart meter
ukpn_smartmeter_schema = pa.DataFrameSchema({
    "household_id": pa.Column(str, nullable=False),
    "kwh_day": pa.Column(float, pa.Check.in_range(0, 200), nullable=False),
})

# Schema for PVGIS
pvgis_schema = pa.DataFrameSchema({
    "month": pa.Column(int, pa.Check.in_range(1, 12)),
    "kwh_per_kwp": pa.Column(float, pa.Check.ge(0)),
})

# Schema for ONS regions
ons_regions_schema = pa.DataFrameSchema({
    "region_code": pa.Column(str),
    "region_name": pa.Column(str),
})
