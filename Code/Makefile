.PHONY: keys fetch data features train packs eval test audit app all bench lcl demo warm pipeline

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
	PYTHONPATH=. $(PY) -m pytest -q app/tests tests/

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

# Start the API and the web app together in live mode with one-off local secrets. Ctrl+C stops both.
demo:
	@test -d out/packs || (echo "Run 'make pipeline' first" && exit 1)
	@export ENV=demo JWT_SECRET=$$($(PY) -c "import secrets;print(secrets.token_urlsafe(48))") \
	  DATA_KEY=$$($(PY) -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"); \
	trap 'kill 0' INT TERM EXIT; \
	$(PY) -m uvicorn api.main:app --host 127.0.0.1 --port 8000 & \
	DEMO_MODE=live API_BASE_URL=http://127.0.0.1:8000 $(PY) -m streamlit run app/Home.py --server.address 127.0.0.1 --server.port 8501

# Pre-generate the model-written explanations for the 8 demo customers (needs GEMINI_API_KEY in .env).
# Paced for free-tier rate limits; already-cached explanations are skipped, so it is safe to re-run.
warm:
	$(PY) -c "import time; from api.services import load_customer_packs as f; [(f('CUST-000%d' % i, 'CUST-000%d' % i), print('CUST-000%d' % i), time.sleep(20)) for i in range(1, 9)]"

pipeline: data features train packs eval
	$(PY) -m greendash.manifest

all: pipeline test
