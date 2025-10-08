.PHONY: *

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=bratishkabot --cov-report=html --cov-report=term

lint:
	@echo "Проверка flake8..."
	flake8
	@echo "Проверка ruff..."
	ruff check

ruff-fix:
	ruff check --fix
ruff-fix-unsafe:
	ruff check --fix --unsafe-fixes
