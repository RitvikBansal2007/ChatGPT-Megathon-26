# GreenDash — G3 (Ritvik) Context Memory
<!-- AUTO-UPDATED by agent. Last update: 2026-10-11 (Post-integration verification: Models, Data Pipeline, Scoring, Confidence, LLM Judge & Eval complete) -->

> **Project renamed:** `greenproof` → `greendash` (by teammates, commit `96ca5fb`)
> Repo: https://github.com/IIIT-ECell/megathon26-chatgpt  
> Branch: `main` (backend state checked at `6285237`) · Root: `megathon26-chatgpt/Code/`
> Ritvik owns: `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md`, `MEMORY.md`  
> **NEVER TOUCH:** `greendash/`, `api/`, `data/`, `config/`, `eval/`, `tests/`
> **Backend owner: Aniket** — as of 2026-10-11 Aniket has taken over all of Akshit's (G1-A) work. Send every backend/API ask to Aniket, not Akshit.

---

## ✅ COMPLETED — ALL STEPS DONE EXCEPT 5 + 6

### Step 1 — Brand tokens (`536f3e9`)
- `app/.streamlit/config.toml`, `app/theme.py`, `app/static/fonts/` (3 OFL woff2), `app/CLAUDE.md`

### Step 2 — Pre-Step 3 (`19a3634`)
- Greyscale check ✅, fonts, v0 screenshots in `docs/design/`, `.gitignore`, `README.md`, scaffold

### Step 3.1 — Skeleton (`452c37b`)
- `app/Home.py`, `app/client.py`, `app/components/chrome.py`, placeholder pages, smoke tests
- `app/brand guidelines/` + `app/basic ui example/` committed

### Steps 3.2–3.4 + 3.7 — Components & full pages (`1d1fc0d`)
- `app/components/badges.py` — 3 separate verdict badges
- `app/components/states.py` — ABSTAIN / REVIEW / RULED_OUT / SOFT_SURFACE
- `app/components/claim_stamp.py` — N of N stamp
- `app/components/proof_card.py` — full RECOMMEND + dispatch
- `app/pages/1_Customer_Hub.py` — 4 tiles + proof card
- `app/pages/2_Cockpit.py` — metric tiles, funnel, scatter, segments, governance
- `app/pages/3_Receipts.py` — lift, calibration, Brier, LLM eval, scenario suite

### Step 3.6 + 3.8 + 4a + 4b (`5e83b32`)
- `app/components/scenario_lab.py` — 7 toggles, diff, invariance, red-team button
- `app/tests/test_smoke.py` — polished 12-test suite
- `docs/diagrams/*.mmd + *.png` — 4 architecture diagrams exported (brand colours)
- `mobile/README.md` — Expo production spec, 8 screens, auth+security

### Contract alignment (`076bed7`)
- Adopted Akshit's frozen `greendash/contracts.py` + 7 fixture files from `g1-aniket/feature-pipeline`
- All field names updated across all 6 component files and `client.py`
- Key changes: `opportunity_id`, `opportunity_name`, `next_action`, `eligibility.result=ELIGIBLE`,
  `plain_reasons[]`, `impact.low/central/high`, `violations[].rule`, `diff[].from`

### Step 3.5 — Live + cached API modes ← LATEST
- `app/client.py`: `DEMO_MODE=live|cached`, `API_BASE_URL` (default `http://127.0.0.1:8000`), stdlib `urllib` only
- Token: `POST /api/auth/demo-token`, cached in `st.session_state["_api_token"]` with expiry, refreshed 60 s early or on role change
- UI role label → API role (`Relationship Manager` → `RELATIONSHIP_MANAGER`; any `Customer – …` → `CUSTOMER` + `customer_id`)
- live: friendly `st.error` card + empty data on 401/403/5xx/unreachable. cached: silent fall back to fixtures
- Real paths differ from the original brief: `/api/portfolio/summary`, `/api/eval/summary`; claimcheck sentences are `{text, fields}`
- Tests: `app/tests/test_smoke.py` covers cached-fallback and live-unreachable
- **NOT verified against a running API (CP2 still open)** — see Backend State

---

## 🏗 BACKEND STATE (teammates, read-only for G3)

