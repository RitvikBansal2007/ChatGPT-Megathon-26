.PHONY: keys fetch data features train packs eval test audit app all bench

PY ?= python

keys:
	$(PY) -m greenproof.security.keys

fetch:
	$(PY) -m ingest.priors

data:
	$(PY) -m greenproof.generator

features:
	$(PY) -m greenproof.features

train:
	$(PY) -m greenproof.categoriser.evaluate
	$(PY) -m greenproof.models.train

packs:
	$(PY) -m greenproof.packs
	$(PY) -m greenproof.cache

eval:
	$(PY) -m eval.report

test:
	$(PY) -m pytest -q

audit:
	bandit -q -r greenproof api
	pip-audit
	gitleaks detect --no-banner

bench:
	$(PY) -m eval.bench

app:
	uvicorn api.main:app --host 127.0.0.1 --port 8000 &
	streamlit run app/Home.py --server.address 127.0.0.1

all: keys fetch data features train packs eval test
	$(PY) -m greenproof.manifest
