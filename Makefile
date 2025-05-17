.PHONY: up down build logs clean check-status run-lint-all run-test-all

up:
		@echo "Starting all services..."
		docker-compose up -d
		@make check-status

down:
		@echo "Stopping and removing containers..."
		docker-compose down
		@echo "Done."

build:
		@echo "Building Docker images..."
		docker-compose build
		@echo "Build completed. Checking logs for errors..."
		docker-compose logs

logs:
		@echo "Displaying logs for all services..."
		docker-compose logs -f

logs-service:
		@echo "Enter service name (e.g., admin_panel, web_api, kafka_consumer): "
		@read service; \
		docker-compose logs -f $$service

check-status:
		@echo "Service status:"
		docker-compose ps

clean:
		@echo "Cleaning up images and volumes..."
		docker-compose down -v
		docker image prune -f
		@echo "Cleanup completed."

debug-build:
		@echo "Debugging build process..."
		docker-compose build --no-cache
		docker-compose logs

run-lint-all:
		@echo "Running linting for all services..."
		make -C backend/admin_panel run-lint
		make -C backend/web_api run-lint
		make -C backend/kafka_consumer run-lint
		@echo "Linting completed for all services."

run-test-all:
		@echo "Running tests for all services..."
		make -C backend/admin_panel run-test
		make -C backend/web_api run-test
		make -C backend/kafka_consumer run-test
		@echo "Tests completed for all services."
