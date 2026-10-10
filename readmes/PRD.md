# GreenProof — 14-Hour Execution PRD

Oct 10, 2026 · @Ritvik Bansal

## Executive summary

GreenProof ships in 14 hours as one Python codebase: a seeded synthetic-data and ML pipeline, two deterministic engines (eligibility, carbon), a guarded LLM layer, and a two-page Streamlit app. Two showstoppers sit on top, and each one doubles as a graded evaluation artefact rather than a demo trick.

**Why this shape wins.** 65% of the rubric is engineering rigour (ML 20, sustainability 15, LLM 15, architecture 15). UX is 5%. Most teams will ship a chatbot, an LLM that does carbon arithmetic, and one AUC number. We ship the opposite: every number has a source, every refusal is a designed state, and every LLM sentence is checked before display.

**The two killer spikes** (chosen for demo impact per hour of effort across all 13 input docs):

1. **Claim-Check firewall** — a deterministic sentence-level verifier between the LLM and the screen, plus a 150-case LLM evaluation set. Live moment: inject a fake claim, watch it get blocked, counter ticks up.
2. **Scenario Lab** — a judge-facing panel that mutates a persona live (set vehicle to EV, remove mileage, add a conflicting signal, make data stale) and recomputes all three verdicts in under a second, with a diff. The same scenarios run headlessly as a pytest suite that pre-empts the organisers' four scenario tests.

**Deliberately cut to slides:** Promise vs. Proof, multi-session memory, Spending Hub, auth, React, PostgreSQL, PCAF financed emissions, GP05/GP06, regional maps, What-If sliders beyond mileage.

**Locked in hour 0 (no re-litigating later):**

| Decision | Choice | Why |
| --- | --- | --- |
| Cutoff date | 2026-06-30 | 12 months of history before it |
| Outcome window | 90 days after cutoff | Short enough to act on; stated everywhere |
| Factor vintage | One DESNZ/Defra release, pinned; every row copied from the primary workbook with sheet and row | Mixed vintages are the most common silent error in the inputs |
| Public EV charging | Category = Fuel (transport energy) | Keeps ICE and EV transport spend comparable |
| Dual-fuel supplier bill | Category = Utilities; split later from the energy table | Keeps FR2 mutually exclusive |
| Taxi / ride-hail | Category = Other | Public Transport = scheduled mass transit only |
| LLM | One small model, temperature 0, cached by input hash; template fallback always on | The app must run with no API key |
| Model per product | LightGBM, isotonic-calibrated; baselines = logistic regression + rule heuristic | Required baseline comparison |
| Synthetic population | 5,000 customers + 8 named golden personas | Fast to regenerate; personas drive the demo |

## 1. Product Identity & Competitive Moat

**Name:** GreenProof — *the green recommendation that shows its receipts.*

**Hook:** Carbon trackers tell you your footprint; GreenProof tells you your next step, proves why, and says "I don't know" when the data can't support a claim.

**Core rule, on every screen:** ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies.

### The competitive wedge

| What \~90% of teams will ship | What GreenProof ships |
| --- | --- |
| A chatbot or an LLM that "estimates" carbon | LLM sees pre-formatted numbers only; a verifier blocks any number not in the Evidence Pack |
| One "Green Score" blending likelihood, eligibility and impact | Three badges that never merge: Likelihood (ML) · Eligibility (rules) · Impact quality (carbon engine) |
| Raw probability shown as "confidence" | Composite confidence (completeness × recency × ensemble stability × in-distribution), validated: error falls as confidence rises |
| Random row split, AUC 0.98 | Customer-level + temporal split, leakage test, placebo test, baseline lift, calibration curve |
| Only happy-path demos | Refusals as product: RULED\_OUT with the rule that fired, ABSTAIN with the one missing field, REVIEW for mixed signals |
| Paperless reported as CO2e | Four separate metric families: CO2e, kWh, paper sheets, digital adoption |
| Static screenshots of edge cases | Scenario Lab: judges flip a toggle and watch verdicts change live, backed by an automated pass/fail suite |

### Rubric exploit

- **ML & recommendation quality (20%) + Sustainability (15%) → the honest pipeline.** Latent-variable synthetic labels (not trivially separable), customer-level splits with a leakage test, two baselines, calibrated LightGBM, validated confidence, and a carbon engine with pinned factors, ranges, abstain states and hand-calculated unit tests. All metrics come from one auto-generated evaluation report.
- **GenAI/LLM (15%) + Explainability & RAI (10%) → Claim-Check.** A deterministic sentence verifier plus a 150-case evaluation set scored on numeric fidelity, unsupported-claim rate, banned-phrase rate, product mapping and abstain wording, compared against a naive prompt. The live hallucination trap makes it memorable.
- **Technical architecture (15%) + Business relevance (15%) → contracts and the Scenario Lab.** Pure-function engines behind typed Pydantic contracts, a one-command reproducible run, cached LLM, measured latency; the cockpit drills Customer → Opportunity → Evidence → Impact → Action, and the Scenario Lab proves the four organiser scenarios before judges ask.

## 2. 14-Hour Feature Scope & Architecture

