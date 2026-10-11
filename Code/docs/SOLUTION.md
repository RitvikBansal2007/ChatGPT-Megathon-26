# GreenDash: what we built, how it works, and how it maps to the brief

Problem Statement 1 (Lloyds): Green Customer Insights Platform. All data is synthetic; no real customer data is used anywhere.

## 1. The idea in one paragraph

GreenDash finds green-finance opportunities for a customer (EV Finance, Green Home Loan, Solar Finance, Paperless Banking), estimates the impact, and explains each one. Every recommendation is a **Proof Card**: three separate verdicts (likelihood, eligibility, impact), the evidence with dates, an impact range with its formula, and one explanation sentence that has been checked against the numbers before anyone sees it. If the system cannot justify a recommendation, it says so: it abstains, asks one question, or rules the product out and shows the rule.

**Core rule, enforced in code:** ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies.

## 2. How it works

```
synthetic data + smart-meter profile ─► features (one row per customer, cut-off 30 Jun 2026)
        │
        ├─► transaction categoriser (rules, then a text model)
        ├─► 4 propensity models (LightGBM, calibrated)  ─► likelihood + confidence + reason codes
        ├─► eligibility rules (config/products.yaml)     ─► eligible / needs verification / not eligible
        └─► carbon engine (config/factors.csv)           ─► low / central / high, formula, baseline
                         │
                orchestrator: assigns a status, never changes a verdict
                         │
                 Evidence Pack (JSON, frozen contract)
                         │
     minimise ─► input guard ─► LLM ─► output guard ─► Claim-Check ─► fixed wording if any check fails
                         │
        FastAPI (signed tokens, roles) ─► Streamlit: Customer Hub · Cockpit · Receipts
```

### Status rules (in this order)

| # | Condition | Status | What the customer sees |
|---|---|---|---|
| 1 | Eligibility rule says no | RULED_OUT | The rule in plain words. No action, no impact figure. |
| 2 | Records conflict (e.g. EV on file, fuel spend continues) | REVIEW | "Mixed signals", one confirming question. |
| 3 | Carbon engine lacks an input, or a critical field is missing | ABSTAIN | Which single field is missing. No number is invented. |
| 4 | Likelihood at or above the product's average take-up rate, and confidence at least 0.6 | RECOMMEND | Full Proof Card with an action. |
| 5 | Otherwise | SOFT_SURFACE | Shown for information, lower prominence. |

### Data

- 5,000 synthetic customers, seed 42, plus 8 hand-designed personas that are kept out of training.
- Tables follow the brief: customers, transactions, products, vehicles, energy usage, digital usage, green products, emission factors, labels.
- Take-up labels are drawn from hidden customer traits plus noise (not from a rule on visible fields), over a 90-day outcome window after the cut-off, so the models cannot simply recover the label rule.
- **Provided dataset:** the London smart-meter file (about 8 GB, half-hourly readings) is reduced by `ingest/lcl.py` to yearly consumption quantiles over 5,364 households and a 12-month seasonality shape. Each synthetic customer takes the yearly electricity of the real household at the same rank. Only aggregates are stored.
- Age, income band and postcode are never model inputs. They are used only for the fairness tables.

### Models

- One LightGBM classifier per product, 31 inputs, monotone constraints on the obvious signals, early stopping on the validation split.
- Isotonic calibration on validation, so a score reads as a probability.
- Split by customer: 3,494 train, 749 validation, 749 test. A leakage test guards the split.
- Confidence is separate from likelihood: completeness, recency, stability across trees, and how typical the customer is, combined into one number with its four parts shown.
- Reason codes are fixed identifiers (for example `HIGH_ANNUAL_MILEAGE`) with the value, date and whether it was declared or inferred.

### Carbon engine

Pure functions; every number comes from `config/factors.csv` (UK Government GHG conversion factors 2024) or `config/assumptions.yaml`.

| Product | Formula | Range comes from |
|---|---|---|
| EV Finance | miles × petrol or diesel factor − miles × kWh per mile × grid factor | ±15% on mileage |
| Green Home Loan | yearly gas kWh × reduction share × gas factor | 5% / 15% / 30% reduction |
| Solar Finance | 4 kWp × yearly yield × grid factor | ±10% on yield |
| Paperless Banking | paper statements × sheets per statement | reported in sheets, never as carbon |

CO₂e, energy, paper and digital adoption are reported separately and never summed.

### Claim-Check