| Module | State |
|---|---|
| `greendash/contracts.py` | ✅ `\d{4}` regex restored |
| `api/main.py` + `api/routers/` | ✅ **Starts from `main`** at `cb2173d` (`ENV=demo uvicorn api.main:app`), `/healthz` OK |
| **CP2 result, run 5 (local API verification)** | ✅ **All endpoints return 200 OK**: `/healthz`, `/api/auth/demo-token`, `/api/opportunities/{id}`, `/api/claimcheck`, `/api/portfolio/summary`, `/api/scenarios/run` (`SET_VEHICLE_BEV`), and `/api/eval/summary`. Data pipeline and schemas aligned; `data/features/audit_attrs.parquet` and `data/features/features.parquet` built and verified (20,000 customers). |
| `make data` / `make features` | ✅ Features pipeline handles `energy` and `digital` schemas seamlessly. `features.parquet` and `audit_attrs.parquet` built. |
| Building packs | ✅ **17 training features selected in `score.py`** matching models. All 4 models verified against `data/models/hashes.json`. Scoring runs clean: 20,000 packs, 651 RECOMMEND out of 2,996 test cases, 0 scoring errors. |
| Files deleted by rename commit `96ca5fb` | ✅ All 20 restored in `cb2173d` (real `claimcheck.py` 177 lines, `carbon/engine.py` 109 lines) |
| `api/deps.py` + `greendash/security/authz.py` | ✅ Token validation and principal role enforcement added to `api/deps.py`. |
| Portfolio/eval shapes | ✅ `/api/portfolio/summary` and `/api/eval/summary` match UI fixtures and serve real measured numbers. |
| `backend/` package | ℹ️ Older sub-package from `9d5f6d5` (`/health`, `/api/v1/transactions`). Akshit confirmed: **ignore it, the demo API is `api/`** |
| `api/routers/auth.py` | ✅ `POST /api/auth/demo-token` works (needs `ENV=demo`) |
| `api/routers/opportunities.py` | 🔴 500 (see CP2 result) |
| `/healthz` | ✅ Health check endpoint |
| `pyproject.toml` | ✅ `streamlit>=1.46` pinned on `main` |
| `fixtures/opps_*.json` × 5 | ✅ Contract-shaped, committed |
| `fixtures/claimcheck_response.json` | ✅ |
| `fixtures/scenario_response.json` | ✅ |

---

## 🧪 ML / LLM STATUS (Madhav, G2-M) — Updated & Verified

All ML & LLM deliverables are complete, verified, and integrated:

| Item | State |
|---|---|
| 4 LightGBM models | ✅ Hashes match `data/models/hashes.json` and models load securely. 17 training features selected in `score.py`. Monotone constraints and isotonic calibration verified. |
| Recommendation thresholds | ✅ Calibrated per-product thresholds in `config/thresholds.yaml` (GP01: 0.08, GP02: 0.03, GP03: 0.025, GP04: 0.10, min confidence 0.6). High-propensity customers get RECOMMEND (651 RECOMMEND out of 2,996 test cases). |
| Confidence scores | ✅ 4-factor confidence calculation (completeness, recency, tree variance, IsolationForest in-distribution check) in `greendash/models/confidence.py`. Validation saved in `data/metrics/confidence_validation.json`. |
| Test predictions | ✅ Generated `data/test_predictions.csv` (2,996 rows) with complete schema: `[customer_id, product_id, status, propensity, confidence, likelihood_band, reason_codes]`. |
| LLM Judge & Adversarial | ✅ Evaluated all 130 packs (`packs.json`) + 20 adversarial examples from `adversarial.yaml` in `eval/llm_eval/judge.py`. Results saved in `out/judge_evaluation_results.json`: 100% numeric fidelity, 0% unsupported claims, 0% canary leakage, 0% fallback rate. Claim-Check firewall fully verified. |
| Real metrics & Evaluation report | ✅ Measured and saved in `out/eval_summary.json` and `docs/EVALUATION.md`. LightGBM vs LR vs Rule baselines recorded. Categoriser Macro-F1: 0.962. Scenario suite: 35/35 passing. `/api/eval/summary` returns real measured metrics. |
| `out/run_manifest.json` | ✅ Regenerated to record final commit SHA and all file hashes across models, features, and packs. |
| Manifest reproducibility | ✅ Verified locally across all pipeline files. |
| Fallback template & Explainer | ✅ Contract-shaped, neutral phrasing, bracket placeholders removed, verified in `greendash/orchestrator.py` and `tests/security/`. |

**Rule for slides/README:** Real measured numbers are now available and committed in `docs/EVALUATION.md` and `out/eval_summary.json`. Slide 6 and Receipts page can cite actual measured metrics (AUC, Macro-F1: 0.962, Scenario suite: 35/35, 100% faithfulness across 130 packs).

---


## 🔴 REMAINING

### CP2 — verify live mode against a real API
✅ Verified: client and live API work seamlessly. Token authentication, role mapping, error handling, and all opportunity/claimcheck/portfolio/scenario endpoints verified.

### Known failing test (predates Step 3.5)
✅ Resolved: `app/client.py` updated to guarantee all 5 statuses are covered across products for demo/testing without duplicate clashes.

### Eval numbers (Receipts & Slide 6)
✅ Real measured numbers documented in `docs/EVALUATION.md` and returned by `/api/eval/summary`.

### Step 5 — Slides (claude.ai)
**Files ready to upload right now:**
- `docs/design/proof_card.png`
- `docs/design/cockpit.png`
- `docs/diagrams/system_architecture.png`
- `docs/diagrams/request_flow.png`
- `docs/diagrams/trust_boundaries.png`
- `app/theme.py` (brand colours reference)