P0 is one end-to-end loop that is demoable by hour 7 on fixtures and by hour 9 on real model output. P1 adds exactly two spikes. Everything else is a slide.

### P0: The Core Engine (hours 0–7)

**The loop:** Judge opens a persona → orchestrator loads that customer's features → model, rules and carbon engine each return their verdict independently → orchestrator assigns a status and builds the Evidence Pack → explainer writes 2–3 sentences, Claim-Check verifies them → Proof Card renders three badges, evidence with dates, impact range with its formula, and one action.

| ID | Component | User action → logic → output | Owner | Done by |
| --- | --- | --- | --- | --- |
| P0-1 | Synthetic data generator | `make data` → latent profile per customer (green affinity, financial headroom, life-event triggers, hidden noise) → 8 tables + `DATA.md` with every generation and label rule; take-up = Bernoulli(sigmoid(f(observed) + g(hidden) + noise)) from the 90-day window only | BE | H4 |
| P0-2 | Customer 360 + features | `build_features(raw, cutoff)` filters `date < cutoff` → one wide row per customer with `as_of` per source, completeness and conflict flags → `features.parquet`; a pytest asserts no post-cutoff row is read | BE | H6 |
| P0-3 | Transaction categoriser (FR2) | Normalise string → ordered keyword rules (priority list in `config/categories.yaml`) → TF-IDF char n-gram logistic regression for leftovers → exactly one of 8 categories + confidence; low confidence → Other. Evaluated with macro-F1 on merchants unseen in training vs rules-only baseline | AI | H6 |
| P0-4 | Propensity models (FR3) | One LightGBM per GP01–GP04 with monotone constraints on obvious signals, isotonic calibration on validation; 70/15/15 customer-level split; baselines: logistic regression (3–5 features) and rule heuristic → `test_predictions.csv` | AI | H7 |
| P0-5 | Confidence | Weighted geometric mean of four \[0,1\] components (formula in Section 3); validated by Brier score per confidence tercile on the validation set → `confidence` + components on every row | AI | H7 |
| P0-6 | Eligibility rules + reason codes | `config/products.yaml` holds rules per product (e.g. GP01-R1 existing BEV and no second vehicle → NOT\_ELIGIBLE; GP02/GP03-R1 renter → NOT\_ELIGIBLE; GP03-R2 existing solar; GP04-R1 already fully digital or accessibility paper need) → ELIGIBLE / NEEDS\_VERIFICATION / NOT\_ELIGIBLE + rule IDs. Reason codes = top positive SHAP feature groups that also pass a raw-value threshold | Demo/Polish (rules), AI (codes) | H5 |
| P0-7 | Carbon engine (FR4) | Pure functions per product reading `config/factors.csv` (activity, unit, kgCO2e/unit, source, sheet, row, vintage) → ESTIMATED with low/central/high + formula string + baseline + horizon, or INSUFFICIENT\_DATA with `missing_inputs`, or NOT\_APPLICABLE. Paperless returns sheets saved only, never CO2e | Demo/Polish | H5 |
| P0-8 | Orchestrator | Combines the three verdicts into a status without modifying them (rules below) → Evidence Pack JSON per customer × product, cached to `out/packs/` | BE | H7 |
| P0-9 | Explainer + template fallback (FR5) | Evidence Pack subset → LLM returns JSON sentences each citing its fields → verifier v0 (numbers + banned words) → pass or template | AI | H7 |
| P0-10 | Customer Hub page | Four pathway tiles always visible; Proof Card with headline, Why-now tag, evidence chips with dates, three badges, impact drawer with formula/baseline/factor, action + "Not a credit decision"; Why-not list | FE1 | H7 |
| P0-11 | Cockpit page (FR6) | Four separate impact tiles, funnel (identified → eligible → recommended → taken up), propensity × impact quadrant by product, segment table, drill-down Customer → Opportunity → Evidence → Impact → Action | FE2 | H7 |
| P0-12 | Reproducible run | `make all` = data → features → train → score test → packs → eval report; fixed seed; writes `run_manifest.json` with hashes | BE | H9 |

**Status rules (orchestrator, in this order, thresholds in config):**

1. Eligibility NOT\_ELIGIBLE → **RULED\_OUT**. Card shows the rule in plain words; no action, no impact.
2. Conflict flag (e.g. vehicle = BEV while fuel spend persists) → **REVIEW**. "We're seeing mixed signals"; impact hidden; one confirming question.
3. Carbon INSUFFICIENT\_DATA or a critical feature missing → **ABSTAIN**. Propensity may show; no number; Confidence Ladder prompt names the single missing field.
4. Propensity ≥ 0.5 and confidence ≥ 0.6 → **RECOMMEND**.
5. Otherwise → **SOFT\_SURFACE** (visible, lower prominence, education wording).

The model still scores every customer × product (FR3 requires it); status only gates what is surfaced (FR7).

### P1: The 2 Showstopper Spikes (hours 7–11)

#### Spike A — Claim-Check firewall + LLM evaluation harness (owner: AI, eval set: Demo/Polish)

The verifier is a pure function `check(pack, sentences) -> CheckResult`, so it is testable without any LLM.

