# Persistent Rulebook

- **Double-Blind Invariant**: Never allow any personal names (Aniket, Madhav, Kratik, Akshit, Ritvik), team names, or college names inside commits, files, charts, or terminal exports.
- **Deterministic Seed**: All generation must strictly derive from `numpy.random.default_rng(42)`. No unseeded `random.random()`, no `datetime.now()` in synthetic rows.
- **Data Protection**: Zero real banking data. C3 fields (display persona names, raw customer IDs, full postcodes) must be encrypted using AES-256-GCM via the security module or held out in temporary staging.
- **Metric Separation**: Digital adoption (paperless statements) must never be reported as $CO_2$ reduction. Separate: Emissions (kg CO2e), Energy (kWh), Paper (sheets), Digital adoption (count).
- **Mutually Exclusive Transaction Categories**: Fuel, Electricity, Gas, Public Transport, Home Improvement, Automotive, Utilities, Other. Boundary rules: Public EV charging = Fuel, Dual-fuel = Utilities, Taxi = Other, Public Transport = Scheduled mass transit only.
- **LLM Safe String Constraint**: All carbon engine formatted strings must strictly match `^[A-Za-z0-9 £%.,/:()–\\-]{1,60}$`.
