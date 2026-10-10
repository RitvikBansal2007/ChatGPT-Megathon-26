# GreenDash — G3 (Ritvik) Context Memory
<!-- AUTO-UPDATED by Antigravity agent. Last update: 2026-10-11T02:25 IST -->

> Repo: https://github.com/IIIT-ECell/megathon26-chatgpt  
> Branch: `main` · Repo root: `megathon26-chatgpt/Code/`  
> Ritvik owns: `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md`, `MEMORY.md`  
> Rule: NEVER edit `greendash/`, `api/`, `data/`, `config/`, `eval/`, `tests/` (backend)

---

## ✅ COMPLETED

### Step 1 — Brand tokens (`536f3e9`)
- `app/.streamlit/config.toml`, `app/theme.py`, `app/static/fonts/` (3 OFL woff2), `app/CLAUDE.md`

### Step 2 — Pre-Step 3 (`19a3634`)
- Greyscale check ✅, fonts in place, v0 screenshots committed to `docs/design/`
- `.gitignore`, `README.md`, folder scaffold

### Step 3.1 — Skeleton (`452c37b`)
- `app/Home.py`, `app/client.py`, `app/components/chrome.py`
- Placeholder pages + `app/tests/test_smoke.py`
- `app/brand guidelines/` + `app/basic ui example/` committed

### Steps 3.2–3.4 + 3.7 — Full components & pages (`1d1fc0d`)
- `fixtures/` — opportunities (RECOMMEND/SOFT_SURFACE/ABSTAIN/RULED_OUT), scenario, claimcheck, portfolio, eval
- `app/components/badges.py` — 3 separate verdict badges
- `app/components/states.py` — 4 non-RECOMMEND renderers
- `app/components/claim_stamp.py` — N of N stamp
- `app/components/proof_card.py` — full RECOMMEND card + dispatch
- `app/pages/1_Customer_Hub.py` — 4 tiles + proof card (placeholder Scenario Lab)
- `app/pages/2_Cockpit.py` — metric tiles, funnel, scatter, segments, governance
- `app/pages/3_Receipts.py` — lift, calibration, Brier, LLM eval, scenario suite

### Step 3.6 — Scenario Lab (`TBD — committing now`)
- `app/components/scenario_lab.py` — 7 mutation toggles, diff table, invariance badge, red-team button
- `app/pages/1_Customer_Hub.py` — wired with Scenario Lab sidebar (Evaluator/RM only)

### Step 3.8 — Polish (`TBD — committing now`)
- `app/tests/test_smoke.py` — full polished suite: 5-status check, path-traversal guard,
  all fixture loads, role switcher, mode guards

### Step 4a — Mermaid diagrams (`TBD — exporting now`)
- `docs/diagrams/system_architecture.mmd`, `data_flow.mmd`, `request_flow.mmd`, `trust_boundaries.mmd`
- PNG exports in progress (mermaid-cli)

### Step 4b — Mobile README (`TBD — committing now`)
- `mobile/README.md` — full Expo production spec: 8 screens, auth flow, security controls

---

## 🔴 REMAINING

### Step 3.5 — Live API (`app/client.py` live + cached modes)
- **Blocker: needs Akshit's `api/` running**
- When ready: add `live` mode (POST /api/auth/demo-token → Bearer, 15-min refresh)
- Add `cached` mode (try API → fall back to out/cache/ read-only)
- Friendly error cards on 401/403/5xx

### Step 5 — Slides (claude.ai)
- Open https://claude.ai → new chat → slide deck
- Upload: `docs/3 Architecture.md`, `app/theme.py`, `docs/design/*.png`, `docs/diagrams/*.png`
- Use Prompt 5a from playbook → 8-slide deck
- After T+9:30: Prompt 5b with Madhav's `docs/EVALUATION.md` (fill [TBD] numbers)
- Save to `slides/` and commit

### Step 6 — Rehearse + record + submit (~T+9:30–11:15)
- `DEMO_MODE=cached streamlit run app/Home.py` — 2 stopwatch runs of PRD §5 demo script
- Test Customer Hub on real phone (390px)
- Record 2-min backup video, copy to 2 devices
- Pre-stage checklist (Architecture.md §5.9) with Akshit + Kratik
- Upload submission A–I

---

## ⏳ TEAMMATE BLOCKERS

| What | Who | Status |
|---|---|---|
| `streamlit>=1.46` in pyproject.toml | **Akshit (G1-A)** | ⏳ Requested |
| `api/` FastAPI running for Step 3.5 CP2 | **Akshit (G1-A)** | ⏳ Needed |
| `docs/EVALUATION.md` final numbers | **Madhav (G2-M)** | ⏳ Needed at T+9:30 for slides |

---

## 📁 Complete G3 file map

```
app/
├── .streamlit/config.toml       ✅
├── CLAUDE.md                    ✅
├── Home.py                      ✅
├── client.py                    ✅ (fixtures done; live/cached = Step 3.5)
├── theme.py                     ✅
├── components/
│   ├── chrome.py                ✅
│   ├── badges.py                ✅
│   ├── states.py                ✅
│   ├── claim_stamp.py           ✅
│   ├── proof_card.py            ✅
│   └── scenario_lab.py         ✅ Step 3.6
├── pages/
│   ├── 1_Customer_Hub.py        ✅ (with Scenario Lab, Step 3.6)
│   ├── 2_Cockpit.py             ✅
│   └── 3_Receipts.py            ✅
├── tests/
│   └── test_smoke.py            ✅ (polished, Step 3.8)
└── static/fonts/                ✅ (3 OFL woff2)

fixtures/
├── opportunities.json           ✅ (RECOMMEND/SOFT_SURFACE/ABSTAIN/RULED_OUT)
├── scenario.json                ✅
├── claimcheck.json              ✅
├── portfolio.json               ✅
└── eval.json                    ✅

docs/design/                     ✅ proof_card.png + cockpit.png
docs/diagrams/                   🔄 .mmd files done; PNGs exporting now
mobile/README.md                 ✅ Step 4b — full Expo spec
slides/                          🔴 Step 5 (claude.ai)
MEMORY.md                        ✅ (this file)
```

---

## 🔑 Rules (never break)
1. All data via `app/client.py` only — no direct engine imports in pages
2. `theme.css()` called exactly ONCE per page, at top, with `unsafe_allow_html=True`
3. All data rendered in HTML must go through `html.escape()` first
4. Every status + badge: icon AND text label (never colour alone)
5. 4 Cockpit metric tiles always SEPARATE — never summed
6. RULED_OUT: NO action button
7. ABSTAIN: names exactly ONE missing input
8. Synthetic-data banner on EVERY page
9. Only `app/` files to be edited — NEVER touch `greendash/`, `api/`, `data/`