A deterministic verifier, not a second model. Rules: `NUM` (every number must exist in the pack), `FIELD` (every cited field must exist), `BAN` (guaranteed, pre-approved, will save, you qualify, eco-friendly, carbon neutral), `METRIC` (paperless may not be described as carbon), `VERDICT` (nothing may be recommended when the status is ruled out or under review). A failed sentence is regenerated once, then replaced by fixed wording. Every result is written to an append-only, hash-chained audit table.

### Scenario Lab

Seven changes can be applied live to a persona: set vehicle to EV, remove mileage, remove energy data, add a conflicting fuel signal, make data stale, mark as renter, sell the car. The whole pipeline recomputes for that one customer and shows before, after, the rule that caused the change, and the time taken. A 35-case automated suite covers the four scenario types the brief names (missing data, conflicting signals, products that must not be recommended, insufficient information).

## 3. Measured results

Held-out test set, 749 customers the models never saw. Reproduce with `make pipeline`.

| Product | LightGBM AUC | Logistic regression AUC | Rule AUC | Lift at top 10% | Brier |
|---|---|---|---|---|---|
| EV Finance | 0.706 | 0.701 | 0.500 | 2.4× | 0.042 |
| Green Home Loan | 0.766 | 0.771 | 0.638 | 4.4× | 0.030 |
| Solar Finance | 0.673 | 0.705 | 0.790 | 2.5× | 0.016 |
| Paperless Banking | 0.895 | 0.882 | 0.874 | 3.4× | 0.047 |

- **Read honestly:** LightGBM is level with logistic regression (within a point on three products) and behind the simple rule on Solar. Take-up is rare (2–6%), so each test set has only a few dozen positives. The value of the system is the separation of verdicts, the rules and the checked explanations, not a large model advantage.
- **Categoriser:** macro-F1 1.00 against 0.61 for rules alone, 5-fold test on unseen merchants. Synthetic merchant names follow patterns, so real statements will be harder.
- **Scenario suite:** 35 of 35.
- **Explanations:** 80 real evidence packs were tested. 55 were written by the model and all 55 passed Claim-Check; the other 25 were refusals, which are explained by fixed rule wording by design. A second model acting as judge rated 78 of 80 (97.5%) faithful to the evidence. Canary leakage was 0%.
- **Adversarial sentences:** 15 of 20 hand-written unsafe sentences are blocked by the sentence rules alone.
- **Tests:** 549 automated tests pass.
- **Reproducibility:** two consecutive full runs give the same manifest hash (`out/run_manifest.json`).

## 4. Where it differs from a typical submission

| Typical approach | GreenDash |
|---|---|
| One blended "green score" | Three verdicts that never merge |
| The LLM writes freely | Every sentence is checked against the pack; failures fall back to fixed wording |
| Always recommends something | Five statuses, including abstain, review and ruled out, each with a reason |
| A single impact number | Low / central / high, with formula, baseline, factor source and a quality band |
| Paperless shown as carbon saved | Paper sheets and digital adoption only |
| Screenshots of edge cases | Scenario Lab: change one fact and watch the outcome change, backed by a 35-case suite |
| Headline accuracy only | A Receipts page with baselines, calibration, and the cases where our model does not win |
| "Trust us" on reproducibility | One command, fixed seed, manifest hash that repeats |

## 5. Functional requirements

| Requirement | What we did | Where |
|---|---|---|
| FR1 Customer 360 | One wide row per customer, with an as-of date per source and completeness flags | `greendash/features/` |
| FR2 Transaction categorisation | Ordered keyword rules, then a character n-gram text model; exactly one of 8 categories; boundary rules in config | `greendash/categoriser/`, `config/categories.yaml` |
| FR3 Opportunity detection | Likelihood, confidence and reason codes for every customer and product | `greendash/models/`, `data/test_predictions.csv` |
| FR4 Sustainability impact | Deterministic engine with documented factors, baseline and horizon | `greendash/carbon/`, `config/factors.csv` |
| FR5 Customer insight | LLM explanation from a minimised pack only, verified, with fallback | `greendash/llm/` |
| FR6 Business insights | Cockpit: four separate metrics, funnel, quadrant, segments, regions, drill-down | `app/pages/2_Cockpit.py`, `api/routers/portfolio.py` |
| FR7 Explainability | Evidence, confidence parts, reason codes, data date on every card; ruled-out products show the rule | `app/components/proof_card.py`, `config/products.yaml` |
| Customer view | Four pathways, Proof Card, clear action, "not a credit decision" | `app/pages/1_Customer_Hub.py` |
| Business dashboard | Customer → Opportunity → Evidence → Impact → Action | Cockpit "Customers" tab |
| Scenario-based evaluation | Scenario Lab and the 35-case suite | `greendash/scenarios/`, `eval/scenarios/` |
| Baseline and reproducibility | Two baselines per product; `make pipeline`; manifest | `greendash/models/baselines.py`, `greendash/manifest.py` |

