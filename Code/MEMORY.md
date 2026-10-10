# GreenProof — G3 (Ritvik) Context Memory
<!-- AUTO-UPDATED by Antigravity agent. Last update: 2026-10-11T02:18 IST -->

> Repo: https://github.com/IIIT-ECell/megathon26-chatgpt  
> Branch: `main` · Repo root: `megathon26-chatgpt/Code/`  
> Ritvik owns: `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md`, `MEMORY.md`  
> Rule: never edit `greenproof/`, `api/`, `data/`, `config/`, `eval/`, `tests/` (backend folders)

---

## ✅ COMPLETED

### Step 1 — Brand tokens (commit `536f3e9`)
- `app/.streamlit/config.toml` — Streamlit theme (Canopy primary, Mist bg, XSRF on, font serving, 3 fontFaces)
- `app/theme.py` — COLORS, DARK, STATUS×5, BADGES×3, METRICS×4, SPACING, RADIUS, FONT_SIZES, TAP_TARGET, css()
- `app/static/fonts/` — InterVariable.woff2, PlusJakartaSans-Variable.woff2, JetBrainsMono-Variable.woff2 (OFL)
- `app/CLAUDE.md` — rules file for Claude Code

### Step 2 — Pre-Step 3 setup (commit `19a3634`)
- Greyscale check: PASSED — 5 statuses differ by icon+label alone
- Fonts in place; Akshit needs to pin `streamlit>=1.46` in pyproject.toml
- `docs/design/proof_card.png` + `docs/design/cockpit.png` committed (v0 reference)
- `.gitignore`, `README.md`, folder scaffold committed

### Step 3.1 — Streamlit skeleton (commit `452c37b`)
- `app/Home.py` — landing, banner, 12-role switcher, page links
- `app/client.py` — DEMO_MODE gateway, fixtures mode fully working
- `app/components/chrome.py` — banner(), current_role(), ROLES list
- `app/pages/1_Customer_Hub.py` — placeholder (now upgraded, see Step 3.2-3.3)
- `app/pages/2_Cockpit.py` — placeholder (now upgraded, see Step 3.4)
- `app/pages/3_Receipts.py` — placeholder (now upgraded, see Step 3.7)
- `app/tests/test_smoke.py` — AppTest smoke for all 4 pages + role + mode guards
- `app/brand guidelines/` + `app/basic ui example/` — committed for reference

### Steps 3.2–3.4 + 3.7 — Components & real pages (commit `TBD — being committed now`)
- `fixtures/opportunities.json` — 4 opps covering RECOMMEND / SOFT_SURFACE / ABSTAIN / RULED_OUT
- `fixtures/scenario.json`, `claimcheck.json`, `portfolio.json`, `eval.json`
- `app/components/badges.py` — 3 separate verdict badges (Likelihood · Eligibility · Impact quality)
- `app/components/states.py` — ABSTAIN / REVIEW / RULED_OUT / SOFT_SURFACE renderers
- `app/components/claim_stamp.py` — "N of N sentences verified" stamp
- `app/components/proof_card.py` — full RECOMMEND card + dispatch to states
- `app/pages/1_Customer_Hub.py` — FULL: 4 pathway tiles, sorted, drill-down, Proof Card
- `app/pages/2_Cockpit.py` — FULL: 4 metric tiles, funnel, scatter quadrant, segments, governance
- `app/pages/3_Receipts.py` — FULL: lift table, calibration, Brier, LLM eval, scenario suite

---

## 🔴 REMAINING (Ritvik's tasks)

### Step 3.5 — Live API (needs Akshit's FastAPI running)
- File: `app/client.py`
- Add `live` mode: POST /api/auth/demo-token → Bearer, refresh at 15min
- Add `cached` mode: try API, fall back to out/cache/ read-only
- Show friendly error card on 401/403/5xx
- **Blocker: Akshit must have `api/` ready and running**

### Step 3.6 — Scenario Lab + red-team button
- File: `app/components/scenario_lab.py` (CREATE)
- File: `app/pages/1_Customer_Hub.py` (ADD side panel for Evaluator/RM roles)
- 7 toggles → client.run_scenario() → status transition badge + diff + cause + invariance
- Red-team button → fixed sentence → client.claimcheck() → highlight violations
- **Blocker: needs live API or at least scenario/claimcheck fixtures (already done)**

