.PHONY: run-bot run-web-prod run-web-debug test lint install clean activate freeze

PYTHONPATH := src
VENV := venv/bin
PYTHON := python3

# Запуск приложений
run-bot:
	PYTHONPATH=$(PYTHONPATH) ./src/bot/main.py

run-web-prod:
	PYTHONPATH=$(PYTHONPATH) ./src/web/run_web.py

run-web-debug:
	PYTHONPATH=$(PYTHONPATH) ./src/web/app.py

# Активация виртуальной среды
activate:
	@echo "Для активации виртуальной среды выполните:"
	@echo "source venv/bin/activate"

# Создание requirements.txt
freeze:
	$(VENV)/pip freeze > requirements.txt

install:
	venv/bin/pip install -r requirements.txt

install-certbot:
	@echo "Установка certbot..."
	venv/bin/pip install certbot certbot-nginx
	@echo ""
	@echo "✅ Certbot установлен"
	@echo "Для получения сертификата выполните:"
	@echo "  make setup-ssl DOMAIN=studhelper.ru EMAIL=despairr@gmail.com"
	@echo ""
	@echo "Подробнее см. config/SSL.md"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=bratishkabot --cov-report=html --cov-report=term

lint:
	@echo "Проверка ruff..."
	ruff check --fix
	@echo "Проверка flake8..."
	flake8

ruff-fix:
	$(VENV)/ruff check --fix

# Тесты
test:
	PYTHONPATH=$(PYTHONPATH) $(VENV)/pytest

# Линтеры
lint:
	$(VENV)/flake8 src/

# Очистка
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
ruff-fix-unsafe:
	ruff check --fix --unsafe-fixes

# SSL управление
setup-ssl:
	@if [ -z "$(DOMAIN)" ]; then \
		echo "❌ Ошибка: укажите DOMAIN"; \
		exit 1; \
	fi
	@if [ -z "$(EMAIL)" ]; then \
		echo "❌ Ошибка: укажите EMAIL"; \
		exit 1; \
	fi
	@echo "🔒 Получение SSL сертификата для $(DOMAIN)..."
	@echo ""
	sudo mkdir -p /var/www/certbot
	sudo certbot certonly --webroot \
		-w /var/www/certbot \
		-d $(DOMAIN) \
		--email $(EMAIL) \
		--agree-tos \
		--no-eff-email
	@echo ""
	@echo "✅ Сертификат получен!"
	@echo "Обновите nginx конфиг, заменив studteams.example.com на $(DOMAIN)"
	@echo "Затем: sudo nginx -t && sudo systemctl reload nginx"

renew-ssl:
	@echo "🔄 Обновление SSL сертификатов..."
	sudo certbot renew
	@echo "✅ Готово!"

test-ssl-renewal:
	@echo "🧪 Тестирование обновления SSL сертификатов (dry-run)..."
	sudo certbot renew --dry-run
	@echo "✅ Тест завершён!"

list-ssl:
	@echo "📜 Список SSL сертификатов:"
	sudo certbot certificates
