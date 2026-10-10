def ev_switch(annual_miles, ice_factor, kwh_per_mile, grid_factor):
    saved = annual_miles * ice_factor - annual_miles * kwh_per_mile * grid_factor
    return saved, "annual_miles x petrol factor - annual_miles x kWh per mile x grid factor"

def green_home_efficiency(gas_kwh, reduction_fraction, gas_factor):
    kwh_saved = gas_kwh * reduction_fraction
    return kwh_saved, kwh_saved * gas_factor, "gas kWh x reduction fraction (x gas factor for CO2e)"

def solar_install(kwp, kwh_per_kwp, grid_factor):
    kwh = kwp * kwh_per_kwp
    return kwh, kwh * grid_factor, "kWp x kWh per kWp (x grid factor for CO2e)"

def paperless(paper_statements_12m, sheets_per_statement):
    return paper_statements_12m * sheets_per_statement, "paper statements per year x sheets per statement"
