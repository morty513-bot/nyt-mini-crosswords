FRONTEND_DIR := frontend
BACKEND_DIR := backend

.PHONY: backend-install backend-test backend-dev frontend-install frontend-dev frontend-build build

backend-install:
	cd $(BACKEND_DIR) && python3 -m pip install -e '.[dev]'

backend-test:
	cd $(BACKEND_DIR) && pytest

backend-dev:
	cd $(BACKEND_DIR) && uvicorn nyt_mini_crosswords.app:app --reload --port 8790

frontend-install:
	cd $(FRONTEND_DIR) && npm install

frontend-dev:
	cd $(FRONTEND_DIR) && npm run dev

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

build: frontend-build
