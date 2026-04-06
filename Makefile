.PHONY: run stop lint format check test

run:
	docker compose up --build

stop:
	docker compose down

lint:
	uv run ruff check .
	uv run pyright app/

format:
	uv run ruff format .
	uv run ruff check --fix .

check: format lint

test:
	POSTGRES_DB=test_db uv run pytest tests/

test-clean:
	docker stop $$(docker ps -q --filter ancestor=postgres:17-alpine) || true