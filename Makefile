.PHONY: all acquire ingest index eval test dev clean lint

PYTHON ?= python

acquire:
	$(PYTHON) scripts/acquire_data.py --scope minimal

ingest:
	$(PYTHON) -m src.ingest.pipeline

index:
	$(PYTHON) scripts/build_indexes.py

eval:
	$(PYTHON) -m eval.run_all

test:
	pytest -v --cov=src

dev:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
