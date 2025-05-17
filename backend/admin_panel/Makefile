.PHONY: lint test run-lint run-test

lint:
	@echo "Running linting..."
	uv run ruff check .
	uv run mypy .
	@echo "Linting completed."

test:
	@echo "Running tests..."
	uv run pytest .
	@echo "Tests completed."

run-lint:
	@echo "Running linting inside container..."
	docker-compose run --rm admin_panel make lint

run-test:
	@echo "Running tests inside container..."
	docker-compose run --rm admin_panel make test
