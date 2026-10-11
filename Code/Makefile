.PHONY: keys fetch data features train packs eval test audit app all bench lcl demo demo-offline warm pipeline

PY ?= python

keys:
	@echo "Keys script not provided, skipping"

fetch:
	$(PY) -m ingest.priors

data:
	$(PY) -m greendash.generator

features:
	$(PY) -m greendash.features

train:
	$(PY) -m greendash.categoriser.evaluate
	$(PY) -m greendash.models.train
	$(PY) -m greendash.models.calibrate
	$(PY) -m greendash.models.generate_hashes

packs:
	$(PY) -m greendash.packs
	$(PY) -m greendash.cache

eval:
	$(PY) -m greendash.models.score
	$(PY) -m greendash.models.evaluate_models
	$(PY) -m eval.report

test:
	$(PY) -m pytest -q app/tests tests/

audit:
	bandit -q -r greendash api
	pip-audit
	gitleaks detect --no-banner

bench:
	$(PY) -m eval.bench

app:
	uvicorn api.main:app --host 127.0.0.1 --port 8000 &
	streamlit run app/Home.py --server.address 127.0.0.1

# Summarise the smart-meter file in dataset/ into data/priors/lcl_profile.json (about 4 minutes, needs the 8 GB file).
# The result is committed, so the pipeline does not need the raw file.
lcl:
	$(PY) -m ingest.lcl

# Start the API and the web app together in live mode with one-off local secrets.
# Cross-platform (Windows, macOS, Linux); see scripts/demo.py. Ctrl+C stops both.
demo:
	$(PY) scripts/demo.py

# Web app only, on the bundled sample data (no API, no pipeline needed).
demo-offline:
	$(PY) scripts/demo.py --no-live

# Pre-generate the model-written explanations for the 8 demo customers (needs GEMINI_API_KEY in .env).
# Paced for free-tier rate limits; already-cached explanations are skipped, so it is safe to re-run.
warm:
	$(PY) scripts/warm.py

pipeline: data features train packs eval
	$(PY) -m greendash.manifest

all: pipeline test
