FRONTEND_DIR := frontend
BACKEND_DIR := backend

.PHONY: backend-install backend-test backend-dev backend-sweep backend-report backend-compare-optimizations frontend-install frontend-dev frontend-build build

backend-install:
	cd $(BACKEND_DIR) && python3 -m pip install -e '.[dev]'

backend-test:
	cd $(BACKEND_DIR) && pytest

backend-dev:
	cd $(BACKEND_DIR) && uvicorn nyt_mini_crosswords.app:app --reload --port 8790

backend-sweep:
	cd $(BACKEND_DIR) && python scripts/sweep_generation.py --start-seed 1 --count 100 --time-budget-ms 1000 --candidate-limit 64 --max-search-nodes 20000

backend-report:
	cd $(BACKEND_DIR) && python scripts/generate_report.py --label baseline --start-seed 1 --count 100 --time-budget-ms 1000 --candidate-limit 64 --max-search-nodes 20000

backend-compare-optimizations:
	cd $(BACKEND_DIR) && python scripts/compare_optimizations.py --start-seed 1 --count 50 --time-budget-ms 1000 --candidate-limit 64 --max-search-nodes 20000

frontend-install:
	cd $(FRONTEND_DIR) && npm install

frontend-dev:
	cd $(FRONTEND_DIR) && npm run dev

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

build: frontend-build
