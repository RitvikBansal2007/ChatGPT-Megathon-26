# GreenDash Data Documentation

## 1. Overview
The customer population is fully **synthetic** (5,000 customers, seed 42). Public data is used only as licensed **priors** (distribution shapes and national averages). No real banking data is used anywhere. Cutoff date is 2026-06-30 and take-up labels cover the 90 days after it.

## 2. Sources
| id | publisher | licence | used for | decision |
| --- | --- | --- | --- | --- |
| desnz_ghg_factors | DESNZ / Defra | OGL v3.0 | emission factors (`config/factors.csv`) | GO |
| dft_veh_fuel_share | Department for Transport | OGL v3.0 | vehicle fuel and age priors | GO |
| dft_nts_mileage | Department for Transport | OGL v3.0 | annual mileage prior | GO |
| ofgem_tdcv | Ofgem | OGL v3.0 | electricity and gas use priors | GO |
| ukpn_smartmeter_daily | UK Power Networks | OGL v3.0 | monthly electricity seasonality | GO |
| jrc_pvgis | EC JRC | CC BY 4.0 | solar kWh per kWp | GO |
| ons_regions | ONS | OGL v3.0 | region labels | GO |
| EPC register (address level) | MHCLG | extra address-data conditions | none | EXCLUDE |
| Kaggle mirrors | various | mirror licence may differ | none | EXCLUDE |

Full attribution sentences and check dates: `docs/LICENSES_DATA.md`.

## 3. Substitutions
The generator is parameterised by `data/priors/priors.json`, committed so the build runs offline with no API key. Where a source was not fetched on a given machine, the committed priors are used as the documented fallback. UCI Online Retail II was not used. Solar yield uses the sourced value `solar_kwh_per_kwp` in the priors and the `gp03_kwp_sizing` assumption.

## 4. Pipeline
Six stages: fetch (hash and record) → licence gate → schema validation (pandera) → sanitise (strip, de-duplicate, PII scan, drop-rate check) → priors (`priors.json`) → synthetic generation (latent → tables → personas → labels). Gates are in section 10.

## 5. Schema
Classes: C0 public, C1 internal synthetic, C2 sensitive synthetic, C3 pseudonymous key or free text.

| table | column | type | class |
| --- | --- | --- | --- |
| customers | customer_id | str | C3 |
| customers | age | int | C2 |
| customers | income_band | str | C2 |
| customers | postcode (fake, XX prefix) | str | C2 |
| customers | region | str | C1 |
| customers | home_owner | bool | C1 |
| customers | digital_usage | float 0-1 | C1 |
| customers | sustainability_preference | float 0-1 | C1 |
| customers | is_persona | bool | C0 |
| customers | epc_band | str | C1 |
| customers | roof_suitability | str | C1 |
| customers | existing_solar | bool | C1 |
| customers | accessibility_paper_need | bool | C2 |
| vehicles | customer_id, vehicle_type, fuel_type, vehicle_age, annual_mileage | str, str, str, int, int | C3, C1, C1, C1, C1 |
| energy_usage | customer_id, month, electricity_kwh, gas_kwh | str, str, float, float | C3, C1, C1, C1 |
| transactions | transaction_id, customer_id, date, merchant_description, amount, debit_credit, true_category | str, str, str, str, float, str, str | C3, C3, C1, C3, C2, C1, C1 |
| digital_usage | customer_id, month, digital_statements, paper_statements, digital_transactions, branch_visits | str, str, int, int, int, int | C3, C1, C1, C1, C1, C1 |
| products | customer_id, product, start_date, balance, status | str, str, str, float, str | C3, C1, C1, C2, C1 |
| green_products | product_id, product, category, eligibility, sustainability_metric | str | C0 |
| emissions_factors | activity, unit, kg_co2e_per_unit, source, sheet, row, col, vintage, licence | mixed | C0 |
| take_up_labels | customer_id, take_up_GP01..GP04 | str, int | C3, C1 |
| transaction_labels | transaction_id, true_category | str | C3, C1 |

`true_category` and the take-up labels are targets and must never be model features.