### Step 3.8 — Polish pass
- Loading spinners on all loads (partially done)
- Empty + error states on every component
- 390px check — open Chrome DevTools mobile view
- pytest app/tests/ — all green

### Step 4a — Export Mermaid diagrams (~T+8:00)
- Run in Claude Code: extract mermaid blocks from Architecture.md, export PNG+SVG
- Output: `docs/diagrams/*.mmd`, `docs/diagrams/*.png`, `docs/diagrams/*.svg`

### Step 4b — mobile/README.md (~T+8:00)
- Run in Claude Code: write Expo (React Native) production plan
- Screens: Login, Hub, Proof Card, 4 refusal states, Settings

### Step 5 — Slides deck (claude.ai, ~T+8:00)
- Upload: Architecture.md, theme.py, screenshots from docs/design/, diagram PNGs
- Use Prompt 5a from playbook → 8-slide deck
- After T+9:30 → Prompt 5b with Madhav's EVALUATION.md
- Save exports to `slides/`

### Step 6 — Rehearse + record + submit (~T+9:30–11:15)
- `DEMO_MODE=cached streamlit run app/Home.py` — 2 stopwatch runs
- Test on real phone at 390px
- Record 2-min backup video
- Pre-stage checklist with Akshit + Kratik

---

## ⏳ WAITING ON TEAMMATES

| What | Who | Status |
|---|---|---|
| `streamlit>=1.46` in pyproject.toml | **Akshit (G1-A)** | ⏳ Requested |
| `greenproof/contracts.py` frozen | **Akshit (G1-A)** | ⏳ Should be done at T+1:30 |
| `api/` FastAPI running for CP2 | **Akshit (G1-A)** | ⏳ Needed for Step 3.5 |
| `docs/EVALUATION.md` final numbers | **Madhav (G2-M)** | ⏳ Needed at T+9:30 for slides |
| Claimcheck JSON shape | **Madhav (G2-M)** | ✅ Inferred from JS data |

---

## 📁 Current file map (G3-owned files only)

```
app/
├── .streamlit/config.toml       ✅ committed
├── CLAUDE.md                    ✅ committed
├── Home.py                      ✅ committed
├── client.py                    ✅ committed (fixtures only; live/cached = Step 3.5)
├── theme.py                     ✅ committed
├── components/
│   ├── chrome.py                ✅ committed
│   ├── badges.py                🔄 built, committing now
│   ├── states.py                🔄 built, committing now
│   ├── claim_stamp.py           🔄 built, committing now
│   ├── proof_card.py            🔄 built, committing now
│   └── scenario_lab.py         🔴 Step 3.6
├── pages/
│   ├── 1_Customer_Hub.py        🔄 FULL build, committing now
│   ├── 2_Cockpit.py             🔄 FULL build, committing now
│   └── 3_Receipts.py            🔄 FULL build, committing now
├── tests/
│   └── test_smoke.py            ✅ committed
└── static/fonts/                ✅ committed (3 OFL woff2 files)

fixtures/
├── opportunities.json           🔄 created, committing now
├── scenario.json                🔄 created, committing now
├── claimcheck.json              🔄 created, committing now
├── portfolio.json               🔄 created, committing now
└── eval.json                    🔄 created, committing now

docs/design/                     ✅ proof_card.png + cockpit.png committed
docs/diagrams/                   🔴 Step 4a
mobile/README.md                 🔴 Step 4b
slides/                          🔴 Step 5
```

---

## 🔑 Key rules (never break these)
1. All data through `app/client.py` only. Pages never import from `greenproof/`
2. `theme.css()` called exactly once per page, at the top, with `unsafe_allow_html=True`
3. Every data value in HTML must be `html.escape()`'d first
4. Every status + badge has icon AND text label (never colour alone)
5. 4 metric tiles on Cockpit are ALWAYS separate (never summed)
6. RULED_OUT card has NO action button
7. ABSTAIN names exactly ONE missing input
8. Synthetic-data banner on every page
