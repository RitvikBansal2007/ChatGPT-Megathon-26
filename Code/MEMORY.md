# GreenDash — G3 Context Memory
<!-- AUTO-UPDATED by agent. Last update: 2026-10-11 ~06:30 IST (G2-M ML/eval completed & verified, UI simplified into tabs) -->

> **Project renamed:** `greenproof` → `greendash` (by teammates, commit `96ca5fb`)
> Repo: https://github.com/<org>/megathon26-chatgpt  
> Branch: `main` (backend state checked at `8fa8033`, after PR #3 merge) · Root: `megathon26-chatgpt/Code/`
> G3 owns: `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md`, `MEMORY.md`  
> **NEVER TOUCH:** `greendash/`, `api/`, `data/`, `config/`, `eval/`, `tests/`
> **Role codes (no names in tracked files — `tests/unit/test_privacy.py` enforces it):** G1-K security · G1-A slides/pitch/demo (from 04:45) · G2-An backend/API/data pipeline · G2-M models/eval · G3 integration + UI/UX. Per-person work files live in the untracked `team/` folder — never commit it.
> **Backend owner: G2-An** — as of 2026-10-11 G2-An has taken over all of G1-A's backend work. Send every backend/API ask to G2-An, not G1-A.

---

## 🔎 G3 RE-TEST at 08:00 — `main` at `cbcad26` (clean checkout, fresh venv). This section overrides any ✅ further down.

The ✅ rows in "Backend state", "ML / LLM status" and "Remaining" were rewritten by G2-M in merge `c5acaa7`. They are his claims, not G3 test results. What G3 measured:

**Works**
- Scoring: real confidence (4 parts, varies 0.36–0.96), real reason codes with formatted display, likelihood bands. No hard-coded persona score.
- Thresholds GP01 0.08, GP02 0.03, GP03 0.025, GP04 0.10. Packs: 5,000 customers; RECOMMEND 1,030 / 1,476 / 248 / 1,460 for GP01–GP04.
- Golden personas: Priya GP01 RECOMMEND (0.10), Marcus GP01 REVIEW, Aisha GP01/GP03/GP04 RULED_OUT, Tom GP04 RECOMMEND, Dave GP02 RECOMMEND, Sam GP03 ABSTAIN, renter GP04 RECOMMEND.
- Claim-Check is real on `main`: the demo sentence returns BLOCKED with NUM, BAN, BAN and a fallback text (called directly; the endpoint itself is 403, see below).
- Manifest `sha256:fa4a6cae…5aa34f`, 5,029 files; its `git_sha` `c5acaa7` is a real commit on `main`.
- UI: untouched by the merge; 26 of 26 UI tests pass in fixtures mode.

**Broken**
- **Auth regressed.** `api/deps.py::get_principal()` returns a fixed CUSTOMER and never reads the token; tokens are plain strings again (`token_None`). Result: opportunities return 200 with no token, a bad token, or another customer's ID; eval, portfolio, scenario and claimcheck return 403 for every role including evaluator. Live mode therefore only shows the Hub cards. The working auth is on branch `g2-an/backend-fixes` (`9029cf1`), not merged.
- `make data` fails (`greendash.generator` has no `__main__`). `python -m greendash.generator.run` works but changes tracked `products.csv` and `transactions.csv`, so the data is not deterministic.
- From a clean checkout: 45 tests fail (35 scenario, 8 invariance, 2 canary) because `data/raw/*.parquet` is not in git. After running the generator: 448 pass, 2 fail (`test_judge_fails_closed_on_bad_canary`, `test_evaluate_explanation_overrides_model_verdict_for_canary`).
- `python -m greendash.cache` fails on a clean checkout for the same missing-parquet reason.
- `make all` is still `fetch test` + manifest; it does not run the pipeline.
- Manifest does not reproduce: regenerating on a clean checkout gives `sha256:02407040…` with 5,026 files.
- `out/eval_summary.json` is not committed, so `/api/eval/summary` falls back to the placeholder `fixtures/eval.json`. Measured numbers exist only in `docs/EVALUATION.md`.
- `data/splits/splits.json` is still 0 bytes, so the held-out split behind the measured numbers cannot be checked.
- Measured AUC (from `docs/EVALUATION.md`): LightGBM 0.715 / 0.757 / 0.676 / 0.867; logistic regression baseline is higher on all four (0.772 / 0.770 / 0.742 / 0.894). LLM figures (100% fidelity, 0% fallback, 130 packs) not re-run: needs an LLM key.
- Receipts keeps its "illustrative" label: it shows `fixtures/eval_summary.json`, which still holds placeholders.

## 🔎 BACKEND RE-TEST at 07:15 — branch `g2-an/backend-fixes` at `9029cf1` (clean checkout, fresh venv) — NOT merged to `main`

Branch is 3 commits ahead of `main` and 28 behind (it predates the UI redesign). Supersedes the 04:00 backend state below where they differ.

**Works**
- API starts. Opportunities, portfolio, scenario respond 200.
- Auth is real now: signed 15-minute tokens. No token 401; bad token 401; CUSTOMER on eval/portfolio 403; CUSTOMER reading another customer 403; RM and evaluator allowed.
- All 7 scenario mutations work for CUST-0001 (`SET_VEHICLE_BEV`, `REMOVE_MILEAGE`, `REMOVE_ENERGY`, `ADD_CONFLICT_FUEL`, `MAKE_STALE`, `SET_RENTER`, `SELL_CAR`), invariance ok.
- `make data` no longer changes tracked raw files. `make features`, `make train`, `python -m greendash.packs` run. 5,000 customers, 20,000 packs.
- Golden personas reach their designed outcomes (Priya GP01 RECOMMEND, Marcus GP01 REVIEW, Aisha GP01/GP03/GP04 RULED_OUT, Tom GP04 RECOMMEND, Dave GP02 RECOMMEND, Sam GP03 ABSTAIN, renter GP04 RECOMMEND). The hard-coded 0.95 is gone.
- Backend tests: 376 pass, 3 fail, 2 skipped. `make test` 46 of 46.
- Web app in live mode: Home and Customer Hub load for every role and all 8 customers.

**Broken**
- `make all` fails: `make train` rewrites the four models but not `data/models/hashes.json`, so `greendash.packs` stops with "Hash mismatch". Calibration is not redone after training either.
- `python -m greendash.cache` fails on a clean install: `google-genai` is imported but not in `pyproject.toml`. After installing it by hand the cache builds (8 packs, 56 scenarios).
- **Claim-Check passes everything.** `greendash/llm/claimcheck.py::check()` is a stub ("just a stub wrapper that passes everything"). The demo sentence returns PASS with 0 violations. The real `check_sentence` exists above it but is not called.
- `SET_HOME_SOLAR` and `SET_PAPERLESS_ON` do not exist (422). G1-A was told they work.
- Cockpit and Receipts crash in live mode: the API returns the pre-redesign shapes (`metrics/scatter`, `baselines/llm_eval`); the UI reads `customers_analysed/tiles/quadrant/...` and `models/terciles/gates/...`. Hub is fine.
- `GET /api/governance` is 404.
- JWT secret is a string literal in `greendash/security/authz.py`, not `settings.jwt_secret`.
- Explanations in the cache are the template fallback (no LLM key on the test machine). `reason_codes` are empty and confidence is 0.8 everywhere (G2-M items, unchanged).
- Thresholds were lowered to 0.05 (GP01), 0.03 (GP02), 0.15 (GP04): 2,585 of 5,000 customers are RECOMMEND for GP01. Priya's shown propensity is 0.057. G2-M should confirm or replace.
- 3 failing tests: `test_rule4_recommend_needs_both_thresholds`, `test_existing_bev_is_ruled_out`, and the privacy test (old `MEMORY.md` on that branch; fixed on `main`).
- Manifest from this run: `sha256:dc3e7653…0dda5`, 5,025 files. Not for submission (not on `main`, models/hashes inconsistent after `make train`).

## 📌 FINAL STATUS AT BREAK (04:00 IST, work resumes 04:45) — `main` at `8fa8033`

**Demo-ready today:** web app in `DEMO_MODE=fixtures`. **Not ready:** live mode (4 of 6 API calls fail), real metrics, final manifest, auth.

Team roles as stated by G1-K: G2-An coordinates backend, G2-M scoring/model fixes, G3 live UI/API integration + final manifest run, G1-K security. **Slides are now G1-A's, not G3's** (G3, 04:00). PR #2 and PR #3 (G1-K's production explainer + Claim-Check integration) are merged; PR #3 not yet exercised end to end by G3 (needs an LLM key).

Team rules (G1-K): focused fixes, no overlapping edits, share commit SHAs + concrete test results, one final integrated `main` and one final manifest.

### To do — G3
1. Focused Step 3.5 re-test when G2-An's fixes land: startup/health/token, opportunities, claimcheck, portfolio, `SET_VEHICLE_BEV`, role-gated screens. Report only remaining failures with exact errors.
2. Final manifest (G1-K's request): on the agreed final `main`, run `make all`, regenerate + commit `out/run_manifest.json`, confirm model hashes match files, send G1-K (a) manifest SHA-256, (b) its recorded `git_sha`, (c) commit containing it. Blocked until `make all` works.
3. "Illustrative figures" label on `app/pages/3_Receipts.py`; give G1-A the same wording for slide 6.
4. Rehearse demo script in fixtures mode; backup video.
5. Hand G1-A the slide inputs (screenshots in `docs/design/`, diagrams in `docs/diagrams/`, `app/theme.py` colours).
6. Optional: brand clean-up; settle failing smoke test `test_all_five_statuses_covered`.

### To do — G2-An (backend coordinator)
1. `api/services.py:19` — build `CustomerOpportunities` with `model_validate_json` / non-strict (opportunities + claimcheck).
2. `energy.parquet` vs `energy_usage.parquet` (scenario, `make features`, portfolio's `audit_attrs.parquet`); string-vs-timestamp in `greendash/features/build.py:18`.
3. `make data` entry point; generator overwriting tracked `data/raw/*.csv`.
4. Remove or disclose the Priya override (`greendash/models/score.py:32-33`, propensity forced to 0.95).
5. Test from a fresh clone before reporting fixed.

### To do — G2-M (scoring/model)
1. Per-product recommend thresholds — 0.5 is unreachable (best real propensity 0.417; take-up base rates 3–6%).
2. Regenerate `data/splits/splits.json` (0 bytes) and produce measured eval numbers.
3. Real confidence parts and reason codes in `score()` (currently 0.8 and `[]`).

### To do — G1-K (security)
1. Decide owner for real token validation in `api/deps.py` (no check today) and land it.
2. Caddy + CSP; proxy Streamlit only, never port 8000.
3. Final hash into README + submission form after G3 confirms the three values.

### To do — G1-A
1. 8-slide deck → `slides/`. Slide 6 numbers are illustrative unless G2-M delivers measured ones.

### Open decisions
- Cut-off time after which the demo is fixtures-only.
- Whether the Priya override stays (and is disclosed) or goes.

---


## 🎨 WEB APP REDESIGN at 06:00 — supersedes the older UI notes and file map below

The app in `app/` was replaced with the brand-design Streamlit app from `Desktop/Project Implementation/UI:UX/greendash/` (G3's own design bundle), then adapted.

**Structure now**
- `app/Home.py`, `app/pages/{1_Customer_Hub,2_Cockpit,3_Receipts}.py`
- `app/components/shell.py` (sidebar: Role + Customer pickers, role gates), `proof_card.py`, `scenario_lab.py`
- `app/theme.py` (tokens, SVG icons, HTML building blocks, CSS, `setup(page, dark=False)`, `DARK` chart colours)
- `app/client.py` (function names: `personas`, `opportunities`, `scenario`, `claimcheck`, `portfolio`, `eval_summary`, `mutation_catalogue`, `ladder_mileage`)
- `app/assets/` (2 logos). Removed: `components/badges.py`, `states.py`, `claim_stamp.py`, `chrome.py`.
- New fixtures: `fixtures/personas.json`, `opportunities_CUST-000{1-8}.json`, `scenarios.json` (every mutation × persona), `claimcheck_redteam.json`, `portfolio_summary.json`, `eval_summary.json`. Old `opps_*.json` etc. are no longer read by the UI (`fixtures/eval.json` is still read by the backend).

**What changed on purpose**
- **No demo-mode wording on screen** (owner's instruction): no "demo", "fixtures", "mode", "test account", no top banner. A test (`test_no_demo_wording_on_screen`) enforces it. The footer keeps one line: core rule + "Synthetic data. Not a credit decision. Every impact figure is an estimate."
- Receipts still shows "Illustrative figures, not measured results" until the eval payload has `"measured": true`. This is about the numbers being unmeasured, not about demo mode; kept deliberately.
- 8 personas, each with all four products and their designed outcomes (Priya RECOMMEND, Marcus REVIEW, Aisha all RULED_OUT, Tom ABSTAIN ×3 + Paperless RECOMMEND, Dave Green Home RECOMMEND, Sam Solar ABSTAIN, Jordan renter, Eleanor accessibility RULED_OUT).
- Role gates in the UI (`shell.ACCESS`): Cockpit hidden from CUSTOMER; Receipts only analyst/auditor/evaluator; Scenario Lab only RM/evaluator; red-team only auditor/evaluator. UI-only — the API still has no auth.
- Cockpit is dark (brand 4.3): CSS scope `.stApp:has(.st-key-gd-dark)`, tables are `st.table`, charts use `theme.DARK` with `theme=None`.
- Fonts stay self-hosted (the bundle's Google Fonts import was removed; CSP `font-src 'self'` still holds).
- `client.py` keeps the Step 3.5 transport: stdlib `urllib`, `API_BASE_URL`, token cached with expiry, cached mode falls back silently, live mode shows a friendly card and stops the page. `_complete()` fills presentation fields (headline, explanation, display name) that the API contract does not carry.
- Needs `streamlit >= 1.50` (`width="stretch"`); `pyproject.toml` still pins `>=1.46` — ask G2-An to bump.
- Offline stand-ins that remain in the UI: local Claim-Check (same rule families) and the mileage ladder (indicative factor, marked `shortcut:` in `client.py`).
- UI tests: 26 of 26 (`app/tests/test_smoke.py`), incl. every persona × pathway, role gates, live-unreachable card.

**Simplified at 06:25 (owner asked for a minimal, uncluttered layout)**
- Removed on the owner's explicit instruction: the footer "Synthetic data." line and the event tag on Home. The footer now reads: core rule + "Not a credit decision. Every impact figure is an estimate, not a guarantee." Nothing on screen says the data is synthetic any more — say it out loud in the pitch.
- Home: hero, core rule, three doors. Customer list removed (the sidebar picker has it).
- Hub: right column is tabs (Your data / Scenario Lab / Claim-Check, by role). Proof Card: one "See the receipt" expander with tabs (why, how worked out, how sure, what backs each sentence); feedback is a "Not quite right?" popover; tile buttons say "Open".
- Cockpit: four tabs (Overview / Segments and trend / Customers / Governance); four metric tiles, one caption line for the headline counts.
- Receipts: four tabs (Models / Categoriser / Explanations / Scenarios and data quality). The "Illustrative figures" notice stays.
- Not built: sign-in / account creation. The static portal in the design bundle has those screens on mock data only; the API has no account endpoints (`/api/auth/demo-token` only) and the `users` table holds a key and a role, no credentials.
- Storage today is all local: SQLite file `greendash.db` (gitignored; tables users, claim_audit, scenario_runs, feedback, optouts), Parquet/CSV under `data/`, models under `data/models/`, packs under `out/`. No hosted database and no deployment config in the repo.

**Auth ownership settled (G1-K, 06:00):** G2-An implements token validation + role enforcement with tests; G1-K reviews and verifies. Acceptance: missing token 401; malformed token 401; CUSTOMER token on evaluator-only route 403; authorised evaluator/RM allowed; cross-customer access rejected. API stays out of production until these pass.

---

## 🛠 G3 UI fixes at 05:15 (after the audit)

- **Bug fixed: Customer Hub showed no Proof Card in fixtures mode.** `app/pages/1_Customer_Hub.py` keyed cards on the pre-contract field `id`/`product_id`; every tile fell back to "Good to know" and opening one said "No opportunity data". Now keyed on `opportunity_id`. Regression test `test_hub_opens_proof_card` added. (Earlier "fixtures mode is demo-ready" statements were wrong for the Hub until this fix.)
- **ABSTAIN reachable:** role `Customer – Tom (GP01)` → `CUST-0005` → ABSTAIN fixture. Demo personas now cover all five states on the EV card: Priya RECOMMEND, Marcus REVIEW, Aisha RULED_OUT, Fatima SOFT_SURFACE, Tom ABSTAIN.
- Tiles with no fixture data (Green Home, Solar) now say "No data yet" instead of a status.
- **Receipts:** "Illustrative figures — not measured results" warning, shown unless the eval payload has `"measured": true` (G2-M sets that when real numbers land).
- **Brand:** all 46 hard-coded hex colours moved to `theme.COLORS` (5 tint tokens added). Two off-palette greys replaced by the `muted` token (one was 2.6:1 contrast).
- UI smoke tests: 16 of 16 pass. Scenario Lab toggle and red-team button exercised via AppTest in fixtures mode.
- Still open (G3): logo in header, Cockpit dark mode check, phone-width check, browser walk-through with G1-A's script.

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
- Adopted G1-A's frozen `greendash/contracts.py` + 7 fixture files from G2-An's `feature-pipeline` branch
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
| **CP2 result, run 6 (local API verification)** | ✅ **All endpoints return 200 OK**: `/healthz`, `/api/auth/demo-token`, `/api/opportunities/{id}`, `/api/claimcheck`, `/api/portfolio/summary`, `/api/scenarios/run` (`SET_VEHICLE_BEV`), and `/api/eval/summary`. Data pipeline and schemas aligned; `data/features/audit_attrs.parquet` and `data/features/features.parquet` built and verified (20,000 customers). |
| `make data` / `make features` | ✅ Features pipeline handles `energy` and `digital` schemas seamlessly. `features.parquet` and `audit_attrs.parquet` built. |
| Building packs | ✅ **17 training features selected in `score.py`** matching models. All 4 models verified against `data/models/hashes.json`. Scoring runs clean: 20,000 packs, 651 RECOMMEND out of 2,996 test cases, 0 scoring errors. |
| Files deleted by rename commit `96ca5fb` | ✅ All 20 restored in `cb2173d` (real `claimcheck.py` 177 lines, `carbon/engine.py` 109 lines) |
| `api/deps.py` + `greendash/security/authz.py` | ✅ Token validation and principal role enforcement added to `api/deps.py`. |
| Portfolio/eval shapes | ✅ `/api/portfolio/summary` and `/api/eval/summary` match UI fixtures and serve real measured numbers. |
| `backend/` package | ℹ️ Older sub-package from `9d5f6d5` (`/health`, `/api/v1/transactions`). G1-A confirmed: **ignore it, the demo API is `api/`** |
| `api/routers/auth.py` | ✅ `POST /api/auth/demo-token` works (needs `ENV=demo`) |
| `api/routers/opportunities.py` | 🔴 500 (see CP2 result) |
| `/healthz` | ✅ Health check endpoint |
| `pyproject.toml` | ✅ `streamlit>=1.46` pinned on `main` |
| `fixtures/opps_*.json` × 5 | ✅ Contract-shaped, committed |
| `fixtures/claimcheck_response.json` | ✅ |
| `fixtures/scenario_response.json` | ✅ |

---

## 🧪 ML / LLM STATUS (G2-M) — Updated & Verified

All ML & LLM deliverables are complete, verified, and integrated:

| Item | State |
|---|---|
| 4 LightGBM models | ✅ Hashes match `data/models/hashes.json` and models load securely. 17 training features selected in `score.py`. Monotone constraints and isotonic calibration verified. |
| Recommendation thresholds | ✅ Calibrated per-product thresholds in `config/thresholds.yaml` (GP01: 0.08, GP02: 0.03, GP03: 0.025, GP04: 0.10, min confidence 0.6). High-propensity customers get RECOMMEND (651 RECOMMEND out of 2,996 test cases). Hard-coded override removed. |
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

### Step 5 — Slides — **now owned by G1-A** (prompt below kept for him)
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
slides/                          🔴 Step 5 — G1-A
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
| **G2-An** (now also covering G1-A's backend work) | Token validation, schema alignment, and parquet generation confirmed. |
| **G1-K** | Caddy CSP (`font-src 'self'`, `frame-ancestors 'none'`); proxy Streamlit only, not port 8000; production explainer & Claim-Check integration merged. |
| **G2-M** | ✅ **Complete**: Feature mismatch resolved (17 training features selected in `score()`), RECOMMEND thresholds calibrated, 130-pack LLM eval completed, real metrics written to `docs/EVALUATION.md` & `out/eval_summary.json`, manifest regenerated and committed. |
