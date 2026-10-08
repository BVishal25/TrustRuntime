install:
	uv pip install -e '.[all]'
test:
	uv run pytest -q
seed:
	uv run python scripts/seed_demo.py
run:
	uv run uvicorn app.main:app --reload
benchmark:
	uv run python scripts/benchmark.py
docker-up:
	docker compose up --build
