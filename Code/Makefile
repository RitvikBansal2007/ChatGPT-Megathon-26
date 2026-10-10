.PHONY: keys fetch data features train packs eval test audit app all bench

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

packs:
	$(PY) -m greendash.packs
	$(PY) -m greendash.cache

eval:
	$(PY) -m eval.report

test:
	$(PY) -m pytest -q

audit:
	bandit -q -r greendash api
	pip-audit
	gitleaks detect --no-banner

bench:
	$(PY) -m eval.bench

app:
	uvicorn api.main:app --host 127.0.0.1 --port 8000 &
	streamlit run app/Home.py --server.address 127.0.0.1

all: keys fetch data features train packs eval test
	$(PY) -m greendash.manifest