1. **Input to the LLM** is a minimal pack: product catalogue name, status, badge labels, reason-code phrases with values and dates, impact **display strings** already formatted by the engine, missing inputs, required disclaimer IDs. No raw transactions, names or postcodes.
2. **Output contract:** `{"sentences":[{"text":"…","fields":["impact.central","evidence.avg_monthly_fuel"]}]}`.
3. **Per-sentence checks**, each with a rule ID:
   - `NUM` every numeric token (regex over digits, %, £, kg, t, tonnes, kWh, miles) normalised ("1,400" = "1400"; "1.4 t" = "1400 kg") must be in the pack's allow-list.
   - `FIELD` every cited field exists in the pack.
   - `BAN` lexicon: guaranteed, will save, approved, pre-approved, you qualify, carbon neutral, eco-friendly; "eligible" allowed only when eligibility = ELIGIBLE.
   - `VERDICT` no recommending verbs when status is RULED\_OUT or REVIEW.
   - `METRIC` a GP04 sentence may not contain CO2/carbon terms.
   - `PRODUCT` product names must match the catalogue.
   - `IMPLIED` "halve", "double", "x times" and percentages need a backing field.
4. **On failure:** regenerate once; if it fails again, render the deterministic template built from the same pack. Every result writes a row to `claim_audit` (SQLite) → the cockpit's "claims blocked" counter.
5. **Evaluation set:** 150 packs = 8 personas × perturbations (missing field, conflict, ruled-out, abstain, prompt-injection text in a feedback field) + 20 hand-written adversarial sentences. Report numeric fidelity, unsupported-claim rate, banned-phrase rate, product-mapping accuracy, correct abstain wording, fallback rate, p50 latency, cost per 1,000 insights — governed pipeline vs a naive prompt allowed to compute.
6. **Stretch (only if green at H10):** metamorphic test — scale the impact range ×1.5 in the pack, regenerate, assert the old number disappears and the new one appears.

#### Spike B — Scenario Lab + automated scenario suite (owner: FE1 panel, BE endpoint, Demo/Polish suite)

1. **Toggles** on the Customer Hub side panel: Set vehicle to BEV · Remove annual mileage · Remove energy data · Add conflicting signal (BEV record + 3 months of fuel spend) · Make data stale (shift `as_of` back 200 days) · Mark as renter · Sell the car.
2. **Logic:** deep-copy the persona's raw rows → apply mutation (each is a small pure function in `scenarios/mutations.py`) → `build_features` for that one customer → `model.score`, `rules.evaluate`, `carbon.estimate` → orchestrator → new pack. LightGBM on one row is milliseconds; target < 1 s end to end.
3. **Diff panel:** status transition badge (e.g. RECOMMEND → RULED\_OUT), field-level table of what changed, and the cause line: "Rule GP01-R1 fired" or "Model rescored: `vehicle_fuel_type` changed".
4. **Invariance line:** the Lab only edits inputs; it never writes to a verdict. A pytest asserts that outputs equal a fresh run on the mutated data.
5. **Headless suite:** `tests/scenarios/*.yaml`, each `{persona, mutation, expected: {GP01: RULED_OUT, …}}`, 30+ cases covering the four organiser scenario types. Results JSON renders as a pass/fail table in the app and the eval report.

### P2: Cut for hackathon — pitch deck only

- **Promise vs. Proof:** estimated vs realised impact after take-up. Needs post-adoption data we would have to fabricate.
- **Persistent customer memory and three-strike back-off.** The Scenario Lab's "Sell the car" shows the event-driven retirement moment without a memory store.
- **Value-of-information prompts** ranking which missing field narrows the range most (we show the one missing field instead).
- **PCAF financed-emissions panel**, kept strictly separate from avoided estimates.
- **Regional heat map, What-If sliders, factor-vintage toggle.**
- **Spending Hub** (manual entry, CSV import, bills), auth, roles, PostgreSQL, React front end.
- **GP05 Green Investments, GP06 Green Loans** — same catalogue and engines, added by config.
- **Uplift modelling, Open Banking ingestion, installer marketplace, regulator audit export.**

## 3. Agent-Ready System Architecture

One Python repo, pure-function engines behind typed contracts, one directory per owner. Agents get a frozen `contracts.py` and a fixture file at hour 2, so nobody waits on anybody.

### Unified tech stack

| Layer | Choice | Why for agents + 14 hours |
| --- | --- | --- |
| Language | Python 3.11 only | One toolchain; every engine is importable by tests, API and UI |
| Contracts | Pydantic v2 models in `greenproof/contracts.py` | Agents generate code against typed schemas; FastAPI gets OpenAPI for free |
| Data | pandas + NumPy, Parquet files in `data/`, SQLite for `claim_audit` and scenario runs | Zero setup, inspectable, reproducible |
| ML | LightGBM, scikit-learn (logistic baseline, isotonic calibration, IsolationForest, TF-IDF), SHAP | All on the permitted list; fast on 5,000 rows |
| API | FastAPI (thin wrapper over `greenproof/` functions) | Satisfies "Dashboard and API"; UI can bypass it if it dies |
| UI | Streamlit multi-page (`app/pages/1_Customer_Hub.py`, `2_Cockpit.py`, `3_Receipts.py`) + Plotly | Brief's preferred stack; one file per FE dev = no merge conflicts |
| LLM | One small Anthropic or OpenAI model at temperature 0, JSON output, cache keyed by SHA-256 of the pack | Cheap, deterministic enough; cache makes reruns free and identical |
| Tests | pytest: unit (carbon hand calcs, rules), leakage, invariance, scenario suite, verifier | Same tests feed the eval report |
| Run | `Makefile`: `make data`, `make train`, `make packs`, `make eval`, `make app`, `make all` | Organisers may rerun; one command does it |

