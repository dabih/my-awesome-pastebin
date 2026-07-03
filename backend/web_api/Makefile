.PHONY: lint test audit run-lint run-test run-audit

lint:
	@echo "Running linting..."
	uv run ruff check .
	uv run ruff format
	uv run isort .
	uv run mypy .
	uv run black --check .
	uv run flake8 src --inline-quotes '"'
	uv run pylint src
	@echo "Linting completed."

test:
	@echo "Running tests..."
	uv run pytest .
	@echo "Tests completed."

audit:
	@echo "Running audit..."
	uv run pip-audit --ignore-vuln GHSA-wj6h-64fc-37mp --ignore-vuln CVE-2026-30922 --ignore-vuln PYSEC-2026-161 --ignore-vuln CVE-2026-48818 --ignore-vuln CVE-2026-48817 --ignore-vuln CVE-2026-54283 --ignore-vuln CVE-2026-54282
	@echo "Audit completed."

run-lint:
	@echo "Running linting inside container..."
	docker-compose run --rm web_api make lint

run-test:
	@echo "Running tests inside container..."
	docker-compose run --rm web_api make test

run-audit:
	@echo "Running audit inside container..."
	docker-compose run --rm web_api make audit
