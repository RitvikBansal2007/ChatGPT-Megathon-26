# GreenDash

> The green recommendation that shows its receipts.  
> ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies.

Megathon X · Singularity · Problem Statement 1 (Lloyds)  
Team: G1-K, G1-A (G1) · G2-An, G2-M (G2) · G3

---

## Quick start

### 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock       # hash-pinned; needs Python 3.11
```

> **Requires:** `streamlit >= 1.50` (the UI uses `width="stretch"` and variable fonts in config.toml)

### 2. Run the UI (fixtures mode — no API key needed)

```bash
DEMO_MODE=fixtures streamlit run app/Home.py
```

Opens on http://localhost:8501. Use the role switcher to pick a persona.

### 3. Run with the live API

```bash
cp .env.example .env          # fill in LLM_API_KEY, JWT_SECRET
DEMO_MODE=live uvicorn api.main:app --reload &   # start FastAPI
DEMO_MODE=live streamlit run app/Home.py
```

### 4. Run tests

```bash
pytest app/tests/          # UI smoke tests (AppTest)
pytest tests/              # backend unit / security / invariance tests
```

---

## DEMO_MODE values

| Value | Behaviour |
|---|---|
| `fixtures` | UI reads `fixtures/*.json`; no API, no LLM key needed |
| `cached` | Packs from `out/cache/`; falls back to in-process on API failure |
| `live` | Full FastAPI + live LLM through cache |

---

## Folder ownership

| Folder | Owner |
|---|---|
| `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md` | G3 |
| `api/`, `greendash/features`, `greendash/rules`, `greendash/orchestrator.py`, `greendash/db/`, `greendash/scenarios/`, `config/`, `Makefile`, `pyproject.toml`, `fixtures/` | G1-A |
| `greendash/security/`, `greendash/llm/minimise.py`, `greendash/llm/guard.py`, `greendash/llm/claimcheck.py`, `infra/`, `SECURITY.md` | G1-K |
| `greendash/generator/`, `greendash/carbon/`, `ingest/`, `data/priors/` | G2-An |
| `greendash/models/`, `greendash/categoriser/`, `greendash/llm/explainer.py`, `greendash/llm/client.py`, `greendash/llm/templates.py`, `eval/`, `docs/EVALUATION.md` | G2-M |

Cross-folder changes → 2-line PR + chat ping.

---

## Important rules

- **Never commit** `.env`, `keys/`, `data/raw/`, `*.db`, API keys or JWT secrets.
- **Never import** engines directly from `app/` — all data goes through `app/client.py`.
- **Never hard-code** hex values in UI — use `app/theme.py` only.
- Every page shows the synthetic-data banner.
