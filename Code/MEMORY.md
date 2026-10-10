# GreenDash — G3 (Ritvik) Context Memory
<!-- AUTO-UPDATED by Antigravity agent. Last update: 2026-10-11T02:38 IST -->

> **Project renamed:** `greenproof` → `greendash` (by teammates, commit `96ca5fb`)
> Repo: https://github.com/IIIT-ECell/megathon26-chatgpt  
> Branch: `main` (HEAD: `076bed7`) · Root: `megathon26-chatgpt/Code/`  
> Ritvik owns: `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md`, `MEMORY.md`  
> **NEVER TOUCH:** `greendash/`, `api/`, `data/`, `config/`, `eval/`, `tests/`

---

## ✅ COMPLETED — ALL STEPS DONE EXCEPT 3.5 + 5

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

### Contract alignment (`076bed7`) ← LATEST
- Adopted Akshit's frozen `greendash/contracts.py` + 7 fixture files from `g1-aniket/feature-pipeline`
- All field names updated across all 6 component files and `client.py`
- Key changes: `opportunity_id`, `opportunity_name`, `next_action`, `eligibility.result=ELIGIBLE`,
  `plain_reasons[]`, `impact.low/central/high`, `violations[].rule`, `diff[].from`

---

## 🏗 BACKEND STATE (teammates, read-only for G3)

| Module | State |
|---|---|
| `greendash/contracts.py` | ✅ **Frozen** — `frozen=True` all models |
| `api/main.py` + `api/routers/` | ✅ **Built** — FastAPI with all routers (opportunities, auth, claimcheck, scenario, portfolio, eval, governance, feedback) |
| `api/routers/auth.py` | ✅ `POST /api/auth/demo-token` available |
| `api/routers/opportunities.py` | ✅ `GET /api/customers/{id}/opportunities` |
| `/healthz` | ✅ Health check endpoint |
| `pyproject.toml` | ⚠️ `streamlit>=1.46` **NOT yet pinned** (missing from deps list) |
| `fixtures/opps_*.json` × 5 | ✅ Contract-shaped, committed |
| `fixtures/claimcheck_response.json` | ✅ |
| `fixtures/scenario_response.json` | ✅ |

---

## 🔴 REMAINING

### Step 3.5 — Live API (`app/client.py` live + cached modes)
**Ready to start — `api/` is fully built!**

When you say "do Step 3.5", I will add to `app/client.py`:
```python
# live mode:
#   POST /api/auth/demo-token  → Bearer token (role from session_state)
#   Refresh at 15 min
#   GET /api/customers/{id}/opportunities  (Bearer header)
#   POST /api/scenarios/{id}
#   POST /api/claimcheck
#   GET /api/portfolio
#   GET /api/eval
#   Friendly error card on 401/403/5xx — never stack trace
#
# cached mode:
#   GET /healthz → if fails, fall back to fixtures/
```

**To test (CP2):** `uvicorn api.main:app --reload` then `DEMO_MODE=live streamlit run app/Home.py`

**Note:** Need to add `streamlit>=1.46` to `pyproject.toml` — tell Akshit or I can add it (it's his file so needs his OK).

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
├── client.py                    ✅ fixtures ✅ | live/cached 🔴 Step 3.5
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
| **Akshit (G1-A)** | Add `streamlit>=1.46` to `pyproject.toml` dependencies |
| **Madhav (G2-M)** | Push final `docs/EVALUATION.md` — needed for slide 6 real numbers |