### System diagram / data flow

```text
[generator.py, seed=42] ──> data/raw/*.parquet  (customers, transactions, products,
                                                  vehicles, energy, digital, labels)
          │
          ▼
[categoriser] rules → TF-IDF LR → one of 8 categories per transaction
          │
          ▼
[features.build(raw, cutoff=2026-06-30)] ──> features.parquet  (+ as_of, completeness, conflict flags)
          │
  ┌───────┼──────────────────────┬───────────────────────────┐
  ▼       ▼                      ▼                           │
[model.score]           [rules.evaluate]            [carbon.estimate]
 propensity, confidence  ELIGIBLE / NEEDS_VERIF /    ESTIMATED range + formula /
 + SHAP reason codes     NOT_ELIGIBLE + rule IDs     INSUFFICIENT_DATA / NOT_APPLICABLE
  └───────┴──────────────────────┴───────────────────────────┘
          │   (three verdicts, never modified downstream)
          ▼
[orchestrator] status = RULED_OUT | REVIEW | ABSTAIN | RECOMMEND | SOFT_SURFACE
          │   ──> out/packs/{customer}_{product}.json   (Evidence Pack)
          ▼
[explainer] minimal pack ─> LLM (cached) ─> sentences + cited fields
          │
          ▼
[claimcheck.check] PASS ──────────────┐     FAIL ─> retry once ─> template
          │                           │              │
          ▼                           ▼              ▼
     SQLite claim_audit         FastAPI /api/*  <──── Streamlit pages
                                      ▲               (Customer Hub, Cockpit, Receipts)
                                      │
[scenario.run(persona, mutation)] ── mutate raw rows ─> features ─> same three engines ─> diff
```

### Repo layout = ownership map

```text
greenproof/
  contracts.py        # BE owns; frozen at H2, changes need a 2-line PR + Slack ping
  generator/          # BE
  features/           # BE
  categoriser/        # AI
  models/             # AI   (train.py, score.py, confidence.py, reasons.py)
  rules/              # Demo/Polish   (engine.py + config/products.yaml)
  carbon/             # Demo/Polish   (engine.py + config/factors.csv)
  orchestrator.py     # BE
  llm/                # AI   (explainer.py, claimcheck.py, templates.py, prompts/)
  scenarios/          # BE   (mutations.py, run.py)
api/main.py           # BE
app/pages/1_Customer_Hub.py   # FE1
app/pages/2_Cockpit.py        # FE2
app/pages/3_Receipts.py       # FE2 (eval metrics, scenario pass/fail, claims blocked)
app/client.py         # FE1; DEMO_MODE switch (live | cached | fixtures)
fixtures/*.json       # BE writes at H2 from contracts; FE builds against them
eval/                 # Demo/Polish   (report.py, llm_eval_set/, scenario yaml)
tests/                # each owner tests their own folder
```

### Confidence formula (P0-5)

```latex
\text{confidence} = c_{\text{complete}}^{0.35}\; c_{\text{recency}}^{0.15}\; c_{\text{stable}}^{0.30}\; c_{\text{in-dist}}^{0.20}
```

Completeness = importance-weighted share of the model's top features observed, minus a penalty per conflict flag. Recency = 1 for sources under 60 days old, decaying linearly to 0 at 365. Stability = 1 − normalised standard deviation of propensity across 5 bootstrap models. In-distribution = rescaled IsolationForest score on training features. Validation: Brier score must fall from the bottom to the top confidence tercile; report correlation(confidence, propensity), which should be low. Weights are tuned on validation only.

### Contract-first API specs

All endpoints are thin wrappers; each returns the same Pydantic models the engines return. Fixtures with these exact shapes exist at H2.

**1. `GET /api/customers/{customer_id}/opportunities`** → one Evidence Pack per product (drives the Proof Card and drill-down).

