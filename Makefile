PYTHON ?= python3

.PHONY: install build test smoke main-table coefficient-ablation virginia-beach

install:
	$(PYTHON) -m pip install -r requirements.txt

build:
	$(PYTHON) -m pip install -e .

test: build
	$(PYTHON) -m pytest -q

smoke: build
	$(PYTHON) scripts/smoke_test.py

main-table: build
	$(PYTHON) scripts/reproduce_main_table.py --full

coefficient-ablation: build
	$(PYTHON) scripts/reproduce_coefficient_ablation.py

virginia-beach: build
	$(PYTHON) scripts/reproduce_virginia_beach.py
