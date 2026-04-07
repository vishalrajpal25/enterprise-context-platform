PYTHON ?= python3
UVICORN ?= uvicorn
OPA_DEFAULT_ALLOW ?= true

.PHONY: help up down init seed api mcp test eval security-smoke load-smoke demo

help:
	@echo "ECP commands:"
	@echo "  make up             - start docker dependencies"
	@echo "  make down           - stop docker dependencies"
	@echo "  make init           - initialize postgres schema"
	@echo "  make seed           - seed postgres + neo4j demo data"
	@echo "  make api            - run FastAPI service on :8080"
	@echo "  make mcp            - run MCP stdio server"
	@echo "  make test           - run pytest suite"
	@echo "  make eval           - run golden + security + load smoke against local API"
	@echo "  make demo           - full local demo setup (up/init/seed)"

up:
	docker compose up -d

down:
	docker compose down

init:
	$(PYTHON) scripts/init_db.py

seed:
	$(PYTHON) scripts/seed_data.py

api:
	ECP_OPA_DEFAULT_ALLOW=$(OPA_DEFAULT_ALLOW) $(UVICORN) src.main:app --reload --port 8080

mcp:
	cd src/protocol && npm ci && npm start

test:
	$(PYTHON) -m pytest tests/ -q

eval:
	ECP_OPA_DEFAULT_ALLOW=$(OPA_DEFAULT_ALLOW) $(PYTHON) scripts/run_golden_eval.py http://127.0.0.1:8080
	ECP_OPA_DEFAULT_ALLOW=$(OPA_DEFAULT_ALLOW) $(PYTHON) scripts/security_smoke.py http://127.0.0.1:8080
	ECP_OPA_DEFAULT_ALLOW=$(OPA_DEFAULT_ALLOW) $(PYTHON) scripts/load_smoke.py http://127.0.0.1:8080 30 3 5000 "" 10 1

demo: up init seed
	@echo "Demo infra is ready."
	@echo "Next: run 'make api' in one terminal and 'make eval' in another."