### Submission items

| Item | Location |
|---|---|
| A. Working prototype | `make demo` |
| B. Source code and run instructions | repository, top-level `README.md` |
| C. Trained models and inference code | `data/models/`, `greendash/models/score.py` |
| D. Preprocessing pipeline | `greendash/generator/`, `ingest/`, `greendash/features/`, `greendash/categoriser/` |
| E. LLM implementation | `greendash/llm/` (prompts, gateway, guards, Claim-Check), `config/llm.yaml`, `eval/llm_eval/` |
| F. Architecture diagram | `docs/diagrams/` |
| G. Evaluation report | `docs/EVALUATION.md`, `out/eval_summary.json`, Receipts page |
| H. Responsible AI note | `docs/RESPONSIBLE_AI.md` |
| I. Test set predictions | `data/test_predictions.csv` |

## 6. Scoring criteria

| Criterion | Weight | Our evidence |
|---|---|---|
| Business relevance | 15% | Two audiences from one engine: a customer card with one clear action, and a ranked, explainable pipeline for relationship teams. "Why now" triggers such as car finance ending. |
| ML and recommendation quality | 20% | Customer-level split with a leakage test, two baselines, calibration, held-out metrics, and honest reporting where the baseline wins. Labels from hidden traits, not a visible rule. |
| Sustainability insight quality | 15% | Documented government factors, formula and baseline on every estimate, ranges not points, four metric families kept apart, abstention when an input is missing. |
| GenAI and LLM implementation | 15% | Minimised input, input and output guards, canary token, five-rule Claim-Check, fallback, audit trail, an evaluation set scored by rules and by a second model. |
| Technical architecture | 15% | Frozen contracts between components, one-command reproducible pipeline, signed-token API with roles, rate limits, cached explanations, sub-second scenario recompute. |
| Explainability and Responsible AI | 10% | Three separate verdicts, reason codes with dates and provenance, rule text for refusals, fairness tables by income and age band, human review path. |
| UX and dashboard | 5% | Brand design system, light and dark mode, role-based views, drill-down. |
| Innovation | 5% | Claim-Check, Scenario Lab, and a Receipts page that shows our own weaknesses. |

## 7. Security

- Signed HS256 tokens, 15-minute expiry, role checks on every route; a customer cannot read another customer; evaluators see the eight personas only.
- The API refuses to start outside development without a 32+ character secret. No secret is in the repository; `.env` is git-ignored.
- Request-rate limit, 64 KB body cap, security headers, and a log line for every refusal (no token or body is logged).
- All SQL is parameterised. Database rows are keyed by a keyed hash, never the customer ID. Feedback notes are encrypted with AES-256-GCM. The audit table is append-only and hash-chained.
- Models are stored in a safe format and hash-checked before loading. No pickle.
- All text shown in the UI is escaped; a test injects markup into every field and checks it is not rendered.
- Reverse-proxy configuration with a content security policy is in `infra/`.

## 8. Known limits

- Synthetic data: the metrics show the pipeline is sound, not real-world accuracy.
- The model does not clearly beat logistic regression; with 2–6% take-up and 5,000 customers this is expected.
- The confidence score is not yet validated: higher confidence does not yet mean lower error.
- Sign-in is a role picker with short-lived tokens. A bank would use its own single sign-on with multi-factor authentication.
- Storage is a local SQLite file. Production would use a managed database with encrypted connections and least-privilege accounts.
- Parts of the Cockpit (cohort quadrant, named segments, trend chart) use illustrative data.
- The optional customer-memory extension is not built. Feedback and opt-outs are stored but do not yet change later recommendations.

## 9. Running it for an evaluator

```bash
cd Code
source .venv/bin/activate
make pipeline     # about 3 minutes; ends by printing the manifest hash
make demo         # opens the app on http://127.0.0.1:8501
```

Suggested walk-through: Customer Hub as Evaluator with Priya (EV Finance card, "See the receipt") → Scenario Lab (set vehicle to EV; add conflicting fuel signal) → Claim-Check (inject the fake claim) → switch customer to Marcus, Tom and Aisha (review, abstain, ruled out) → Cockpit (four metrics, funnel, Governance tab) → Receipts (models, scenarios, explanations) → switch role to Customer and open Cockpit to show access is refused.
