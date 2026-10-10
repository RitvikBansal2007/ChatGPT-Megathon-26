# ANIKET'S GUIDE v2: Data and Carbon Lead (Group 2)

**Project:** GreenProof (Megathon X, Problem Statement 1, Lloyds)
**You are:** Aniket, G2 "Data & carbon lead". Your partner is **Madhav** (ML and AI lead). He has his own guide.
**Sources:** the Deliverables PDF and Lloyds brief override everything; the PRD's product decisions stand; `3 Architecture.md` wins over the PRD only on team, clock and security (see Part A). If anything here disagrees, tell the team and fix this guide.
**Clock:** 11h30m total. `T+0:00` is kickoff. Every time below is "hours:minutes after kickoff".

---

## PART A. v2 UPDATE: WHAT THE OFFICIAL BRIEF, THE PRD AND THE DELIVERABLES RULES CHANGE

You now have every source document. This part lists what is **new or different** from v1. Read it first. The rest of this guide has already been edited to match.

### A.1 Which document wins

1. **Deliverables PDF** (deadlines, file names, double-blind rules) and the **Lloyds brief PDF** (what is graded): override everything.
2. **PRD.md**: product decisions stand (status rules, personas, Claim-Check rules, locked decisions, API shapes).
3. **3 Architecture.md**: wins over the PRD **only** on team split, clock, and security.
4. `Research.md` and `Project_Details.md`: background for the report and slides. No code depends on them.

### A.2 Hard deadlines (wall clock, no grace period)

| Milestone | Deadline | What is submitted |
| --- | --- | --- |
| **M1** | **10:00 PM, 10 Oct** | `deliverables/M1.pdf`, 2 pages: problem understanding, idea, high-level approach/pipeline/architecture, planned testing methodology |
| **M2** | **4:00 AM, 11 Oct** | `deliverables/M2.pdf`, 2 pages: current approach and changes since M1, **experiments run so far and their results**, testing progress, plan for the remaining time. **Plus all code so far pushed to `main`** |
| **Final** | **11:00 AM, 11 Oct** | Code on `main`; `README.md` (setup and run instructions **only**); `LICENSE` (MIT); `deliverables/final_report.pdf` (max 3 pages); demo video (max 4 minutes, Google Drive link set to "Anyone with the link"); code zip (no `node_modules`, virtual environments, datasets or model weights) |
| **Slides** | **11:30 AM, 11 Oct** | Slides as PDF through the slides form (cannot be pushed to the repo) |

Rules that can end our run:

- **No M1 or late M1/M2 = direct disqualification.** M1 is the single most important deliverable tonight.
- **Only the latest commit on `main` at each deadline is evaluated.** Work on branches is invisible. **Merge to `main` at least 30 minutes before every deadline**, and make sure `main` still runs.
- All documents are **PDFs**, committed under `deliverables/` with the **exact file names** above. Never delete earlier deliverables.
- **Team number at the top of every PDF.**

### A.3 Clock warning (ask Ritvik to settle this now)

The Architecture plan counts hours from kickoff (**T+0:00**, 11h30m total). The real deadlines are wall-clock times (M1 at 10 PM, M2 at 4 AM, final at 11 AM). **They do not line up by themselves.** Ask Ritvik to write the **wall-clock time of T+0:00** on the team board and convert every T+ time in your guide. Until then:

- Send your M1 inputs to Ritvik at least **45 minutes before 10 PM**.
- Send your M2 inputs (real numbers) at least **1 hour before 4 AM**; merge everything to `main` **30 minutes before 4 AM**.
- If the schedule puts a result after M2, report only what exists at that time, honestly (see A.9).

### A.4 Double-blind rules (breaking these risks disqualification from round 0)

