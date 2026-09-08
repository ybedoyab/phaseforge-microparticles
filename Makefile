PYTHON ?= python
UV ?= uv

.PHONY: setup test lint models figures report reproduce cfd-check cfd audit

setup:
	$(UV) sync --extra dev

test:
	$(UV) run pytest --cov=phaseforge --cov-report=term-missing

lint:
	$(UV) run ruff check phaseforge tests scripts
	$(UV) run ruff format --check phaseforge tests scripts

models:
	$(UV) run python scripts/reproduce_all.py --skip-figures --skip-report

figures:
	$(UV) run python scripts/reproduce_all.py --figures-only

report:
	$(UV) run python scripts/build_evidence_table.py
	$(UV) run python scripts/reproduce_all.py --report-only

reproduce:
	$(UV) run python scripts/reproduce_all.py

cfd-check:
	bash scripts/run_cfd.sh --check

cfd:
	bash scripts/run_cfd.sh

audit:
	$(UV) run pytest --cov=phaseforge --cov-report=term-missing
	$(UV) run ruff check phaseforge tests scripts
	$(UV) run python scripts/reproduce_all.py
	$(UV) run python scripts/build_evidence_table.py