```json
{
  "customer_id": "CUST-0001",
  "persona": "Priya — commuter, homeowner",
  "cutoff_date": "2026-06-30",
  "outcome_window_days": 90,
  "run_manifest": "sha256:…",
  "opportunities": [
    {
      "opportunity_id": "GP01",
      "opportunity_name": "EV Finance",
      "status": "RECOMMEND",
      "propensity": 0.82,
      "likelihood_band": "HIGH",
      "confidence": {"overall": 0.88, "completeness": 0.95, "recency": 0.92, "stability": 0.86, "in_distribution": 0.81},
      "eligibility": {"result": "ELIGIBLE", "rules_fired": [], "rules_version": "rules-1.0"},
      "reason_codes": [
        {"code": "HIGH_FUEL_SPEND", "phrase": "Fuel spend above your usual range", "metric": "avg_monthly_fuel_gbp", "value": 185, "display": "£185/month", "observed_at": "2026-06-30", "source": "inferred_transactions"},
        {"code": "HIGH_ANNUAL_MILEAGE", "phrase": "High annual mileage", "metric": "annual_mileage", "value": 11200, "display": "11,200 miles/year", "observed_at": "2026-05-14", "source": "customer_declared"}
      ],
      "why_now": {"trigger": "CAR_FINANCE_ENDING", "display": "Car finance ends in 74 days", "observed_at": "2026-06-30"},
      "impact": {
        "status": "ESTIMATED",
        "metric_family": "emissions",
        "unit": "kgCO2e/year",
        "low": 0, "central": 0, "high": 0,
        "display": "about X–Y kg CO2e a year (modelled estimate)",
        "formula": "miles × petrol factor − miles × kWh/mile × grid factor",
        "baseline": "current petrol car, same mileage",
        "horizon": "year 1",
        "factor_refs": ["DESNZ_<vintage>_petrol_car_avg", "DESNZ_<vintage>_grid_electricity"],
        "quality": "HIGH",
        "missing_inputs": []
      },
      "explanation": {"sentences": [{"text": "…", "fields": ["reason_codes.0"], "check": "PASS"}], "source": "llm|template", "claimcheck_status": "PASS"},
      "next_action": {"label": "Explore EV options", "secondary": "2-minute suitability check", "disclaimer": "Not a credit decision. Estimate, not a guarantee."}
    }
  ]
}
```

The impact numbers above are placeholders: real values come only from `carbon.estimate` with verified factors. Paperless packs carry `metric_family: "paper"` (sheets/year) plus a separate `digital_adoption` block, never CO2e.

**2. `POST /api/scenario`** → Scenario Lab recompute.

```json
// request
{"customer_id": "CUST-0001", "mutations": ["SET_VEHICLE_BEV"]}
// response
{
  "before": {"GP01": {"status": "RECOMMEND", "propensity": 0.82, "eligibility": "ELIGIBLE", "impact_status": "ESTIMATED"}},
  "after":  {"GP01": {"status": "RULED_OUT", "propensity": 0.31, "eligibility": "NOT_ELIGIBLE", "impact_status": "NOT_APPLICABLE"}},
  "diff": [{"product": "GP01", "field": "status", "from": "RECOMMEND", "to": "RULED_OUT", "cause": "Rule GP01-R1: existing BEV, no second vehicle"}],
  "invariance_ok": true,
  "elapsed_ms": 240
}
```

Mutation enum: `SET_VEHICLE_BEV`, `REMOVE_MILEAGE`, `REMOVE_ENERGY`, `ADD_CONFLICT_FUEL`, `MAKE_STALE`, `SET_RENTER`, `SELL_CAR`.

**3. `POST /api/claimcheck`** → the verifier (used by the explainer and by the red-team button).

```json
// request
{"customer_id": "CUST-0001", "opportunity_id": "GP01", "sentences": [{"text": "Switching will save you 4,000 kg a year and you're pre-approved.", "fields": []}]}
// response
{
  "verdict": "BLOCKED",
  "sentences": [{"text": "…", "status": "BLOCKED", "violations": [
    {"rule": "NUM", "span": "4,000 kg", "detail": "not in Evidence Pack allow-list"},
    {"rule": "BAN", "span": "will save"},
    {"rule": "BAN", "span": "pre-approved"}
  ]}],
  "fallback_text": "Your fuel spend has been above your usual range, so an EV may be worth exploring. Eligibility has not been confirmed.",
  "blocked_total": 17
}
```

**Supporting read-only endpoints** (same contracts file): `GET /api/portfolio/summary` (four separate metric tiles, funnel counts, quadrant points) and `GET /api/eval/summary` (metrics, scenario pass/fail, LLM eval table) for the Receipts page.

## 4. 14-Hour Phased Delivery Schedule (5-Dev Parallel Execution)

Five lanes, three phases, four hard checkpoints. Feature freeze is H12; after that only bug fixes and the demo path.

**Lanes:** **FE1** Customer Hub + Scenario Lab panel · **FE2** Cockpit + Receipts page · **BE** data generator, features, orchestrator, API, scenario runner · **AI** categoriser, models, confidence, reason codes, explainer, Claim-Check · **Demo/Polish** rules engine, carbon engine, factor table, eval set, scenario YAML, eval report, docs, slides.

**Working rules for agent-driven parallel work**

- Each lane works only in its own folders (Section 3). `contracts.py` changes = 2-line PR, announced in chat, merged within 10 minutes.
- Every lane's agent prompt starts with: the relevant Pydantic models, the fixture JSON, the folder it may touch, and "pure functions, no I/O outside `data/` and `out/`".
- Merge to `main` every 90 minutes; `main` must always run `make app` against fixtures.

### Phase 1 — Hours 0–4: Foundation & API contracts

