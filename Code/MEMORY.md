# GreenDash — G3 Context Memory
<!-- AUTO-UPDATED by agent. Last update: 2026-10-11 (fifth run at `485ab95`; hard-coded Priya propensity found) -->

> **Project renamed:** `greenproof` → `greendash` (by teammates, commit `96ca5fb`)
> Repo: https://github.com/<org>/megathon26-chatgpt  
> Branch: `main` (backend state checked at `485ab95`) · Root: `megathon26-chatgpt/Code/`
> G3 owns: `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md`, `MEMORY.md`  
> **NEVER TOUCH:** `greendash/`, `api/`, `data/`, `config/`, `eval/`, `tests/`
> **Backend owner: G2-An** — as of 2026-10-11 G2-An has taken over all of G1-A's (G1-A) work. Send every backend/API ask to G2-An, not G1-A.

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
- Adopted G1-A's frozen `greendash/contracts.py` + 7 fixture files from `the G2-An feature-pipeline branch`
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
| **CP2 result, run 5 (local API at `485ab95`, fresh packs)** | 🔴 Unchanged: opportunities, claimcheck, portfolio, scenario all **500**; only `demo-token` + eval work. Same four causes as run 4 (`api/services.py:19` strict validation; `data/raw/energy.parquet`; `features/build.py:18`; `audit_attrs.parquet`) |
| `make data` / `make features` | 🔴 `make data` fails (`greendash.generator` has no `__main__`; `python -m greendash.generator.run` works). `make features` fails on missing `data/raw/energy.parquet`. **Warning: the generator overwrites 6 tracked files in `data/raw/` (`transactions.csv`, `vehicles.csv`, …)** — run `git checkout -- data/raw` afterwards or the manifest inputs drift |
| Building packs | ✅ `python -m greendash.packs` runs clean at `485ab95` (20,000 packs, 0 scoring errors, real propensities). See ML status for what they contain |
| Files deleted by rename commit `96ca5fb` | ✅ All 20 restored in `cb2173d` (real `claimcheck.py` 177 lines, `carbon/engine.py` 109 lines) |
| `api/deps.py` + `greendash/security/authz.py` | 🔴 **CRITICAL (flagged by G1-K, confirmed by test at `6285237`): no authorization.** `require_role()` never reads the request and returns the first permitted role; `require_subject()` is empty. Measured: `/api/eval/summary` returns 200 with no token, with a garbage token, and with a CUSTOMER token (evaluator-only route). Tokens are plain strings (`token_CUST-0001`), not signed JWTs. PR #3 doesn't touch this. Do not expose port 8000 |
| Portfolio/eval shapes | ⚠️ `aafd480` says `/api/portfolio/summary` + `/api/eval/summary` now match the UI fixtures (`metrics` / `baselines`) — **unverified**, needs a running API |
| `backend/` package | ℹ️ Older sub-package from `9d5f6d5` (`/health`, `/api/v1/transactions`). G1-A confirmed: **ignore it, the demo API is `api/`** |
| `api/routers/auth.py` | ✅ `POST /api/auth/demo-token` works (needs `ENV=demo`) |
| `api/routers/opportunities.py` | 🔴 500 (see CP2 result) |
| `/healthz` | ✅ Health check endpoint |
| `pyproject.toml` | ✅ `streamlit>=1.46` pinned on `main` |
| `fixtures/opps_*.json` × 5 | ✅ Contract-shaped, committed |
| `fixtures/claimcheck_response.json` | ✅ |
| `fixtures/scenario_response.json` | ✅ |

---

## 🧪 ML / LLM STATUS (G2-M, G2-M) — re-reviewed read-only at `03b5368`

G2-M says his deliverables are "locked in". What the repo shows:

