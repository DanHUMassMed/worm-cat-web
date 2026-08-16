.PHONY: help install dev start-dev prod start-prod stop restart status logs test lint clean ensure-uv

export PATH := $(HOME)/.local/bin:$(HOME)/.cargo/bin:$(PATH)

VENV := .venv
PYTHON := $(VENV)/bin/python
UV := $(shell command -v uv 2>/dev/null || echo "$(HOME)/.local/bin/uv")

help:
	@echo "WormCat Web Service Control"
	@echo "Available commands:"
	@echo "  make install    - Create .venv and install all dependencies via uv"
	@echo "  make start-dev  - Start development services (Redis, Celery, Web App)"
	@echo "  make dev        - Alias for start-dev"
	@echo "  make start-prod - Start production services (Redis, Celery, Web App)"
	@echo "  make prod       - Alias for start-prod"
	@echo "  make stop       - Stop Web and Celery services (leaves Redis running)"
	@echo "  make stop-redis - Explicitly stop Redis server"
	@echo "  make restart    - Restart all services in dev mode"
	@echo "  make status     - Check status of running services"
	@echo "  make logs       - Tail service logs"
	@echo "  make test       - Run pytest test suite using uv"
	@echo "  make test-r     - Test worm_cat.R execution and verify expected outputs"
	@echo "  make lint       - Run static analysis and code checks"
	@echo "  make clean      - Remove runtime logs, pid files, cache, and build artifacts"

ensure-uv:
	@if ! command -v uv >/dev/null 2>&1 && [ ! -f $(UV) ]; then \
		echo "uv not found. Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh || pip install uv; \
	fi

install: ensure-uv
	$(UV) sync

dev start-dev:
	./sys_ctrl.sh start dev

prod start-prod:
	./sys_ctrl.sh start prod

stop:
	./sys_ctrl.sh stop

stop-redis:
	./sys_ctrl.sh stop redis

restart:
	./sys_ctrl.sh restart dev

status:
	./sys_ctrl.sh status

logs:
	./sys_ctrl.sh logs

test: ensure-uv
	$(UV) run pytest || true

test-r: ensure-uv
	$(UV) run python worm_cat/test_wormcat_r.py

lint: ensure-uv
	$(UV) run ruff check . || true

clean:
	./sys_ctrl.sh stop 2>/dev/null || true
	rm -rf .pytest_cache .uv .run logs *.egg-info build dist
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pid" -delete 2>/dev/null || true
