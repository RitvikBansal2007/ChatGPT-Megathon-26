# GreenDash — G3 Context Memory
<!-- AUTO-UPDATED by agent. Last update: 2026-10-11 (state as of `a3fa7ad`; G2-M status + G2↔G3 integration review added) -->

> **Project renamed:** `greenproof` → `greendash` (by teammates, commit `96ca5fb`)
> Repo: https://github.com/<org>/megathon26-chatgpt  
> Branch: `main` (backend state checked at `cd3ba7d`) · Root: `megathon26-chatgpt/Code/`
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
| `greendash/contracts.py` | ✅ **Frozen** — `frozen=True` all models |
| `api/main.py` + `api/routers/` | 🔴 **Still cannot start from `main`** (checked at `cd3ba7d`): `greendash/llm/claimcheck.py` is missing, and `greendash/contracts.py` has no `CustomerPacks` (it is `CustomerOpportunities`) though `api/services.py` + `api/routers/opportunities.py` import it |
| Files deleted by rename commit `96ca5fb` | 🔴 Not restored — `1319866` added stubs for `llm/claimcheck.py` and `carbon/engine.py` instead (see ML / LLM status). Still missing: `llm/gateway.py`, `guard.py`, `minimise.py`, `providers.py`, `textnorm.py`, `carbon/formulas.py`, `units.py`, all of `generator/`. Real versions recoverable from `96ca5fb^` or `origin/the G1-K claimcheck branch` |
| First-request failures (from reading the code) | 🔴 `settings.ENV` / `settings.DEMO_MODE` don't exist in `config/settings.py` (only `demo_mode`); `issue_token()` takes 1 arg but `auth.py` passes 2; `scenario.py` reads `principal.role` but `require_role` returns a dict |
| `api/deps.py` + `greendash/security/authz.py` | ⚠️ Pushed (`d74e266`) but **stubs**: `require_role` ignores the token, `require_subject` is empty — no real auth. Don't expose port 8000 (`--host 0.0.0.0`) on a shared network |
| Portfolio/eval shapes | ⚠️ `aafd480` says `/api/portfolio/summary` + `/api/eval/summary` now match the UI fixtures (`metrics` / `baselines`) — **unverified**, needs a running API |
| `backend/` package | ℹ️ Older sub-package from `9d5f6d5` (`/health`, `/api/v1/transactions`). G1-A confirmed: **ignore it, the demo API is `api/`** |
| `api/routers/auth.py` | ⚠️ `POST /api/auth/demo-token` defined, will 500 (see above) |
| `api/routers/opportunities.py` | ⚠️ `GET /api/customers/{id}/opportunities` defined, import fails (see above) |
| `/healthz` | ✅ Health check endpoint |
| `pyproject.toml` | ✅ `streamlit>=1.46` pinned on `main` |
| `fixtures/opps_*.json` × 5 | ✅ Contract-shaped, committed |
| `fixtures/claimcheck_response.json` | ✅ |
| `fixtures/scenario_response.json` | ✅ |

---

## 🧪 ML / LLM STATUS (G2-M, G2-M) — reviewed read-only at `a3fa7ad`

G2-M says his deliverables are "locked in". What the repo shows:

