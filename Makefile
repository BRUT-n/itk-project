.PHONY: run stop lint format check test

# Запуск всего проекта в докере
run:
	docker compose up --build

# Остановка и удаление контейнеров
stop:
	docker compose down

# Проверка стиля и ошибок (линтер)
lint:
	uv run ruff check .
	uv run pyright app/

# Автоматическое исправление стиля и сортировка импортов
format:
	uv run ruff format .
	uv run ruff check --fix .

# Полная проверка перед пушем
check: format lint

# Заглушка для тестов (настроим позже)
test:
	POSTGRES_DB=test_db uv run pytest tests/

test-clean:
	docker stop $$(docker ps -q --filter ancestor=postgres:17-alpine) || true