| Lane | Tasks | Exit by H4 |
| --- | --- | --- |
| All (H0–0.5) | Lock the hour-0 decisions table; assign personas; agree status rules | Decisions in README |
| BE | Repo, Makefile, `contracts.py` (H2), 3 fixture packs + scenario + claimcheck responses (H2); generator v0 with all tables, latent profiles, 8 golden personas, labels from the 90-day window | `make data` works; fixtures committed |
| AI | Categoriser: merchant template library, rules + TF-IDF LR, held-out-merchant eval; prompt + output schema for explainer; verifier skeleton with `NUM` and `BAN` checks + 10 unit tests | Categoriser macro-F1 printed; verifier tests green |
| Demo/Polish | `factors.csv` with every row copied from the primary DESNZ/Defra workbook (sheet, row, vintage); `products.yaml` rules; carbon engine for all four products with ranges and INSUFFICIENT\_DATA; hand-calc unit tests | Carbon + rules tests green |
| FE1 | Customer Hub on fixtures: persona picker, four pathway tiles, Proof Card (headline, why-now, evidence chips, three badges, impact drawer, action), Why-not list | Card renders all 5 statuses from fixtures |
| FE2 | Cockpit on fixtures: four separate metric tiles, funnel, quadrant scatter, segment table, drill-down to a pack; Receipts page skeleton | Drill-down clicks through |

**Checkpoint H4:** fixtures render end to end; data generates; engines pass their own tests.

### Phase 2 — Hours 4–10: Feature assembly & showstopper spikes

| Lane | Tasks | Exit by H10 |
| --- | --- | --- |
| BE | `features.build` with as-of and conflict flags + leakage test (H6); orchestrator + packs for all customers (H7); FastAPI 4 endpoints (H8); `scenarios/mutations.py` + `/api/scenario` with diff (H9); `make all` + `run_manifest.json` (H10) | Real packs served; scenario endpoint < 1 s |
| AI | LightGBM ×4 + logistic + heuristic baselines, isotonic calibration, test predictions (H7); confidence components + tercile validation (H8); SHAP → reason codes with raw-value check (H8); live explainer with cache + full Claim-Check rule set + retry/template path + `claim_audit` (H10) | Every pack has calibrated propensity, confidence, codes, checked explanation |
| Demo/Polish | LLM eval set: 150 packs auto-perturbed + 20 adversarial sentences; naive-prompt baseline script (H8); 30+ scenario YAML cases + pytest runner (H9); `eval/report.py` generating the markdown report from artefacts (H10) | Report builds from one command |
| FE1 | Swap fixtures for live client (H7); Scenario Lab panel: toggles, before/after diff, cause line, invariance badge (H9); Confidence Ladder prompt on ABSTAIN; Mixed-signals state on REVIEW; red-team button (H10) | All 7 toggles work on Priya and Aisha |
| FE2 | Live portfolio data (H7); claims-blocked counter; Receipts page: baseline table, calibration curve, confidence-tercile chart, categoriser confusion matrix, LLM eval table, scenario pass/fail (H10) | Receipts page fully populated |

**Checkpoint H7:** one persona flows data → model → rules → carbon → LLM → card with real outputs. **Checkpoint H10:** both spikes work live; eval report builds.

### Phase 3 — Hours 10–14: Integration, edge-case hardening & mock fallbacks

| Lane | Tasks | Exit by H14 |
| --- | --- | --- |
| BE | Clean-clone run test; pre-compute packs and scenario results for all 8 personas into `out/cache/`; `DEMO_MODE=cached` path; latency benchmark | Fresh clone → `make all` → same metrics |
| AI | Run full LLM eval; fix top failure classes; pre-warm LLM cache for demo personas; record cost per 1,000 insights | Eval numbers final |
| Demo/Polish | Responsible AI note, architecture diagram, DATA.md, submission A–I check; slides (8); demo script rehearsal ×3 with stopwatch; backup video at H13 | Submission folder complete |
| FE1 | Edge-state polish: empty/loading/error states, "Not a credit decision", synthetic-data banner on every page, keyboard focus | Demo path has zero dead clicks |
| FE2 | Cockpit polish, governance strip (abstention rate, claims blocked, segment recommendation rates), export test predictions button | Judge can drill in 30 seconds |

**H12 freeze.** **H13** backup video recorded from `DEMO_MODE=cached`. **H13.5** final clean-clone run and submission upload. **H14** buffer.

**Cut order if behind** (cut from the top): metamorphic test → naive-baseline comparison → confidence in-distribution component → `SELL_CAR` and `SET_RENTER` toggles → FastAPI (UI imports engines directly). **Never cut:** customer-level split + leakage test, baselines, calibration, carbon unit tests, verifier + template fallback, status rules, data timestamps, four separate metrics, test predictions, Responsible AI note, `make all`.

## 5. The "Golden Path" 2-Minute Demo Script

The lean-forward moment lands at 0:35: a judge-visible toggle flips a recommendation to a refusal live. Run from `DEMO_MODE=cached` with the LLM cache pre-warmed; one driver, one narrator. All figures shown come from the engines on the day — rehearse with the real numbers, never these placeholders.