| Item | State |
|---|---|
| 4 LightGBM models | ✅ `data/models/take_up_GP0{1-4}_lgb.skops` + `hashes.json` |
| `out/run_manifest.json` | ✅ Committed (`9bab839`). Hash `sha256:bbbea75f…0887`, computed on `6af7a2a`, 21 artefacts |
| Manifest reproducibility | 🔴 `out/models/*` now committed (`a3fa7ad`) and match, but `out/test_predictions.csv` is still missing and `config/settings.py` changed in `1319866`, so the hash **no longer matches `main`**. Hash covers `out/models/*.txt`; `score.py` loads `data/models/*.skops` — different files. `out/models/GP01_iso.json` is a 3-point placeholder calibrator |
| `docs/EVALUATION.md` | 🔴 **Do not use for slides — circular.** Since `a3fa7ad`, `eval/report.py` generates it by reading `fixtures/eval.json`, i.e. G3's own invented placeholders (AUC 0.847 etc., F1 0.891, 28/30 scenarios, LLM 97%). None of it is measured. "100 mocked packs" is hard-coded; real judged n = 2 |
| Real metrics | ⚠️ `evaluate_models.py` computes ROC-AUC/Brier/ECE/lift but only prints them — nothing is saved |
| `fixtures/eval.json` | 🔴 G3 placeholder numbers (invented in `1d1fc0d`). `/api/eval/summary` now just returns this file (`aafd480`), so Receipts shows invented numbers in **every** mode until real ones replace it |
| LLM explainer on `main` | 🔴 Never runs: `minimise.py` + `guard.py` still missing (deleted by `96ca5fb`) → fail-closed fallback rejects every call → always template |
| **Stubs added by `1319866` ("Fix API startup issues")** | 🔴 `greendash/llm/claimcheck.py` is now a 10-line stub that returns PASS for every sentence (G1-K's real one was 163 lines, still on `origin/the G1-K claimcheck branch`); `greendash/carbon/engine.py` `estimate()` always returns `NOT_APPLICABLE`; `greendash/models/score.py` `score()` returns constant `0.5`. **Red-team demo will show 0 violations and no impact numbers in live mode** |
| Explainer output shape | 🔴 Returns `{explanation: str|dict, source, claimcheck_status}`; contract + `claim_stamp.py` need `sentences[{text, fields, check}]`. Status `PII_BLOCK` is not in the contract |
| Fallback template | 🔴 Always uses the `REJECTED` template and reads `pack["recommendation"]` (field is `opportunity_id`) → every fallback says "EV Finance … is not recommended" |
| Scores / reasons / confidence | 🔴 Not contract-shaped: no `likelihood_band`, no `ConfidenceParts`, reason codes lack `phrase/display/observed_at/source`; IDs are `CUST-00001` (5 digits) vs UI/API `CUST-0001` |

**Rule for slides/README:** quote no metric from `EVALUATION.md` or `fixtures/eval.json` as real. The manifest hash may be quoted only with its commit (`6af7a2a`) and the caveat that the model files it covers are not in the repo.

---


## 🔴 REMAINING

### CP2 — verify live mode against a real API
Blocked on backend (owner: **G2-An**): restore the files deleted by `96ca5fb`, fix the `api/` errors in Backend State, then send a LAN IP / tunnel URL for `API_BASE_URL`.
Then: `uvicorn api.main:app --reload` and `DEMO_MODE=live streamlit run app/Home.py`.
No frontend adapter planned: the API was adapted to the fixture shapes (`aafd480`); confirm on first live run.

### Known failing test (predates Step 3.5)
`test_all_five_statuses_covered` fails on `076bed7` too: `client.get_opportunities` de-dupes by
`opportunity_id`, and all five `opps_*.json` fixtures are GP01, so only the primary status survives.
Decide: one card per product (fix the test) or all five statuses (fix the de-dupe).

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
| **G2-An** (now also covering G1-A's G1-A work) | Restore the 20 files deleted by `96ca5fb`; fix `CustomerPacks` import, settings `ENV`/`DEMO_MODE`, `issue_token` call, `principal.role`; real `api/deps.py`; then send LAN IP for CP2 |
| **G1-K** | Caddy CSP (`font-src 'self'`, `frame-ancestors 'none'`); proxy Streamlit only, not port 8000; keep branch `the G1-K claimcheck branch` until Claim-Check is restored on main |
| **G2-M** | Sent the integration flaw list (see "ML / LLM status"). Blocking for slide 6: real AUC/baseline/scenario/F1 numbers written to a file, and an honest LLM-eval sample size |
