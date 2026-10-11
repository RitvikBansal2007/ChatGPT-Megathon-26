# GreenDash — code

Setup and run instructions are in the repository's top-level `README.md`.

```bash
pip install -e . pytest httpx streamlit plotly
make pipeline   # build data, models, packs, evaluation, manifest
make demo       # API on 127.0.0.1:8000, web app on http://127.0.0.1:8501
make test
```

Deployment notes for the reverse proxy are in `infra/README.md`.