- **No team name, member names or college names in any PDF or in the demo video.** That includes screenshots, terminal windows (your username or hostname), browser tabs, file metadata and chart titles.
- Do **not** commit documents that carry names. The planning docs (`PRD.md` has a person's name in its header; `3 Architecture.md` lists the team) must be **sanitised or left out of the repo**. Tell Ritvik and Akshit.
- `README.md` holds **setup and run instructions only**, plus links to externally hosted datasets or model weights. **Do not explain the solution there.** Solution explanations go in `docs/` and the report.
- Add the **MIT `LICENSE`** file (Akshit). Public datasets keep their own licences (see `LICENSES_DATA.md`).
- The code zip **excludes datasets and model weights**, so an organiser must be able to rebuild them: `make all` must work from a clean clone, offline, using the committed `priors.json`, and **without any API key** (template fallback).
- Only synthetic names appear in the data (the 8 personas). Never anything real.

### A.5 What the official brief fixes for us

**Required opportunities:** GP01 EV Finance · GP02 Green Home Loan · GP03 Solar Finance · GP04 Paperless Banking. (GP05 Green Investments and GP06 Green Loans are optional; the PRD cuts them.)

**Data tables and fields (use these exact names; extra columns are allowed if documented):**

| Table | Fields |
| --- | --- |
| Customers | customer_id, age, income_band, postcode, home_owner, digital_usage, sustainability_preference |
| Transactions | transaction_id, customer_id, date, merchant_description (raw text), amount, debit_credit |
| Products | customer_id, product, start_date, balance, status |
| Vehicles | customer_id, vehicle_type, fuel_type, vehicle_age, annual_mileage |
| Energy usage | customer_id, month, electricity_kwh, gas_kwh |
| Digital usage | customer_id, month, digital_statements, paper_statements, digital_transactions, branch_visits |
| Green products | product_id, product, category, eligibility, sustainability_metric |
| Emissions factors | activity, unit, kg_co2e_per_unit, source |
| Labels | transaction category; take-up (0/1) per customer and product |

**FR2: exactly eight transaction categories, mutually exclusive:** `Fuel`, `Electricity`, `Gas`, `Public Transport`, `Home Improvement`, `Automotive`, `Utilities`, `Other`. Boundary decisions must be **documented and applied consistently**.

| Boundary decision | Category | Status |
| --- | --- | --- |
| Petrol, diesel, **public EV charging** | Fuel | **Locked (PRD)** |
| **Dual-fuel** supplier bill | Utilities | **Locked (PRD)** |
| **Taxi / ride-hail** | Other | **Locked (PRD)** |
| Public Transport = scheduled mass transit only (train, bus, tram, tube) | Public Transport | **Locked (PRD)** |
| Electricity-only supplier bill | Electricity | Proposed |
| Gas-only supplier bill | Gas | Proposed |
| Water, sewerage | Utilities | Proposed |
| Vehicle purchase, servicing, MOT, tyres, parts, parking | Automotive | Proposed |
| Insulation, glazing, boilers, DIY and home-improvement retailers, solar installers | Home Improvement | Proposed |
| Groceries, dining, shopping, anything else | Other | Proposed |
| A supermarket **fuel station** line vs a supermarket **groceries** line | decided by the string (fuel-station wording = Fuel, else Other) | Proposed |

**Aniket and Madhav: agree the "Proposed" rows in the first 15 minutes**, write them into `config/categories.yaml` (Madhav) and `docs/DATA.md` (Aniket), and never change them silently afterwards.

**What judges score (weights):** Business relevance 15 · ML and recommendation quality incl. data quality, validation methodology and held-out metrics **20** · Sustainability insight quality 15 · GenAI/LLM implementation (evaluation set) 15 · Technical architecture incl. data engineering and system performance 15 · Explainability and Responsible AI 10 · UX and dashboard 5 · Innovation 5. **Group 2 owns most of the 20 + 15 + 15 (and shares the 10).**

**What organisers may do:** rerun our code; inspect data, calculations and outputs; test scenarios with **missing data, conflicting signals, products that should not be recommended, and insufficient information to estimate impact**. Results we report that cannot be reproduced can hurt us. Evaluation report (item G) must give the metrics **on the validation set**, with a baseline comparison, methodology and limitations.

**The brief's own example output** (shape to match): `customer_id`, `opportunity` (e.g. EV_FINANCE), `propensity`, `confidence`, `reason_codes` (e.g. HIGH_FUEL_SPEND, HIGH_ANNUAL_MILEAGE, EXISTING_VEHICLE).

**Metric families stay separate:** emissions (kgCO2e), energy (kWh), paper (sheets), digital adoption. Digital adoption is **not** a carbon reduction.

### A.6 The 8 golden personas (PRD Appendix A)

| ID | Persona | Designed outcome |
| --- | --- | --- |
| CUST-0001 | Priya: commuter, homeowner, 8-year-old petrol car, car finance ending, complete data | GP01 RECOMMEND, high confidence; GP04 quick win |
| CUST-0002 | Marcus: vehicle record says BEV, fuel spend continues, stale EPC | GP01 REVIEW (mixed signals); GP02 ABSTAIN |
| CUST-0003 | Aisha: owns BEV, has solar, already paperless | GP01, GP03, GP04 RULED_OUT with rules; "You're all set" |
| CUST-0004 | Tom: new customer, 6 weeks of history, paper statements | GP01-03 ABSTAIN; GP04 RECOMMEND (sheets + adoption only) |
| CUST-0005 | Dave: 1960s semi, high winter gas, EPC D, homeowner | GP02 RECOMMEND |
| CUST-0006 | Sam: homeowner, high electricity, roof suitability unknown | GP03 ABSTAIN with Confidence Ladder (roof question) |
| CUST-0007 | Renter in a flat, high app use, paper statements | GP02, GP03 RULED_OUT; GP04 RECOMMEND |
| CUST-0008 | Accessibility paper need flagged | GP04 RULED_OUT (never nudge) |

**Status rules (orchestrator, in order):** (1) NOT_ELIGIBLE → **RULED_OUT**; (2) conflict flag → **REVIEW**; (3) carbon INSUFFICIENT_DATA or critical feature missing → **ABSTAIN**; (4) propensity ≥ 0.5 **and** confidence ≥ 0.6 → **RECOMMEND**; (5) otherwise **SOFT_SURFACE**. Thresholds live in `config/thresholds.yaml`.

### A.7 A design risk the team must settle early (RECOMMEND may almost never fire)

Take-up base rates are **2-8%** for GP01-GP03. A properly **calibrated** probability for an average customer will therefore be near those rates, far below the **0.5** needed for RECOMMEND. Only customers with very strong signals (Priya, Dave) can reach 0.5. Risks: the cockpit funnel shows almost no RECOMMEND customers, and the persona gate "8 of 8 match" can fail even though nothing is wrong.

What to do:

1. **Aniket:** give personas strong, realistic signals (and hidden drivers) so their *true* take-up probability is high. Do **not** hard-code their scores.
2. **Madhav:** at the end of model training, print how many validation customers land in each status, and the share with calibrated propensity ≥ 0.5 per product.
3. **Everyone (decide by the first checkpoint):** if RECOMMEND is empty for ordinary customers, agree one fix in `config/thresholds.yaml` (for example a per-product threshold, or "top decile of calibrated propensity") and **document it** in the report. Do not weaken calibration to make numbers look bigger.
4. Personas are **held out of training and the three splits** (flag `is_persona`) and only **scored**, so their designed labels cannot leak into the models. Confirm with Akshit.

### A.8 Cautions from the research doc

- Several statistics in `Research.md` are **unverified** (mail-theft figures, Lloyds EV-share claims, a 2027 loan scheme, exact emission factors). **Nothing from that doc goes on a slide or in a report unless you checked it against a primary source.**
- Emissions numbers come only from the pinned DESNZ/Defra workbook (sheet and row recorded).
- Admit limits: synthetic data means reported metrics prove pipeline correctness, **not** real-world performance.
- Fairness is a graded theme: age, income band and fine-grained postcode are **not** model features. They are kept only for the **aggregated** fairness audit by income band, age band and region.


### A.9 Your inputs to the PDFs (send to Ritvik as plain text, **no names**)

| For | What you write | Length | Send |
| --- | --- | --- | --- |
| **M1** (10 PM) | (a) data strategy: synthetic population + licensed public priors, why no real data is used; (b) how data quality is tested: quality gates, leakage prevention, hand-calculated carbon tests | about 120 words + 5 bullets | 45 min before M1 |
| **M2** (4 AM) | actual progress: sources verified (n GO / n excluded), `factors.csv` done, generator status, base rates achieved, gate results, carbon tests, what is left | at most 150 words + real numbers | 1 h before M2 |
| **Final report** (3 pages) | Data section: sources + licences, schema, label formula (β, γ, σ), gates table, carbon method + factor vintage, limitations | half a page + 1 table | before final |
| **Slides / video** | one data slide (licensed sources, synthetic population, no real data) and one carbon-method slide | | with Ritvik |

**Draft M1 paragraph (edit with your real choices, keep it name-free):**

> *Data.* No real banking data is used. We generate a seeded synthetic population (5,000 customers plus 8 designed personas) across the eight tables in the brief. Public data is used only as lawfully licensed summary priors (UK government statistics) and for official emissions factors from the pinned DESNZ/Defra release, each recorded with licence, source and row. Take-up labels come from documented latent drivers plus noise inside a 90-day outcome window after a fixed cutoff, so models cannot recover a formula. *Testing.* Automated gates check schema, key integrity, base rates, single-feature predictability, leakage (no post-cutoff data, no customer in two splits), determinism (same seed gives identical artefacts) and hand-calculated carbon tests.

---

## PART 0. READ THIS FIRST

### 0.1 Your job in one sentence

You make **legal data** and a **fake-but-realistic bank customer world**, and you build the **carbon calculator**. Everyone else's work (models, API, screens) stands on what you produce.

### 0.2 The whole thing explained simply

Imagine we are building a toy bank town.

1. **Real public facts** (how many kWh a house uses, how many miles people drive, how much CO2 a petrol mile makes) come from **government websites**. These are allowed because their licences say we can reuse them. We use them only as **averages and shapes** (called *priors*), never as individual people.
2. Our code **invents 5,000 fake customers** (plus 8 hand-made "golden personas") whose behaviour follows those real averages. Fake names, fake accounts, fake transactions. **No real person is ever involved.**
3. Our code decides, with a hidden formula plus noise, which fake customers "took up" each green product in the next 90 days. Those are the **labels** Madhav trains on.
4. You also build the **carbon engine**: a calculator that says "switching saves roughly X to Y kg CO2e per year", with the maths shown.

### 0.3 Words you must know

| Word | Meaning for a 5-year-old |
| --- | --- |
| **Dataset** | A big table of facts someone published. |
| **Licence** | The rule that says what we may do with a dataset. No allowed licence = we do not use it. |
| **OGL v3.0** | "Open Government Licence". UK government says: use it, even commercially, just credit them. |
| **Prior** | A summary shape of real data, e.g. "20% of cars are diesel". We copy the shape, not the rows. |
| **Synthetic data** | Fake data made by our own code. |
| **Seed (42)** | A starting number that makes the random generator give the same answer every time. |
| **Latent / hidden driver** | A secret trait (like "how green is this person") that creates behaviour but is NOT given to the model. |
| **Label** | The right answer the model learns from (did this fake customer take up the product?). |
| **Base rate** | How often take-up happens overall (e.g. 4–8%). |
| **Cutoff** | `2026-06-30`. Features may only use data **before** this date. Labels look 90 days **after**. |
| **Emission factor** | "1 mile in a petrol car makes N kg of CO2e". Comes from the government workbook. |
| **kgCO2e** | Kilograms of carbon-dioxide-equivalent. The unit of climate impact. |
| **Vintage** | Which year's version of the factor workbook we pinned. Locked in `config/decisions.yaml`. |
| **PII** | Personal info (email, phone, postcode, card number). Must never leak. |
| **C3 columns** | Our most sensitive fake columns (persona name, full postcode, raw customer ID). Kratik's code encrypts them. |
| **Parquet** | A compact file format for tables (`.parquet`). |
| **pandera** | A tool that checks a table has the right columns, types and ranges. |

### 0.4 Your folders (edit ONLY these)

```
ingest/                      (all of it)
greenproof/generator/        (latent.py, tables.py, merchants.py, personas.py, labels.py)
greenproof/carbon/           (engine.py, formulas.py, units.py)
config/factors.csv
data/priors/                 (priors.json is COMMITTED)
docs/DATA.md
docs/LICENSES_DATA.md
eval/llm_eval/build_set.py
eval/llm_eval/adversarial.yaml
tests/unit/                  (only your own carbon / generator tests)
```

If you need a change outside these, do a **2-line PR and ping the owner in chat**.

### 0.5 What you owe other people, and when (the deadlines that stall the team)

| By | To | What |
| --- | --- | --- |
| **T+0:45** | Everyone | `config/factors.csv` + draft `docs/LICENSES_DATA.md` |
| **T+1:15** | Madhav | Merchant template library (`generator/merchants.py`) |
| **T+2:30** | (internal) | `priors.json` committed. Fallback rule kicks in here. |
| **T+3:30** | Akshit, Madhav | `make data` produces all raw tables + labels (**CP1**) |
| **T+3:00-3:20** | Madhav | 20-minute hand-check of the 200-string gold set |
| **T+5:30** | Akshit | Carbon engine (his orchestrator calls it at **CP2 T+6:00**) |
| **T+7:30** | Madhav | 150-case LLM eval set (130 packs + 20 adversarial sentences, plus Kratik's injection set) |
| **T+7:30-9:30** | Everyone | `DATA.md` + `LICENSES_DATA.md` final |
| **T+9:30-11:00** | Ritvik | Receipts charts and data slides |

### 0.6 Ground rules (breaking these can fail the whole project)

1. **No real data. Ever.** No bank exports, no real names, no screenshots of real accounts.
2. **No web scraping.** Download only from the official bulk-download or API link of a source.
3. **Licence first, download second.** If a licence is unclear after 5 minutes, **exclude the source** and use the fallback.
4. **Never paste a secret** (keys, tokens) into chat, code or git. Secrets live only in `.env`, which is gitignored.
5. **Merge to `main` every 90 minutes:** T+1:30, 3:00, 4:30, 6:00, 7:30, 9:00. `main` must always pass `make app` (on fixtures) and `pytest -q`.
6. **Numbers on slides come from `EVALUATION.md`**, never from memory.
7. **Everything from a fixed seed (42).** No `random.random()` without a seeded generator. No `datetime.now()` inside generated data.

---

## PART 1. SET UP YOUR COMPUTER (T+0:00 to 0:30, in parallel with Akshit creating the repo)

### Step 1.1 Check your tools

Open a terminal and run each line. Each should print a version.

```bash
python3 --version      # must say 3.11.x
git --version
make --version
```

If Python is not 3.11, install 3.11 (python.org or `pyenv`). On Windows use WSL2 (Ubuntu) because the Makefile and shell commands assume Linux/macOS.

### Step 1.2 Turn on disk encryption (checklist item for all 5 laptops)

- **Windows:** BitLocker. **macOS:** FileVault. **Linux:** LUKS (usually chosen at install).
- Confirm it is ON and tell Kratik in chat "Aniket FDE confirmed".

### Step 1.3 Get the repo (once Akshit says it exists)

```bash
git clone <REPO_URL_FROM_AKSHIT> greenproof
cd greenproof
git checkout -b g2-aniket
python3.11 -m venv .venv
source .venv/bin/activate          # Windows WSL: same. PowerShell: .venv\Scripts\Activate.ps1
```

You will see `(.venv)` at the start of your prompt. **Always activate it** in every new terminal.

### Step 1.4 Install what you need

Until Akshit's `pyproject.toml` / `requirements.lock` is ready (about T+0:30), install the basics yourself:

```bash
pip install pandas pyarrow numpy pyyaml requests pandera openpyxl pytest
```

When `requirements.lock` exists, switch to the team's pinned install:

```bash
pip install --require-hashes -r requirements.lock
```

### Step 1.5 Run the skeleton

```bash
make keys     # creates .env with DATA_KEY, HMAC_KEY, JWT_SECRET (Kratik's target)
make app      # should start without crashing on fixtures
```

If it fails, do not fix other people's folders. Post the exact error in chat.

### Step 1.6 Install the safety net (Kratik provides it)

```bash
pip install pre-commit
pre-commit install
```

Now every `git commit` runs gitleaks, ruff and bandit. If a commit is rejected, **read the message**; it is telling you about a real problem (usually a secret or an unsafe pattern).

**Exit check:** you can run `make app` and `git commit` on your branch.

---

## PART 2. PROCURE THE DATASETS LEGALLY (T+0:00 to 0:45)

This is the most important part to get exactly right. Take it one source at a time.

### Step 2.1 Understand what "legal" means here

For each dataset you must be able to answer, **in writing**: *Who published it? What is the licence? Where is the licence text? When did I check?* That goes in `docs/LICENSES_DATA.md`.

The code allow-list (later in `licence_gate.py`) accepts only:

- `OGL-UK-3.0` (Open Government Licence v3.0)
- `CC-BY-4.0`
- `CC0-1.0`
- anything **manually approved** with a written note in `LICENSES_DATA.md`

### Step 2.2 DO NOT use these (explicitly excluded)

- EPC register address-level data
- Kaggle re-uploads of any dataset (the mirror's licence may differ from the original)
- anything that needs a login or makes you accept non-reuse terms
- any scraped retailer or bank page
- any real transaction, anywhere

### Step 2.3 The 8 sources, one by one

For **every** source use this exact routine (takes about 5 minutes each; start with #1):

1. Search the web for the source name (phrases below). Choose the **official publisher page** (gov.uk, ons.gov.uk, ofgem.gov.uk, data.london.gov.uk, joint-research-centre / PVGIS site, archive.ics.uci.edu). Not a blog, not a mirror.
2. On that page find the words **"Licence"**, **"Terms"**, **"Re-use"**, or **"Open Government Licence"**. Copy the licence name and the licence link.
3. Find the **direct download link** of the one file you need (CSV or XLSX). Right-click → *Copy link address*.
4. Write the entry into `ingest/sources.yaml` (template in Step 2.4).
5. Add a row in `docs/LICENSES_DATA.md` (template in Step 2.5).
6. Decide: **GO** (licence on allow-list) or **EXCLUDE** (unclear or not allowed).

| # | Search for | Official publisher | What to download | Why we need it | Priority |
| --- | --- | --- | --- | --- | --- |
| 1 | `UK Government GHG Conversion Factors for Company Reporting` | DESNZ / Defra on gov.uk | The Excel workbook for the **pinned vintage year** in `config/decisions.yaml` (ask Akshit which year). Use the "full set" or "condensed set" | Emission factors: petrol/diesel car per mile, EV per mile, grid electricity, natural gas | **REQUIRED** |
| 2 | `DfT vehicle licensing statistics data tables` | Department for Transport | The table of licensed cars by **fuel type** (petrol, diesel, hybrid, battery electric) and by **age** | Fuel-type share and vehicle-age priors | High |
| 3 | `National Travel Survey car mileage` | Department for Transport | The table of **annual miles per car** (distribution by band) | Annual mileage priors | High |
| 4 | `Ofgem Typical Domestic Consumption Values` | Ofgem | The TDCV figures for electricity and gas (kWh/year, low/medium/high) | Annual kWh priors; **fallback if #5 fails** | High |
| 5 | `SmartMeter Energy Consumption Data in London Households` | UK Power Networks via London Datastore | **Daily summary file only** (not the half-hourly one, it is huge) | Household electricity distribution + seasonality | Medium |
| 6 | `PVGIS photovoltaic estimate UK` | European Commission JRC | kWh per kWp per year for a few UK regions | Solar Finance impact | Medium |
| 7 | `ONS regions names and codes` | Office for National Statistics | Region or local-authority **names list** | Region labels only | Medium |
| 8 | `UCI Online Retail II` | UCI ML Repository | The dataset file | Optional sanity check of timing/amount seasonality | Low (skip if behind) |

Tips that save you time:

- Government pages often list many files. You want the **smallest** file that has your numbers.
- If a page only shows a chart, look for "Download data" or "CSV" next to it.
- Never download the same file twice by hand. After Step 3 the script does it and checks the fingerprint.
- Start the **big downloads first** (#5) in the background while you do licence checks for the rest. If #5 is not done by **T+2:30**, apply the fallback rule (Step 4.6).

### Step 2.4 Fill `ingest/sources.yaml`

One block per source. Copy this and fill the `<...>` parts from the official page.

```yaml
- id: desnz_ghg_factors
  publisher: DESNZ / Defra
  url: <direct file link, must start with https://>
  licence: OGL-UK-3.0
  licence_url: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
  attribution: "Contains public sector information licensed under the Open Government Licence v3.0."
  sha256: null            # script fills on first download, then enforces
  retrieved_at: null
  used_for: [emission_factors]

- id: dft_veh_fuel_share
  publisher: Department for Transport
  url: <direct file link>
  licence: OGL-UK-3.0
  licence_url: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
  attribution: "Contains public sector information licensed under the Open Government Licence v3.0."
  sha256: null
  retrieved_at: null
  used_for: [vehicle_fuel_type_prior, vehicle_age_prior]
```

Make one block per source id: `dft_nts_mileage`, `ofgem_tdcv`, `ukpn_smartmeter_daily`, `jrc_pvgis`, `ons_regions`, `uci_online_retail_ii`. For a licence that is not one of the three allowed IDs, write the licence **as the page states it**. The gate will reject it unless you add a manual approval note in `LICENSES_DATA.md` (and tell the team why).

### Step 2.5 Start `docs/LICENSES_DATA.md`

```markdown
# Data Licence Register

Checked by: Aniket. Every row was verified on the publisher's page on the date shown.

| id | publisher | dataset | licence (as stated) | licence URL | checked on | decision | attribution used | used for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| desnz_ghg_factors | DESNZ / Defra | GHG conversion factors <year> | OGL v3.0 | <url> | 2026-10-10 | GO | Contains public sector information licensed under the OGL v3.0 | config/factors.csv |

## Excluded sources
- EPC register address-level data: extra address-data licence conditions.
- Kaggle mirrors: mirror licence can differ from the original.

## Manual approvals
(none unless the team agrees in writing here: who approved, why, when)
```

### Step 2.6 Build `config/factors.csv` by hand from the DESNZ workbook (REQUIRED, do it first)

This file drives the carbon engine, so it must be exact.

1. Download the DESNZ workbook from the official page (browser is fine for this one).
2. Open it in Excel / LibreOffice. Use the **contents/index sheet** to find the sheets. The ones you need are usually about: **passenger vehicles** (cars by fuel type, per mile or per km), **UK electricity** (grid factor, kgCO2e per kWh), and **fuels** (natural gas, kgCO2e per kWh).
3. For **each factor you need**, record: the activity name, the unit, the number, the **sheet name**, the **row number**, the column letter, the vintage year, the licence ID.
4. Make sure the unit is what you think. The workbook has per-km AND per-mile; kWh (Net CV) vs kWh (Gross CV); "kg CO2e" vs "kg CO2". **Write down the exact column heading.** Pick the CO2e total column, not a CO2-only column.
5. Create `config/factors.csv`:

```csv
activity,unit,kg_co2e_per_unit,source,sheet,row,col,vintage,licence
car_petrol_average,mile,<copy value>,DESNZ GHG conversion factors,<sheet name>,<row number>,<column letter>,<year>,OGL-UK-3.0
car_diesel_average,mile,<copy value>,DESNZ GHG conversion factors,<sheet name>,<row number>,<column letter>,<year>,OGL-UK-3.0
car_bev_average,mile,<copy value>,DESNZ GHG conversion factors,<sheet name>,<row number>,<column letter>,<year>,OGL-UK-3.0
grid_electricity,kWh,<copy value>,DESNZ GHG conversion factors,<sheet name>,<row number>,<column letter>,<year>,OGL-UK-3.0
natural_gas,kWh,<copy value>,DESNZ GHG conversion factors,<sheet name>,<row number>,<column letter>,<year>,OGL-UK-3.0
```

(The first four columns are exactly the brief's emissions-factor table fields (`activity, unit, kg_co2e_per_unit, source`); `sheet`, `row`, `col`, `vintage`, `licence` are our extras, and `col` is only for your own test. Add more activities only if a product needs them, see Step 6.3. The PRD's GP01 formula uses petrol and grid-electricity factors, so those two rows are mandatory; keep `car_bev_average` only as a cross-check.)

6. Double-check **every number twice** against the workbook, by two different eyes if possible (ask Madhav to read your CSV against the workbook for 5 minutes at T+0:40).
7. Write the unit test later (Step 7.4) that re-reads the workbook cell and compares.

**Exit check T+0:45:** `config/factors.csv` committed, `LICENSES_DATA.md` draft committed, `sources.yaml` filled. Tell the team in chat.

Commit:

```bash
git add config/factors.csv docs/LICENSES_DATA.md ingest/sources.yaml
git commit -m "G2-An: factors.csv, licence register draft, sources manifest"
git push -u origin g2-aniket
```

---

## PART 3. MERCHANT TEMPLATE LIBRARY (T+0:45 to 1:15, hand to Madhav at T+1:15)

### Step 3.1 What this is

Bank statements show messy text like `CARD PAYMENT TO SHELL 0482 LONDON`. Madhav's categoriser must learn to read that. **You** write the generator of that messy text, and you know the **true category** of each, so Madhav can test his categoriser honestly.

### Step 3.2 Use the 8 categories fixed by the brief (agree boundaries with Madhav, 15 minutes)

The brief fixes **exactly eight** categories: `Fuel`, `Electricity`, `Gas`, `Public Transport`, `Home Improvement`, `Automotive`, `Utilities`, `Other`. Use these names **exactly**. The locked and proposed boundary decisions are in the table in **Part A.5**: sit with Madhav for 15 minutes, settle the "Proposed" rows, and write them down in `docs/DATA.md` (you) and `config/categories.yaml` (Madhav). Your templates must obey them, for example:

- Public EV charging = **Fuel**; dual-fuel supplier bill = **Utilities**; taxi / ride-hail = **Other**
- Electricity-only bill = **Electricity**; gas-only bill = **Gas**
- Train / bus / tram = **Public Transport**; car servicing, MOT, tyres = **Automotive**; insulation, glazing, boilers = **Home Improvement**

### Step 3.3 Build the library in `greenproof/generator/merchants.py`

Requirements:

- **At least 60 merchant templates**, at least 5 per category across all 8 categories (more for Fuel, Utilities and Other). Madhav tests on **unseen merchants** (group split by template), so he needs plenty of distinct templates.
- Each template has: `template_id`, `true_category`, a few `names`, a typical `amount range`, and an `ambiguous` flag.
- About **3% of generated strings are deliberately ambiguous** (e.g. a supermarket fuel station vs the supermarket groceries). The true category follows the template that generated it.
- Noise functions: card-processor prefixes, store numbers, truncation, mixed case, trailing town.

```python
# greenproof/generator/merchants.py
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class MerchantTemplate:
    template_id: str          # e.g. "FUEL_01"
    true_category: str        # must match categories.yaml exactly
    names: tuple              # base display names
    amount_range: tuple       # (min, max) in GBP for one purchase
    ambiguous: bool = False

TEMPLATES = [
    MerchantTemplate("FUEL_01", "Fuel", ("SHELL", "SHELL SERVICE STN"), (20, 90)),
    MerchantTemplate("FUEL_02", "Fuel", ("BP CONNECT", "BP"), (20, 90)),
    MerchantTemplate("FUEL_EV_01", "Fuel", ("EV CHARGE POINT", "RAPID CHARGE HUB"), (5, 30)),
    MerchantTemplate("ELEC_01", "Electricity", ("ELECTRICITY SUPPLY DD", "POWER CO ELECTRICITY"), (30, 140)),
    MerchantTemplate("GAS_01", "Gas", ("GAS SUPPLY DD", "HOME GAS CO"), (25, 160)),
    MerchantTemplate("UTIL_01", "Utilities", ("DUAL FUEL ENERGY", "WATER SERVICES"), (40, 220)),
    MerchantTemplate("PT_01", "Public Transport", ("RAIL TICKET", "CITY BUS", "METRO TRAVEL"), (2, 80)),
    MerchantTemplate("AUTO_01", "Automotive", ("QUICK FIT TYRES", "MOT TEST CENTRE", "AUTO SERVICE"), (30, 600)),
    MerchantTemplate("HOME_01", "Home Improvement", ("LOFT INSULATION CO", "DIY WAREHOUSE", "WINDOW AND GLAZING"), (20, 3000)),
    MerchantTemplate("OTHER_TAXI_01", "Other", ("UBER TRIP", "BOLT RIDE"), (6, 40)),
    MerchantTemplate("SUPER_FUEL", "Fuel", ("SUPERMARKET FUEL STATION",), (20, 80), ambiguous=True),
    MerchantTemplate("SUPER_GROC", "Other", ("SUPERMARKET",), (8, 120), ambiguous=True),
    # ... continue until you have 60+ templates (at least 5 per category)
]

PREFIXES = ["", "", "CARD PAYMENT TO ", "POS ", "SQ *", "PAYPAL *", "DD ", "VIS "]
TOWNS = ["LONDON", "LEEDS", "BRISTOL", "GLASGOW", "CARDIFF", "MANCHESTER", ""]

def noisy_string(tpl: MerchantTemplate, rng: np.random.Generator) -> str:
    name = str(rng.choice(tpl.names))
    s = str(rng.choice(PREFIXES)) + name
    if rng.random() < 0.5:
        s += f" {int(rng.integers(1, 9999)):04d}"          # store number
    town = str(rng.choice(TOWNS))
    if town:
        s += f" {town}"
    if rng.random() < 0.15:
        s = s[: int(rng.integers(12, 22))]                 # truncation
    r = rng.random()
    if r < 0.2:
        s = s.lower()
    elif r < 0.35:
        s = s.title()
    return s.strip()
```

**Careful (security):** merchant strings must be **plain safe text**. No emails, phone numbers, long digit strings or anything that looks like a card or account number. Kratik's PII scanner will flag them and the pipeline will stop.

### Step 3.4 Hand over

```bash
git add greenproof/generator/merchants.py
git commit -m "G2-An: merchant template library (60+ templates, noise)"
git push
```

Message Madhav: "merchants.py is on `g2-aniket`, categories used: <list>." Then **merge to main at T+1:30** (the first 90-minute merge).

---

## PART 4. THE INGESTION PIPELINE (T+1:15 to 2:30)

Goal: one command turns downloaded public files into a small committed file `data/priors/priors.json`. After that, the whole project can run **offline**.

The pipeline stages (from the architecture): **fetch → licence gate → schema check → sanitise → PII scan → format priors**.

### Step 4.1 `ingest/fetch.py`

What it must do: download over **HTTPS only**, save to `data/public/<id>/`, record sha256 and time, and **refuse to continue if the hash changes** once pinned.

```python
# ingest/fetch.py
import hashlib, datetime, yaml, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "ingest" / "sources.yaml"
OUT = ROOT / "data" / "public"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch_one(src: dict) -> Path:
    url = src["url"]
    if not url.startswith("https://"):
        raise ValueError(f"{src['id']}: HTTPS only")
    folder = OUT / src["id"]
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / url.split("/")[-1].split("?")[0]
    r = requests.get(url, timeout=60, verify=True)      # never set verify=False
    r.raise_for_status()
    dest.write_bytes(r.content)
    digest = sha256_file(dest)
    if src.get("sha256") and src["sha256"] != digest:
        raise RuntimeError(f"{src['id']}: file changed (hash mismatch)")
    src["sha256"] = digest
    src["retrieved_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    dest.chmod(0o444)                                    # read-only
    return dest

def main():
    sources = yaml.safe_load(SOURCES.read_text())
    for src in sources:
        try:
            print("fetching", src["id"])
            fetch_one(src)
        except Exception as e:
            print("FAILED", src["id"], e)                # one failure must not stop the others
    SOURCES.write_text(yaml.safe_dump(sources, sort_keys=False))

if __name__ == "__main__":
    main()
```

Notes:

- If a download needs a login, a cookie or a click-through agreement, **do not work around it**. Mark `decision: EXCLUDE` and use the fallback.
- `yaml.safe_dump` drops YAML comments. That is fine; keep notes in `LICENSES_DATA.md`.
- Never log full URLs with tokens; there should be none.

### Step 4.2 `ingest/licence_gate.py`

```python
# ingest/licence_gate.py
ALLOW = {"OGL-UK-3.0", "CC-BY-4.0", "CC0-1.0"}

def check(src: dict, manually_approved: frozenset = frozenset()) -> bool:
    ok = src["licence"] in ALLOW or src["id"] in manually_approved
    print(("PASS " if ok else "REJECT ") + src["id"] + " licence=" + str(src["licence"]))
    return ok
```

**Order matters:** run the gate **before** parsing anything. A rejected source must never be written into `data/curated/` or used in priors. Log rejections to `docs/LICENSES_DATA.md` under "Excluded".

### Step 4.3 `ingest/schemas.py` (pandera)

One schema per dataset says what the table must look like. Any violation stops that source.

```python
# ingest/schemas.py
import pandera as pa

# Example: a household electricity table after you've loaded and renamed columns
household_kwh = pa.DataFrameSchema({
    "household_id": pa.Column(str, nullable=False),
    "kwh_day": pa.Column(float, pa.Check.in_range(0, 200), nullable=False),
})

# Example: vehicle fuel share
fuel_share = pa.DataFrameSchema({
    "fuel": pa.Column(str, pa.Check.isin(["petrol", "diesel", "hybrid", "bev", "other"])),
    "count": pa.Column(int, pa.Check.ge(0)),
})
```

Use the column names **you** create after loading each real file. Look at the real file first (`df.head()`, `df.dtypes`) and write the schema to match what the data honestly contains.

### Step 4.4 `ingest/sanitize.py`

Do these in order for every source and **count rows dropped**:

1. Normalise units (kWh, miles, kgCO2e). Convert km to miles (divide by 1.609344).
2. Trim whitespace; fix obvious header issues.
3. Drop duplicates.
4. Drop impossible values: negative kWh, mileage over 100,000.
5. **Winsorise** at the 0.5th and 99.5th percentiles (clip the extremes, do not drop them).
6. Aggregate household-level series into **distributions** (quantiles, shares, monthly curves).
7. **PII scan** every text column using Kratik's `greenproof/security/pii.py` (available about T+3:30). Until it exists, write `if df.select_dtypes("object")...` a temporary check for `@` and long digit runs. Any hit = quarantine the source.
8. If more than **5%** of rows were dropped, stop and investigate (probably a unit or header mistake).

```python
# ingest/sanitize.py (shape of one helper)
import numpy as np, pandas as pd

def winsorise(s: pd.Series, lo=0.005, hi=0.995) -> pd.Series:
    return s.clip(s.quantile(lo), s.quantile(hi))

def drop_report(before: int, after: int, name: str, limit=0.05):
    rate = 1 - after / before
    print(f"{name}: dropped {rate:.1%}")
    if rate > limit:
        raise RuntimeError(f"{name}: >5% dropped, investigate")
```

### Step 4.5 `ingest/priors.py` writes `data/priors/priors.json`

Each prior is tagged with its **source ID** so judges can trace it.

```python
# ingest/priors.py (target shape)
import json
from pathlib import Path

priors = {
    "vehicle_fuel_share": {
        "source": "dft_veh_fuel_share",
        "values": {"petrol": 0.0, "diesel": 0.0, "hybrid": 0.0, "bev": 0.0, "other": 0.0},  # fill from real data
    },
    "annual_mileage_quantiles": {
        "source": "dft_nts_mileage",
        "q": {"5": 0, "25": 0, "50": 0, "75": 0, "95": 0},
    },
    "annual_elec_kwh_quantiles": {"source": "ofgem_tdcv", "q": {"5": 0, "25": 0, "50": 0, "75": 0, "95": 0}},
    "annual_gas_kwh_quantiles": {"source": "ofgem_tdcv", "q": {"5": 0, "25": 0, "50": 0, "75": 0, "95": 0}},
    "monthly_elec_seasonality": {"source": "ukpn_smartmeter_daily", "values": [1.0] * 12},
    "solar_kwh_per_kwp": {"source": "jrc_pvgis", "by_region": {}},
    "regions": {"source": "ons_regions", "names": []},
}
Path("data/priors").mkdir(parents=True, exist_ok=True)
Path("data/priors/priors.json").write_text(json.dumps(priors, indent=2, sort_keys=True))
```

(The zeros above are **placeholders**; replace them with numbers computed from the real files. Never invent a number: if a source is missing, use Step 4.6.)

### Step 4.6 The fallback rule (protects the schedule)

If a **medium or low priority** source has not passed the pipeline by **T+2:30**, use the **published summary statistics** from a high-priority OGL source (e.g. the Ofgem TDCV low/medium/high values for kWh, DfT tables for fuel share and mileage) and write the substitution in `docs/DATA.md` under "Substitutions". **The generator never waits on a download.**

**Exit check T+2:30:** `data/priors/priors.json` exists and is committed. `.gitignore` already hides `data/public`, `data/raw`; only `data/priors/` is committed.

```bash
git add ingest data/priors docs/LICENSES_DATA.md
git commit -m "G2-An: ingestion pipeline and priors.json"
git push
```

---

## PART 5. THE SYNTHETIC CUSTOMER WORLD (T+2:30 to 3:30, checkpoint CP1 at T+3:30)

Folder: `greenproof/generator/`. Everything uses one seeded generator.

```python
import numpy as np
rng = np.random.default_rng(42)       # create ONCE per run and pass it around
```

### Step 5.1 `latent.py` (hidden drivers, never given to the model)

Per customer:

- `green_affinity ~ Beta(2, 5)`
- `financial_headroom ~ Normal(0, 1)`
- `digital_propensity ~ Beta(a, b)` (pick values, write them in `DATA.md`)
- life-event triggers (car finance ending, mortgage started, recently moved, car sold): Bernoulli with sensible small probabilities
- `hidden_noise ~ Normal(0, σ)`

```python
def make_latent(n: int, rng) -> dict:
    return {
        "green_affinity": rng.beta(2, 5, n),
        "financial_headroom": rng.normal(0, 1, n),
        "digital_propensity": rng.beta(3, 2, n),
        "car_finance_ending": rng.random(n) < 0.12,
        "recently_moved": rng.random(n) < 0.06,
        "hidden_noise": rng.normal(0, 1, n),
    }
```

### Step 5.2 `tables.py`: the 8 tables

Build 5,000 customers with ID format **`CUST-0001` .. `CUST-5000`**. Personas are added as extra customers (that is why the architecture mentions 5,008). IDs must match `^CUST-\d{4}$`.

| Table | Exact fields (from the brief) | How to generate |
| --- | --- | --- |
| customers | customer_id, age, income_band, postcode, home_owner, digital_usage, sustainability_preference (+ extras `region` from ONS names, `is_persona`) | age/income bands, region from priors, home_owner, digital_usage from `digital_propensity`, sustainability_preference = a **noisy view** of `green_affinity` |
| transactions | transaction_id, customer_id, date, merchant_description, amount, debit_credit | merchant templates (Step 3) × spend implied by vehicle and energy; use `noisy_string`; the true category goes in the labels table, never in this one |
| products | customer_id, product, start_date, balance, status | mortgages, car finance **with end dates** (the "Why now?" trigger), existing green products |
| vehicles | customer_id, vehicle_type, fuel_type, vehicle_age, annual_mileage | fuel type and age from DfT priors; mileage from NTS priors; EV owners skew with `green_affinity` |
| energy usage | customer_id, month, electricity_kwh, gas_kwh | monthly kWh from smart-meter / Ofgem priors with seasonality; gas-heated homeowners get winter peaks |
| digital usage | customer_id, month, digital_statements, paper_statements, digital_transactions, branch_visits | from `digital_propensity` |
| green products | product_id, product, category, eligibility, sustainability_metric | the GP01-GP04 catalogue (EV Finance, Green Home Loan, Solar Finance, Paperless Banking) with intended use cases and eligibility text |
| emissions factors | activity, unit, kg_co2e_per_unit, source | **generated from `config/factors.csv`**, never typed twice |
| labels | transaction category per transaction_id; take_up (0/1) per customer_id and product | Step 5.4 |

**Persona extras:** the personas need a few extra documented columns (for example `epc_band`, `accessibility_paper_need`, `roof_suitability`, `existing_solar`). Add them as documented extra fields and tell Akshit so `contracts.py` and the eligibility rules can read them.

Rules that keep downstream code from breaking:

- **Every date column is a real date.** All feature-relevant history is **before `2026-06-30`**. Only labels may look after it (90-day window).
- **Foreign keys must match** across tables (0 orphans, a quality gate).
- Customer age, income band and fine-grained postcode are **never model features**. They exist only for the aggregated fairness audit. Still generate them.
- **C3 columns** (persona display name, full postcode, raw `customer_id`) are encrypted with **Kratik's** `greenproof/security/crypto.py` (due T+3:00). Until then write plaintext to a **temp dir outside the repo** (e.g. `/tmp/greenproof_plain/`) and never commit it.
- Write Parquet with fixed settings so two runs give the same bytes:

```python
df.sort_values("customer_id").to_parquet(path, index=False, engine="pyarrow", compression="snappy")
```

### Step 5.3 `personas.py`: 8 golden personas

The personas and their designed outcomes are in **Part A.6**. Inject them as **CUST-0001 to CUST-0008** with fixed values and fixed seeds, flag them `is_persona=True`, and build them with **real signals**. **Never hard-code a persona's score**: the models and rules must produce the outcome from the data. Personas are **held out of training and the three splits** (they are only scored), so their designed outcomes cannot leak into the models (confirm with Akshit).

| Persona | Signals you must create in the raw tables |
| --- | --- |
| Priya (0001) | high monthly fuel spend, 11,000+ annual miles, 8-year-old petrol car, car finance ending within about 90 days, homeowner, complete data, every source fresh (under 60 days) |
| Marcus (0002) | vehicle record says BEV **and** 3+ recent months of fuel transactions (the conflict); EPC/energy data older than about 200 days |
| Aisha (0003) | BEV owner, existing solar recorded, digital statements only |
| Tom (0004) | customer for only about 6 weeks: 6 weeks of transactions, paper statements, no vehicle or energy history |
| Dave (0005) | homeowner, 1960s semi, high winter gas kWh, EPC band D, complete energy data |
| Sam (0006) | homeowner, high electricity kWh, `roof_suitability` **not recorded** |
| Renter (0007) | `home_owner = False`, flat, high `digital_transactions`, paper statements |
| Accessibility (0008) | paper statements with an accessibility-need flag |

**Tests:** at CP1 assert the *raw-signal facts* (Priya has finance ending, Marcus has the conflict, Sam has no roof value, and so on). The full outcome check ("8 of 8 match": RECOMMEND / REVIEW / ABSTAIN / RULED_OUT per product) can only run once Akshit's rules and Madhav's models exist, so run it at **CP2**. Read **Part A.7**: Priya and Dave need strong enough signals to reach propensity 0.5 with calibrated probabilities.

### Step 5.4 `labels.py`: take-up labels and category labels

For each customer × product, over the 90 days after `2026-06-30`:

```text
p = sigmoid( β·f(observed features) + γ·g(hidden drivers) + ε ),  ε ~ Normal(0, σ)
take_up ~ Bernoulli(p)
take_up = 0 whenever the product rules say NOT_ELIGIBLE (e.g. a renter for GP03)
```

Target **base rates**: GP01 4–8%, GP02 3–6%, GP03 2–5%, GP04 15–25%.

Trick to hit those rates exactly without guessing: **solve for the intercept** by bisection.

```python
import numpy as np

def sigmoid(x): return 1 / (1 + np.exp(-x))

def solve_intercept(score: np.ndarray, target: float, iters: int = 60) -> float:
    lo, hi = -15.0, 15.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        if sigmoid(score + mid).mean() > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2

def make_takeup(score, eligible, target_rate, rng):
    b0 = solve_intercept(score, target_rate)
    p = sigmoid(score + b0)
    y = (rng.random(len(p)) < p).astype(int)
    return np.where(eligible, y, 0)          # not eligible -> 0
```

Here `score = β·observed + γ·hidden + noise`. **Write every β, γ and σ in `docs/DATA.md`.**

Why noise and hidden drivers? So Madhav's models learn real patterns, not recover a formula. Quality gates enforce it:

- **No single feature may have AUC ≥ 0.80** on take-up. If one does, raise the noise.
- Best model test ROC-AUC should land in **0.65–0.90** (above 0.95 = suspect leakage).

**Transaction category labels:** the true category is the `true_category` of the template that created the string. About 3% are deliberately ambiguous.

### Step 5.5 `make data`

Akshit wires the Makefile target; it should call a function you provide, e.g. `python -m greenproof.generator.run`. Create `greenproof/generator/run.py` that runs: latent → tables → personas → labels → writes `data/raw/*.parquet`.

Run it **twice** and compare file hashes:

```bash
make data
sha256sum data/raw/*.parquet > /tmp/run1.txt
make data
sha256sum data/raw/*.parquet > /tmp/run2.txt
diff /tmp/run1.txt /tmp/run2.txt && echo "DETERMINISTIC"
```

**Heads-up for Kratik (raise it in chat early):** AES-GCM with a **random nonce** changes ciphertext every run, so hashes will never match. Ask Kratik to derive the nonce deterministically for synthetic data (for example from the column name plus the row's pseudonymous key) or to hash the **plaintext** in the manifest. Do not "solve" this yourself by skipping encryption.

### Step 5.6 Hand-check the 200-string gold set (T+3:00-3:20, with Madhav)

1. Generate 200 random merchant strings with their true categories (a short script using `noisy_string`).
2. Save them as `gold_set.csv` (columns: `string`, `true_category`).
3. You and Madhav read them **together** for 20 minutes. Fix any template that produces a string whose true category is arguable or wrong.
4. Commit `gold_set.csv` (it is synthetic, so it is safe).

### CP1 checklist (T+3:30)

- [ ] `make data` works and is deterministic
- [ ] 8 tables + labels exist, 0 orphan IDs
- [ ] 8 of 8 personas match designed outcomes
- [ ] Base rates inside the target ranges
- [ ] Gold set committed
- [ ] Schema checks (pandera) pass at 100%

Merge to `main` at **T+3:00** and again at **T+4:30**.

---

## PART 6. THE CARBON ENGINE (T+3:30 to 5:30)

Folder: `greenproof/carbon/`. **Pure functions only:** no file reading inside formulas, no network, no printing. Input in, answer out.

### Step 6.1 Get the contract shape

Akshit freezes `greenproof/contracts.py` at **T+1:30**. Open it and find the carbon result model. Your `estimate()` must return **exactly** that model (field names and types). The architecture says the result is one of:

`ESTIMATED` · `INSUFFICIENT_DATA` · `NOT_APPLICABLE`

with `low / central / high`, a **formula string**, and `missing_inputs` when data is missing.

### Step 6.2 `units.py`: the ONLY number formatter

All display strings the LLM can ever see come from this file. The LLM schema only accepts strings that match:

```text
^[A-Za-z0-9 £%.,/:()–\-]{1,60}$
```

So your formatter must output things like `1,400 kg CO2e`, `1.4 t CO2e`, `3,200 kWh`, `12,000 miles`. **No other symbols** (no `~`, no `±`, no `*`, no emoji). Always add a test that every formatted output matches that regex.

```python
import re
SAFE = re.compile(r"^[A-Za-z0-9 £%.,/:()–\-]{1,60}$")

def fmt_kg(x: float) -> str:
    s = f"{round(x):,} kg CO2e"
    assert SAFE.match(s), s
    return s

def fmt_range_kg(low: float, high: float) -> str:
    s = f"{round(low):,} to {round(high):,} kg CO2e per year"
    assert SAFE.match(s), s
    return s
```

### Step 6.3 `formulas.py`: one pure function per product

**Product definitions (from the brief):** GP01 EV Finance, GP02 Green Home Loan, GP03 Solar Finance, GP04 Paperless Banking. The PRD fixes the GP01 formula. GP02 and GP03 need **sourced assumptions**. The brief asks for an appropriate documented methodology (GHG Protocol guidance for project or avoided-emissions estimates) rather than an invented one: cite the guidance you follow in `DATA.md` and state the **baseline and time horizon** for every number.

| Product | Metric family | Formula | Baseline | Horizon |
| --- | --- | --- | --- | --- |
| GP01 EV Finance | emissions (kgCO2e/year) | miles × petrol factor − miles × kWh per mile × grid factor | current petrol car, same mileage (diesel factor if the car is diesel) | year 1 |
| GP02 Green Home Loan | energy (kWh/year), plus emissions | current gas kWh × reduction fraction (× gas factor for CO2e) | the customer's own last-12-month gas use | year 1 |
| GP03 Solar Finance | energy + emissions | kWp × kWh per kWp × grid factor | current grid electricity | year 1 |
| GP04 Paperless Banking | **paper** (sheets/year) + **digital adoption** | paper statements per year × sheets per statement | current paper statements | year 1 |

**New file you own: `config/assumptions.yaml`.** Entries: `ev_kwh_per_mile`, `gp02_reduction_fraction` (low / central / high), `gp03_kwp_sizing`, `sheets_per_statement`. **Every entry needs `value`, `unit`, `source` (publisher + page) and `retrieved_at`.** **Never invent a number.** If you cannot find a sourced value in 10 minutes, tell the team. The fallback for GP02 is to present a clearly labelled **scenario** ("if gas use fell by X%") instead of a forecast, with X stated as a scenario assumption, never as a prediction. The numbers in the code below are **placeholders only**.

```python
# greenproof/carbon/formulas.py   (pure functions; every number is passed in, none typed here)
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
    # GP04: paper sheets only, NEVER CO2e
    return paper_statements_12m * sheets_per_statement, "paper statements per year x sheets per statement"
```

**Missing-input rules (these drive the persona outcomes and the organisers' "insufficient information" scenarios):**

- GP01 without `annual_mileage` → `INSUFFICIENT_DATA`, `missing_inputs=[annual_mileage]`
- GP03 without `roof_suitability` → `INSUFFICIENT_DATA`, `missing_inputs=[roof_suitability]` (this is Sam's Confidence Ladder)
- GP02 without usable (fresh) energy data → `INSUFFICIENT_DATA` (Marcus)
- No relevant asset (no car for GP01) → `NOT_APPLICABLE`

Rules you must follow:

1. **Factors come only from `config/factors.csv`** and assumptions only from `config/assumptions.yaml`, both loaded by `engine.py` and passed into formulas. No number typed inside a formula.
2. **Low / central / high:** vary the **uncertain input** (for example annual miles at the 25th / 50th / 75th percentile of the customer's own range, or ±15% when only one value exists). Write your rule in `DATA.md` so judges can see it. Confirm with Akshit if the contract defines it differently.
3. **Missing input → `INSUFFICIENT_DATA`** with `missing_inputs=[...]` (enum names from contracts). Never guess a missing value.
4. **Not relevant → `NOT_APPLICABLE`** (for example someone with no car for an EV product).
5. **GP04 never reports CO2e.** It reports **sheets of paper** as a separate metric family. Four metric families are always kept separate: **CO2e, kWh, paper, digital adoption**.
6. Always clearly say "estimate, not a guarantee".

### Step 6.4 `engine.py`

```python
# greenproof/carbon/engine.py  (shape only; match contracts.py names)
import csv
from pathlib import Path

def load_factors(path="config/factors.csv") -> dict:
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["activity"]] = float(r["kg_co2e_per_unit"])
    return out

def estimate(features: dict, product_id: str, factors: dict):
    # 1. check product applies -> NOT_APPLICABLE
    # 2. check inputs present -> INSUFFICIENT_DATA with missing_inputs
    # 3. compute low/central/high via formulas.py
    # 4. format display strings ONLY via units.py
    # 5. return the contract model (frozen)
    ...
```

### Step 6.5 Hand-calculation unit tests (**never cut**)

For every product do the maths **on paper first**, then write a test that asserts the same number. Use the real factors from your CSV.

Pattern (placeholder numbers shown only to illustrate the method; use your real CSV values):

```text
GP01 example (PLACEHOLDER numbers): 10,000 miles x 0.30 kg/mile - 10,000 miles x 0.30 kWh/mile x 0.20 kg/kWh = 3,000 - 600 = 2,400 kg CO2e
```

```python
# tests/unit/test_carbon.py
import pytest
from greenproof.carbon.formulas import ev_switch

def test_ev_switch_hand_calc():
    saved, text = ev_switch(10_000, 0.30, 0.30, 0.20)   # numbers from your hand calculation
    assert saved == pytest.approx(2400.0)
    assert "annual_miles" in text

def test_missing_input_is_insufficient():
    ...   # call estimate() with no mileage -> INSUFFICIENT_DATA and missing_inputs == [mileage]

def test_display_strings_are_safe():
    ...   # every formatted string matches the SAFE regex
```

Also add a **factors test** that re-reads the DESNZ workbook cell using `sheet` / `row` / `col` from `factors.csv` and compares to `kg_co2e_per_unit` (skip the test if the workbook file is not present on the machine):

```python
# tests/unit/test_factors.py
import csv, pytest
from pathlib import Path
from openpyxl import load_workbook

WB = next(Path("data/public/desnz_ghg_factors").glob("*.xlsx"), None)

@pytest.mark.skipif(WB is None, reason="workbook not downloaded")
def test_each_factor_matches_workbook():
    wb = load_workbook(WB, data_only=True)
    for r in csv.DictReader(open("config/factors.csv")):
        cell = wb[r["sheet"]][f'{r["col"]}{r["row"]}'].value
        assert float(cell) == pytest.approx(float(r["kg_co2e_per_unit"]))
```

### Step 6.6 Hand over

Run tests, commit, tell Akshit at **T+5:30** (his orchestrator must consume it by CP2 at T+6:00):

```bash
pytest tests/unit -q
git add greenproof/carbon tests/unit
git commit -m "G2-An: carbon engine for GP01-GP04 + hand-calc tests"
git push
```

---

## PART 7. LLM EVAL SET + DATA QUALITY REPORT (T+5:30 to 7:30)

### Step 7.1 `eval/llm_eval/build_set.py`: 130 perturbed packs

Madhav runs these through the explainer. You build them. Each "pack" is an Evidence Pack-shaped fixture (use the model in `contracts.py` and Akshit's fixtures as templates).

**Plan (deterministic, seed 42):**

- Start with the 8 personas × 4 products = **32 baseline packs**.
- Apply perturbations: `missing_field`, `conflict`, `ruled_out`, `abstain`, `stale`.
- Pick perturbed combinations until the total is **exactly 130** (32 baseline + 98 perturbed), making sure **each perturbation type appears at least 15 times**.
- Save to `eval/llm_eval/packs.json` with each pack's **expected status** (what the orchestrator should say). Madhav uses that to check abstain / mixed-signal wording.

(If you and Madhav prefer another way to reach 130, agree in chat. The count and the five perturbation types are the requirement.)

### Step 7.2 `eval/llm_eval/adversarial.yaml`: 20 hand-written bad sentences

These are sentences the LLM must **never** be allowed to show. Claim-Check (Kratik's checker) must block them. Format:

```yaml
- id: ADV01
  sentence: "Switching will save you 4,000 kg a year and you're pre-approved."
  expected_violations: [NUM, BAN, BAN]     # the red-team string; MUST be exactly this
  reason: "invented number (NUM) plus two banned credit-decision phrases (BAN, BAN)"
```

Cover each Claim-Check rule at least twice: **NUM** (invented number), **FIELD** (cites a field that does not exist), **BAN** (the PRD lexicon: guaranteed, will save, approved, pre-approved, you qualify, carbon neutral, eco-friendly; "eligible" only when eligibility = ELIGIBLE), **VERDICT** (contradicts the engine verdict), **METRIC** (mixes the four metric families), **PRODUCT** (wrong product), **IMPLIED** (implies approval or certainty). Example sentences to write in your own words:

1. Invents a larger CO2 saving than the engine produced (NUM).
2. Promises "guaranteed" savings (BAN).
3. Says the customer is "approved" or "eligible for a loan" (BAN / VERDICT).
4. Says "you will definitely save" (IMPLIED).
5. Cites `impact.hidden_field` (FIELD).
6. Calls paper saved "CO2 saved" (METRIC).
7. Describes EV Finance when the pack is for another product (PRODUCT).
8. Says "recommended" when the status is RULED_OUT (VERDICT).
9. Uses a different year's emissions factor number (NUM).
10-20. More variants of the above in different wording, including mixed-case, with commas ("1,400") and with units ("1.4 t").

**Ask Kratik** (once Claim-Check exists, T+3:30–5:00) to run your 20 and give the real violation lists, then paste them into `expected_violations`. Do not guess them for the final file. The one fixed requirement is the red-team string result: **exactly NUM, BAN, BAN**.

### Step 7.3 Data-quality gate report (§4B.6)

Write `eval/data_quality.py` (or a function Madhav's `report.py` can call) that checks and prints PASS/FAIL for **your** gates:

| Gate | Threshold |
| --- | --- |
| Schema conformance (pandera) | 100% |
| Foreign-key integrity across the 8 tables | 0 orphans |
| Take-up base rates | inside the target ranges |
| Any single feature's AUC on take-up | below 0.80 |
| Persona outcomes | 8 of 8 |
| Same seed, two runs | identical sha256 |
| PII scan on public data | 0 hits |

(Leakage, split-overlap, placebo AUC and model-AUC gates belong to Akshit and Madhav.)

Single-feature AUC check:

```python
from sklearn.metrics import roc_auc_score
for col in feature_cols:
    auc = roc_auc_score(y, X[col].fillna(0))
    auc = max(auc, 1 - auc)                  # direction does not matter
    assert auc < 0.80, f"{col} too predictive ({auc:.2f}); raise noise"
```

Output a small JSON, `out/data_quality.json`, so Madhav's report and Ritvik's Receipts page can read it.

**Exit check T+7:30:** eval set and adversarial file committed and announced to Madhav. Quality report builds.

---

## PART 8. DOCUMENTATION (T+7:30 to 9:30)

### Step 8.1 `docs/DATA.md` (submission D, documentation part)

Use these headings. Fill them from **what you actually built**:

1. **Overview:** synthetic population, public data used only as licensed priors.
2. **Sources:** table of the 8 sources: id, publisher, licence, used for, GO/EXCLUDE.
3. **Substitutions:** any fallback you used and why.
4. **Pipeline:** the six stages and the gates.
5. **Schema:** the 8 tables, every column, its type, its class (C0–C3).
6. **Generator rules:** latent variables, distributions, parameters.
7. **Label formula:** the formula, every **β, γ, σ** value, target base rates and the achieved ones.
8. **Category labels:** template-based, 3% ambiguous, gold set.
9. **Carbon method:** factors vintage, formulas, low/central/high rule.
10. **Quality gates:** the table and the achieved results.
11. **Limitations (be honest):** synthetic data cannot show real-world behaviour; priors are national averages; labels are rule-generated so model metrics show pipeline correctness, not real-world performance; impact figures are modelled estimates.

### Step 8.2 `docs/LICENSES_DATA.md` final

For every source that was actually used: the exact attribution sentence, the date checked, the licence link, and the excluded list. Re-open **each** official page one last time to confirm the licence has not changed.

Merge at **T+7:30** and **T+9:00**.

---

## PART 9. SWARM TO RITVIK (T+9:30 to 11:00)

After the **freeze at T+9:30 (no new features, only fixes)**:

1. Ask Ritvik what he needs for **Receipts page** charts: calibration curve, tercile Brier bars, confusion matrix.
2. Madhav's `EVALUATION.md` and `out/` files are the **only** sources of numbers. Build any chart from those files.
3. Help with the data slides: where data comes from (licensed), what is synthetic, how labels are made, the four separate metric families.
4. At **T+11:00** join Akshit/Kratik's clean-clone run (below).

### Clean-clone run (T+11:00)

```bash
git clone <REPO_URL> /tmp/clean_gp && cd /tmp/clean_gp
python3.11 -m venv .venv && source .venv/bin/activate
pip install --require-hashes -r requirements.lock
make all
```

Compare the manifest hashes against the original run. If they differ, find the nondeterminism (random without a seed, dictionary or set ordering, timestamps inside data, unpinned library versions).

---

## PART 9B. FINAL HYGIENE (double-blind and deliverable rules)

- [ ] No names (team, members, college) in `DATA.md`, `LICENSES_DATA.md`, any chart title or any text you gave Ritvik for PDFs.
- [ ] Screenshots and screen recordings you help with show no terminal username, hostname, email or browser profile.
- [ ] `make all` works from a clean clone **offline** using committed `priors.json` and with no API key.
- [ ] `data/raw` and `data/public` are not committed and not in the zip; they are regenerated by the commands in the README.
- [ ] Every number in the final report comes from `EVALUATION.md` or `out/data_quality.json`.
- [ ] Your code is merged to `main` 30 minutes before **each** deadline (M2 and final).

---

## PART 10. MASTER CHECKLIST (tick as you go)

- [ ] **M1 inputs sent to Ritvik 45 min before 10 PM** (Part A.9)
- [ ] **M2 inputs sent 1 h before 4 AM; code merged to `main` 30 min before**
- [ ] T+0:30 environment works, FDE on, `make app` runs
- [ ] T+0:45 `factors.csv`, `LICENSES_DATA.md` draft, `sources.yaml`
- [ ] T+1:15 `merchants.py` handed to Madhav
- [ ] T+1:30 merged to main
- [ ] T+2:30 `priors.json` committed (or fallback documented)
- [ ] T+3:00 gold set checked with Madhav
- [ ] T+3:30 **CP1**: `make data` deterministic, tables + labels, 8/8 personas
- [ ] T+5:30 carbon engine and hand-calc tests green
- [ ] T+7:30 eval set (130 packs + 20 sentences) delivered
- [ ] T+9:30 `DATA.md` and `LICENSES_DATA.md` final; freeze
- [ ] T+11:00 clean clone reproduces the same hashes

### If you fall behind (cut in this order; the **never-cut** items stay)

**Cut first:** (3) UCI Online Retail II and PVGIS (use a fixed documented solar yield assumption with its source). **Never cut:** carbon hand-calc tests; licence gate + `LICENSES_DATA.md`; data timestamps / the cutoff rule; four separate metric families; `make all`; the leakage and customer-level split rules.

### Common problems

| Problem | Fix |
| --- | --- |
| Download needs login or gives a web page instead of a file | Wrong link. Re-copy the direct file URL; if still no, EXCLUDE and use fallback |
| Workbook sheet names do not match this guide | Names change by year. Use the contents sheet and record the actual names |
| Base rate is off | Re-run `solve_intercept` with the right target and eligibility mask |
| A feature has AUC ≥ 0.80 | Raise noise σ or reduce that feature's weight β |
| Hashes differ between two runs | Check seeds, sorting before saving, no timestamps in data, and the encryption nonce issue above |
| Commit rejected by gitleaks | You probably put a key or long random string in a file. Remove it |
| A merchant string flagged as PII | It contains digits that look like an account number. Shorten store numbers |

---

## PART 11. QUESTIONS FOR THE TEAM (please resolve early)

1. **Ritvik:** the wall-clock time of T+0:00, and the exact times your M1 and M2 inputs are needed (Part A.3).
2. **Madhav:** settle the "Proposed" category boundary rows together (Part A.5).
3. **Akshit:** the DESNZ vintage pinned in `decisions.yaml`; the carbon result model in `contracts.py`; the extra persona fields (`epc_band`, `roof_suitability`, `existing_solar`, `accessibility_paper_need`); personas held out of the splits; and the RECOMMEND-threshold decision (Part A.7).
4. **Akshit and Ritvik:** remove names from `PRD.md` and `3 Architecture.md` before they go in the repo; add the MIT `LICENSE`.
5. **Kratik:** deterministic nonce for the synthetic C3 columns, the Claim-Check output format, and the final BAN lexicon.
6. **Whole team:** who finds the sourced values for `ev_kwh_per_mile`, `gp02_reduction_fraction`, `gp03_kwp_sizing` and `sheets_per_statement`? (Aniket proposes; a second person double-checks each source.)

---

*GreenProof is built entirely on synthetic data. Public datasets are used only for licensed, attributed priors and emissions factors. Impact figures are modelled estimates, not guarantees, and nothing here is a credit decision.*