| Time | Screen | Driver input | What appears | Narrator line |
| --- | --- | --- | --- | --- |
| 0:00–0:10 | Customer Hub, persona picker | Select **Priya (CUST-0001)** | Four pathway tiles; EV Finance tile highlighted | "Carbon trackers tell you your footprint. GreenProof tells you your next step — and shows its receipts." |
| 0:10–0:35 | Priya's EV Proof Card | Click the card, then expand the impact drawer | Bills-first headline; Why-now tag "Car finance ends in N days"; evidence chips with values, dates and declared/inferred labels; three badges: Likelihood HIGH · Eligibility ELIGIBLE (rules-1.0) · Impact quality HIGH; range, formula, baseline, factor vintage; Claim-Check stamp "3 of 3 sentences verified" | "Three verdicts, three separate components. The LLM wrote none of these numbers." |
| 0:35–0:55 | Scenario Lab panel (same page) | Toggle **Set vehicle to BEV** | Status badge animates RECOMMEND → RULED\_OUT; diff row "Rule GP01-R1 fired: existing BEV, no second vehicle"; invariance badge green; elapsed time shown | "You're a judge testing ruled-out products. The rule wins over the model, every time — live." |
| 0:55–1:05 | Scenario Lab | Reset, toggle **Remove annual mileage** | Status → ABSTAIN; impact shows "Not enough information to estimate"; Confidence Ladder: "Add your annual mileage to unlock this estimate" | "Missing data gets an honest 'I don't know' and one question — never a made-up number." |
| 1:05–1:25 | Proof Card, red-team button | Click **Inject fake claim** (fixed string: "Switching will save you 4,000 kg a year and you're pre-approved.") | Sentence shown struck through with three highlighted spans (NUM, BAN, BAN); safe template appears; "claims blocked" counter increments | "This is how greenwashing happens. Every sentence is checked against the engine before a customer sees it." |
| 1:25–1:45 | Cockpit → Receipts | Click quadrant point → drill to Priya's evidence; open Receipts tab | Four separate tiles (CO2e, kWh, paper, digital); Receipts: lift vs both baselines, calibration curve, confidence-tercile chart, scenario suite "N/N passed", LLM eval numeric fidelity | "Every number reproduces from one command. Here's lift over baseline, calibration, and our own scenario tests passing." |
| 1:45–2:00 | Receipts page, stays on screen | — | Synthetic-data banner visible | "Predict with ML, decide with rules, calculate with the engine, explain with the LLM — and prove it." |

**Rehearsal rules:** stopwatch three times; if a section runs over, cut the 0:55 mileage beat first. Keep the synthetic-data banner in every frame. If asked a question mid-demo, answer after 2:00.

**Longer slot (5 minutes) add-ons, in order:** Marcus (REVIEW, mixed signals) → Tom (paperless only; paper sheets and digital adoption as separate metrics, no carbon claim) → Aisha ("You're all set": every product ruled out with reasons) → governance strip (abstention rate, recommendation rates by segment).

## 6. Fallback & Defensive Playbook

The most fragile component is the live LLM call inside the explainer and the red-team moment: network, rate limits or a model that phrases things differently on stage. The fix is structural — the verifier is deterministic and the trap uses a fixed string, so the climax of the demo never depends on the LLM at all.

### One switch: `DEMO_MODE`

| Mode | What it does | When |
| --- | --- | --- |
| `live` | Real LLM calls through the cache; FastAPI; engines run on request | Development, judges' Q&A if Wi-Fi is solid |
| `cached` (default on stage) | Explanations read from the SHA-256-keyed cache; packs and scenario results from `out/cache/`; engines still run for any input not cached | The demo |
| `fixtures` | UI reads `fixtures/*.json` only; no API, no models | Everything else has failed |

### Fragility ranking and exact fallbacks

| Rank | Failure | Fallback (already built, not improvised) |
| --- | --- | --- |
| 1 | LLM API slow, down or no key | Template explainer renders the same facts from the pack; card shows "standard summary" source tag; demo personas' outputs pre-warmed in cache at H11 |
| 2 | Red-team injection behaves differently | The injected sentence is a constant; `claimcheck.check` is a pure function with a unit test asserting the exact three violations; it never calls the LLM |
| 3 | Scenario recompute slow or errors | All 7 mutations × 8 personas precomputed into `out/cache/scenarios.json`; panel reads the cache first, recomputes only on a miss |
| 4 | FastAPI process dies | `app/client.py` imports `greenproof` engines in-process when the API health check fails |
| 5 | Model artefacts missing or retrain non-deterministic | Trained models, packs and `test_predictions.csv` committed under `out/` with hashes in `run_manifest.json`; the app loads them, it never trains at demo time |
| 6 | Factor value challenged by a judge | Impact drawer shows factor ID, vintage, sheet and row; DATA.md lists the retrieval date; the range, not a point, is the headline |
| 7 | Streamlit rerun lag on large data | Cockpit reads a pre-aggregated `portfolio.parquet`; `st.cache_data` on every loader; drill-down limited to top 50 customers |
| 8 | Laptop, projector or venue network | Backup video (H13) of the full 2-minute path; second laptop with the repo and `DEMO_MODE=fixtures` ready |

### Pre-stage checklist (run at H13.5 and again 10 minutes before presenting)