## 6. Generator rules
All randomness comes from `numpy.random.default_rng(42)`. No wall-clock time is used in rows. Latent drivers (never exposed to models): `green_affinity ~ Beta(2,5)`, `financial_headroom ~ N(0,1)`, `digital_propensity ~ Beta(3,2)`, `hidden_noise ~ N(0,1)`, plus event flags (car finance ending 12%, mortgage started 5%, recently moved 6%, car sold 3%). Eight golden personas overwrite CUST-0001 to CUST-0008; owners get a vehicle record and non-owners none.

## 7. Label formula
`score = β·observed + γ·hidden + σ·hidden_noise`; `p = sigmoid(score + b0)`; `take_up ~ Bernoulli(p)`; `take_up = 0` where not eligible. The intercept `b0` is solved by bisection on **eligible customers**, so the eligible-population base rate matches the target.

| product | γ green | γ headroom/digital | σ | eligibility | target (eligible) | achieved (eligible) |
| --- | --- | --- | --- | --- | --- | --- |
| GP01 | 2.0 | headroom 1.0 | 2.0 | has a car | 4-8% | 6.4% |
| GP02 | 1.5 | headroom 2.0 | 4.0 | homeowner | 3-6% | 4.8% |
| GP03 | 3.0 | headroom 1.0 | 2.5 | homeowner | 2-5% | 4.0% |
| GP04 | 1.0 | digital 4.0 | 2.0 | paper user (digital_usage < 0.5) | 15-25% | 18.4% |

Observed-feature weights β are zero by construction: take-up is driven by hidden drivers that also shape observed behaviour (income, usage, digital use), so features are informative but never a formula. Achieved values are read from `out/data_quality.json`.

## 8. Category labels
`true_category` is the category of the merchant template that produced the string (65 templates). 2 templates (about 3%) are deliberately ambiguous. A 200-row hand-checked gold set is in `gold_set.csv`.

## 9. Carbon method
Factors: DESNZ 2024 from `config/factors.csv`; assumptions from `config/assumptions.yaml`. Baseline is the customer's own current behaviour; horizon is year 1.

| product | metric family | formula |
| --- | --- | --- |
| GP01 | CO2e | miles × petrol factor − miles × kWh/mile × grid factor |
| GP02 | kWh, plus CO2e | gas kWh × reduction fraction (× gas factor) |
| GP03 | kWh, plus CO2e | kWp × kWh per kWp (× grid factor) |
| GP04 | paper (sheets) | paper statements per year × sheets per statement; never CO2e |

Low / central / high: vary the uncertain input. GP01 ±15%; GP02 reduction fraction low / central / high from the assumptions file scale; GP03 ±10% yield; GP04 has a single value. Missing input gives `INSUFFICIENT_DATA` with `missing_inputs`; no relevant asset gives `NOT_APPLICABLE`. The four metric families (CO2e, kWh, paper, digital adoption) are never mixed. All figures are estimates, not guarantees. Display strings come only from `greendash/carbon/units.py` and match `^[A-Za-z0-9 £%.,/:()–\-]{1,60}$`. Methodology follows GHG Protocol project and avoided-emissions guidance for baseline and horizon statements.

## 10. Quality gates
Run `python eval/data_quality.py` (writes `out/data_quality.json`).

| gate | threshold | result |
| --- | --- | --- |
| Schema conformance (pandera) | 100% | PASS |
| Foreign-key integrity | 0 orphans | PASS |
| Take-up base rates | in target ranges | PASS |
| Single-feature AUC (eligible population) | < 0.80 | PASS (max 0.72) |
| Persona raw-signal facts | 8 of 8 | PASS |
| Same seed, two runs | identical sha256 | PASS |
| PII scan | 0 hits | PASS |

The full persona outcome check (RECOMMEND / REVIEW / ABSTAIN / RULED_OUT) needs the orchestrator and models and is run at integration.

## 11. Limitations
Synthetic data cannot show real-world behaviour. Priors are national averages. Labels are rule-generated, so model metrics show pipeline correctness, not real-world performance. Impact figures are modelled estimates. Several assumptions in `config/assumptions.yaml` cite generic sources and need a page-level citation before final submission. Take-up RECOMMEND rates can be low because calibrated probabilities sit near the base rates; a per-product threshold decision is outstanding.