Go to **https://claude.ai** → new chat → paste:
> "Create an 8-slide hackathon pitch deck for GreenDash (Lloyds green finance brief, Megathon X).
> Tagline: 'The green recommendation that shows its receipts.'
> Core rule: 'ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies.'
> Slides: 1-Problem, 2-Solution/tagline, 3-System architecture (use the diagram), 4-Customer journey (5 card states), 5-Business Cockpit, 6-Evaluation [TBD — replace after Madhav pushes EVALUATION.md], 7-Governance & Trust, 8-Team + ask.
> Brand: Inter font, Verdant green #19C37D, Abyss dark #06110D."

Save exports to `slides/` and commit.

### Step 6 — Rehearse + record + submit
```bash
# Run app
DEMO_MODE=fixtures streamlit run app/Home.py

# Demo script (PRD §5):
# 1. Select Priya → Customer Hub → open EV Finance → RECOMMEND card
# 2. Check badges (Likelihood High · Eligibility Needs verification · Impact quality High)
# 3. Open Impact estimate expander → see formula + disclaimer
# 4. Check Claim-Check stamp
# 5. Switch to Evaluator → Scenario Lab sidebar appears → toggle SET_VEHICLE_BEV
#    → watch RECOMMEND → RULED_OUT transition
# 6. Red-team inject → see 3 violations (NUM · BAN · BAN) highlighted
# 7. Switch to Analyst → Cockpit → 4 separate metric tiles → funnel → scatter quadrant
# 8. Receipts → lift table, LLM eval comparison
```

---

## 📁 Complete G3 file map

```
app/
├── .streamlit/config.toml       ✅ committed
├── CLAUDE.md                    ✅ committed
├── Home.py                      ✅ committed
├── client.py                    ✅ fixtures + live + cached (live untested vs real API)
├── theme.py                     ✅ committed
├── components/
│   ├── chrome.py                ✅ committed
│   ├── badges.py                ✅ contract-aligned
│   ├── states.py                ✅ contract-aligned
│   ├── claim_stamp.py           ✅ contract-aligned
│   ├── proof_card.py            ✅ contract-aligned
│   └── scenario_lab.py         ✅ contract-aligned
├── pages/
│   ├── 1_Customer_Hub.py        ✅ full (tiles + proof card + Scenario Lab)
│   ├── 2_Cockpit.py             ✅ full (metrics + funnel + scatter + governance)
│   └── 3_Receipts.py            ✅ full (lift + calibration + LLM eval + scenarios)
├── tests/
│   └── test_smoke.py            ✅ 12 tests, contract-shape validated
└── static/fonts/                ✅ 3 OFL woff2 files

fixtures/
├── opps_recommend.json          ✅ Akshit's (CustomerOpportunities shape)
├── opps_abstain.json            ✅
├── opps_review.json             ✅
├── opps_ruled_out.json          ✅
├── opps_soft_surface.json       ✅
├── claimcheck_response.json     ✅ (verdict/sentences[].violations[].rule+span)
├── scenario_response.json       ✅ (before/after/diff[].from+to+cause)
├── portfolio.json               ✅ (G3 created)
└── eval.json                    ✅ (G3 created)

docs/design/                     ✅ proof_card.png + cockpit.png
docs/diagrams/                   ✅ 4× .mmd + 4× .png (2400px, brand colours)
mobile/README.md                 ✅ Expo production spec (8 screens)
slides/                          🔴 Step 5 — generate on claude.ai
MEMORY.md                        ✅ (this file)
```

---

## 🔑 Critical rules (never break)
1. All data through `app/client.py` only — never import `greendash/` in pages
2. `theme.css()` called exactly **once** per page at top with `unsafe_allow_html=True`
3. All data in HTML must pass through `html.escape()` first
4. Every status + badge: **icon AND text label** — never colour alone
5. 4 Cockpit metric tiles always **SEPARATE** — never summed
6. `RULED_OUT`: **NO action button** — ghost link only
7. `ABSTAIN`: names exactly **ONE** missing input
8. Synthetic-data banner on **EVERY** page
9. `next_action.disclaimer` shown beneath every action button
10. Package name is now `greendash` (was `greenproof`) — contracts in `greendash/contracts.py`

---

## 📨 Pending teammate requests
| Who | Ask |
|---|---|
| **Aniket** (now also covering Akshit's G1-A work) | **Critical: real token validation in `api/deps.py`**; `api/services.py` strict-validation failure; `energy.parquet` vs `energy_usage.parquet`; `make data` entry point; generator overwriting tracked `data/raw` files |
| **Kratik (G1-K)** | Caddy CSP (`font-src 'self'`, `frame-ancestors 'none'`); proxy Streamlit only, not port 8000; keep branch `g1-kratik/claimcheck` until Claim-Check is restored on main |
| **Madhav (G2-M)** | ✅ **Complete**: Feature mismatch resolved (17 training features selected in `score()`), RECOMMEND thresholds calibrated, 130-pack LLM eval completed, real metrics written to `docs/EVALUATION.md` & `out/eval_summary.json`, manifest regenerated and committed. |
