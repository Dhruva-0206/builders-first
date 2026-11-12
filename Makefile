# Builders First — run `make setup all` for the offline path (no credentials needed).
# Override the interpreter with `make PY=python ...` to use an existing environment.
ifeq ($(OS),Windows_NT)
  PY ?= .venv/Scripts/python.exe
  BOOT := python
else
  PY ?= .venv/bin/python
  BOOT := python3
endif
export PYTHONPATH := src

.PHONY: setup data analysis site test all clean

setup:
	$(BOOT) -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

# Needs network + GITHUB_TOKEN, GCP_PROJECT, GOOGLE_APPLICATION_CREDENTIALS (see .env.example)
data:
	$(PY) -m builders_first.ingest_ecosystems
	$(PY) -m builders_first.ingest_hackathon
	$(PY) -m builders_first.ingest_bigquery
	$(PY) -m builders_first.ingest_github

analysis:
	$(PY) -m builders_first.claims

site:
	$(PY) -m builders_first.build_site

test:
	$(PY) -m pytest -q

all: analysis site test

clean:
	rm -rf .pytest_cache src/builders_first/__pycache__ tests/__pycache__
