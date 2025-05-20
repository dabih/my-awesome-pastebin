.PHONY: lint test audit run-lint run-test run-audit

lint:
	@echo "Running linting..."
	uv run ruff check .
	uv run ruff format
	uv run isort .
	uv run mypy .
	uv run black --check .
	uv run flake8 src
	uv run pylint src
	@echo "Linting completed."

test:
	@echo "Running tests..."
	uv run pytest .
	@echo "Tests completed."

audit:
	@echo "Running audit..."
	uv run pip-audit
	@echo "Audit completed."

run-lint:
	@echo "Running linting inside container..."
	docker-compose run --rm admin_panel make lint

run-test:
	@echo "Running tests inside container..."
	docker-compose run --rm admin_panel make test

run-audit:
	@echo "Running audit inside container..."
	docker-compose run --rm admin_panel make audit
