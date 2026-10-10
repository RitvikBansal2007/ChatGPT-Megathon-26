# GreenProof

> The green recommendation that shows its receipts.  
> ML predicts. Rules decide eligibility. The carbon engine calculates. The LLM only explains. Claim-Check verifies.

Megathon X · Singularity · Problem Statement 1 (Lloyds)  
Team: Kratik, Akshit (G1) · Aniket, Madhav (G2) · Ritvik (G3)

---

## Quick start

### 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock       # hash-pinned; needs Python 3.11
```

> **Requires:** `streamlit >= 1.46` (for variable font support in config.toml)

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
| `app/`, `mobile/`, `slides/`, `docs/diagrams/`, `README.md` | G3 — Ritvik |
| `api/`, `greenproof/features`, `greenproof/rules`, `greenproof/orchestrator.py`, `greenproof/db/`, `greenproof/scenarios/`, `config/`, `Makefile`, `pyproject.toml`, `fixtures/` | G1-A — Akshit |
| `greenproof/security/`, `greenproof/llm/minimise.py`, `greenproof/llm/guard.py`, `greenproof/llm/claimcheck.py`, `infra/`, `SECURITY.md` | G1-K — Kratik |
| `greenproof/generator/`, `greenproof/carbon/`, `ingest/`, `data/priors/` | G2-An — Aniket |
| `greenproof/models/`, `greenproof/categoriser/`, `greenproof/llm/explainer.py`, `greenproof/llm/client.py`, `greenproof/llm/templates.py`, `eval/`, `docs/EVALUATION.md` | G2-M — Madhav |

Cross-folder changes → 2-line PR + chat ping.

---

## Important rules

- **Never commit** `.env`, `keys/`, `data/raw/`, `*.db`, API keys or JWT secrets.
- **Never import** engines directly from `app/` — all data goes through `app/client.py`.
- **Never hard-code** hex values in UI — use `app/theme.py` only.
- Every page shows the synthetic-data banner.