- [ ] `make all` from a clean clone reproduces the Receipts metrics
- [ ] `pytest` green: carbon hand calcs, rules, leakage, invariance, verifier, scenario suite
- [ ] LLM cache warmed for all 8 personas × 4 products
- [ ] `DEMO_MODE=cached` set; Wi-Fi off test passes
- [ ] Red-team button blocks with exactly NUM, BAN, BAN
- [ ] Synthetic-data banner visible on every page
- [ ] Backup video on two devices

## Appendix

### A. Golden personas (seeded into the generator)

| ID | Persona | Designed outcome |
| --- | --- | --- |
| CUST-0001 | Priya — commuter, homeowner, 8-year-old petrol car, car finance ending, complete data | GP01 RECOMMEND, high confidence; GP04 quick win |
| CUST-0002 | Marcus — vehicle record says BEV, fuel spend continues, stale EPC | GP01 REVIEW (mixed signals); GP02 ABSTAIN |
| CUST-0003 | Aisha — owns BEV, has solar, already paperless | GP01, GP03, GP04 RULED\_OUT with rules; "You're all set" |
| CUST-0004 | Tom — new customer, 6 weeks of history, paper statements | GP01–03 ABSTAIN; GP04 RECOMMEND with sheets + adoption only |
| CUST-0005 | Dave — 1960s semi, high winter gas, EPC D, homeowner | GP02 RECOMMEND |
| CUST-0006 | Sam — homeowner, high electricity, roof suitability unknown | GP03 ABSTAIN with Confidence Ladder (roof question) |
| CUST-0007 | Renter in a flat, high app use, paper statements | GP02, GP03 RULED\_OUT; GP04 RECOMMEND |
| CUST-0008 | Accessibility paper need flagged | GP04 RULED\_OUT (never nudge) |

### B. Submission checklist mapped to owners

- [ ] A. Working prototype — Streamlit app (FE1, FE2)
- [ ] B. Source code + README with `make all` (BE)
- [ ] C. Trained models + `score.py` (AI)
- [ ] D. Preprocessing pipeline: generator, categoriser, features (BE, AI)
- [ ] E. LLM implementation: prompts, model/API, Claim-Check, eval set + results (AI, Demo/Polish)
- [ ] F. Architecture diagram (Demo/Polish, from Section 3)
- [ ] G. Evaluation report on the validation set: baselines, calibration, confidence tiers, categoriser macro-F1, carbon tests, LLM eval, scenario suite, limitations (Demo/Polish)
- [ ] H. Responsible AI note: privacy, bias, explainability, hallucination, human oversight, data limitations (Demo/Polish)
- [ ] I. `test_predictions.csv` with propensity, confidence, reason codes, status (AI)

### C. Conflicts between the source docs, resolved

| Conflict | Sources disagree | Decision |
| --- | --- | --- |
| Factor vintage | DEFRA 2024 vs DESNZ 2026 vs "DEFRA\_2026" placeholder | One vintage, pinned, every row verified from the primary workbook; no headline numbers on slides until verified |
| Outcome window | 90 days vs 6 months | 90 days for all four products |
| Stack | Next.js/React/Postgres/Redis vs Streamlit/FastAPI/SQLite | Python + Streamlit + FastAPI + SQLite/Parquet: brief's preferred stack, fastest for agents |
| Confidence | Single score vs 3–4 decomposed components | Four components, geometric mean, validated by tercile |
| Eligibility states | 3 states vs 4 (with human review) | 3 eligibility states; conflicts handled by the REVIEW card status |
| Memory and Promise vs. Proof | Core vs stretch | Cut to slides; "Sell the car" in the Scenario Lab shows retirement without a memory store |
| Paperless carbon | Optional paper-material CO2e vs none | None in the prototype; sheets saved + digital adoption only |
| Label realism | Rule-based vs latent-variable labels | Latent-variable labels with hidden drivers; metrics described as an upper bound on synthetic data |

### D. Judge Q&A — the four hardest questions

**"Your labels are synthetic — aren't the metrics circular?"** Partly, and we say so. Labels come from documented latent drivers and noise the model never sees, so it cannot recover the generator. What we claim is narrower: the pipeline is leak-free (tested), beats two baselines by a measured lift, is calibrated, and its confidence tracks error. On real data the same code retrains unchanged.

**"Your verifier checks numbers — what about qualitative hallucinations?"** Three layers: every sentence must cite a pack field; implied-quantity words ("halve", "double", percentages) need a backing field; a banned lexicon covers approval and guarantee language. We report the residual miss rate on 150+ cases rather than claim zero. Two failures fall back to a template, so the worst case is a plainer sentence, never a false one.

**"Why trust an avoided-emissions number?"** We never present it as measured. Each figure is a labelled estimate with baseline, year-one horizon, pinned factor IDs and a low–high range, and is never netted against the bank's own emissions. Missing inputs return "insufficient information" instead of a default. Every formula has a hand-calculated unit test.

**"Is it fair?"** Age, income band and fine-grained postcode are not model features. The governance strip shows recommendation and abstention rates by income band, age band and region, and we report gaps rather than hide them. Likelihood is labelled "not a measure of worthiness or creditworthiness".
