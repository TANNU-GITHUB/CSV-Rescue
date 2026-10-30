.PHONY: dev test lint build docker gen-api bench samples smoke

dev:
	@echo "Start backend: cd backend && uvicorn app.main:app --reload --port 8000"
	@echo "Start frontend: cd frontend && npm run dev"

test:
	cd backend && python -m pytest -q --tb=short
	cd frontend && npm test -- --run

lint:
	cd backend && ruff check app tests || true
	cd frontend && npm run lint || true

build:
	cd frontend && npm run build

docker:
	docker compose build

gen-api:
	cd frontend && npm run gen:api

bench:
	cd backend && python -m benchmarks.run_benchmark

samples:
	cd backend && python -m app.samples.generate_samples

smoke:
	bash scripts/smoke.sh http://localhost:8000