| Item | State |
|---|---|
| 4 LightGBM models | 🔴 Models load and score, but **never recommend anyone**: highest real propensity in 20,000 packs is 0.417, threshold is 0.5 (`config/thresholds.yaml`); median 0.018. Result: 0 REVIEW and exactly **1 RECOMMEND — Priya GP01, which is hard-coded**: `greendash/models/score.py:32-33` sets `calib_pred = 0.95` when `customer_id == "CUST-0001"` and `pid == "GP01"` (G2-An, `40da7c3`; model's real value ≈ 0.1). Her card also has no reason codes, no explanation, confidence hard-coded 0.8 |
| `out/run_manifest.json` | 🔴 G2-M's "final": `sha256:7b510d60…3322bc`, 5,024 files, committed in `485ab95`. Problems: recorded `git_sha` `b3a4bb68…` **does not exist in the repo** (amended away); 5,000 of the files are `out/packs/*`, which are gitignored; regenerating packs on a clean install reproduced only 1,004 of 5,000 pack hashes; it bakes in the hard-coded Priya pack. The 24 non-pack files do match. **Not usable as proof yet** |
| Manifest reproducibility | ✅ Verified locally (non-parquet files re-hashed) |
| `docs/EVALUATION.md` | 🔴 **Not measured, and won't be.** Team confirmed real eval can't run: `data/splits/splits.json` is 0 bytes. **Agreed fallback: label slide 6 and the Receipts page "illustrative".** Numbers come from `fixtures/eval.json` (G3 placeholders) |
| Real metrics | ⚠️ `evaluate_models.py` computes ROC-AUC/Brier/ECE/lift but only prints them — nothing is saved |
| `fixtures/eval.json` | 🔴 G3 placeholder numbers (invented in `1d1fc0d`). `/api/eval/summary` now just returns this file (`aafd480`), so Receipts shows invented numbers in **every** mode until real ones replace it |
| LLM explainer on `main` | ⚠️ Security modules restored in `cb2173d`; not re-tested end to end (needs an LLM key) |
| Explainer output shape | ✅ Both paths contract-shaped; LLM path builds sentences from `explanation` + `metrics_summary`, canary dropped (read, not run — needs an LLM key) |
| Fallback template | ✅ Keyed on `opportunity_id` + status; bracket placeholders removed |
| Scores / reasons / confidence | ⚠️ Hard-coded `£100` reason removed (`reason_codes=[]`), so live cards show no evidence chips. Confidence still hard-coded 0.8. Bands hard-coded 0.7/0.4 |
| `greendash/contracts.py` | ⚠️ No longer frozen in practice: G2-M edited `ScenarioRequest.customer_id` to `\d{4,5}` in `6c41d76` |

**Rule for slides/README:** every eval number is illustrative — say so on slide 6 and on Receipts. Do not quote a manifest hash until G1-K's conditions are met (final snapshot, real git_sha, reproducible). **Do not present Priya's live RECOMMEND as a model prediction while the override is in `score.py`** — fixtures mode (openly synthetic) is the honest demo path.

---


## 🔴 REMAINING

### CP2 — verify live mode against a real API
Ran twice (see Backend State → CP2 result): client side works — token, role mapping, error cards. Blocked on backend: G2-An — `api/services.py` missing fields, two data files not in repo; G2-M — `data/models/hashes.json` mismatch (no RECOMMEND until fixed). **Demo fallback: `DEMO_MODE=fixtures` is unaffected and is the safe mode to present.** Test locally with `uvicorn api.main:app`; G2-An's `10.166.113.188:8000` was unreachable.
No frontend adapter planned: the API was adapted to the fixture shapes (`aafd480`); confirm on first live run.

### Known failing test (predates Step 3.5)
`test_all_five_statuses_covered` fails on `076bed7` too: `client.get_opportunities` de-dupes by
`opportunity_id`, and all five `opps_*.json` fixtures are GP01, so only the primary status survives.
Decide: one card per product (fix the test) or all five statuses (fix the de-dupe).

### Label eval numbers as illustrative (G3, agreed with team)
- `app/pages/3_Receipts.py`: add a visible "Illustrative figures — not measured results" note (icon + text)
- Slide 6: same label; do not present AUC/F1/scenario numbers as results

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
> Slides: 1-Problem, 2-Solution/tagline, 3-System architecture (use the diagram), 4-Customer journey (5 card states), 5-Business Cockpit, 6-Evaluation [TBD — replace after G2-M pushes EVALUATION.md], 7-Governance & Trust, 8-Team + ask.
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
├── opps_recommend.json          ✅ G1-A's (CustomerOpportunities shape)
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
| **G2-An** (now also covering G1-A's G1-A work) | **Remove or disclose the `CUST-0001` propensity override**; **critical: real token validation in `api/deps.py`**; `api/services.py:19` strict validation; `energy.parquet` naming; `make data` entry point |
| **G1-K** | Caddy CSP (`font-src 'self'`, `frame-ancestors 'none'`); proxy Streamlit only, not port 8000; keep branch `the G1-K claimcheck branch` until Claim-Check is restored on main |
| **G2-M** | Models never clear the 0.5 threshold (max 0.417); manifest: git_sha must be a real commit, packs not reproducible; coordinate final hash with G1-K |
