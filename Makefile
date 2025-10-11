.PHONY: *

# Активация виртуальной среды
activate:
	@echo "Для активации виртуальной среды выполните:"
	@echo "source venv/bin/activate"

# Запуск бота
run:
	venv/bin/python bot.py

# Создание requirements.txt
freeze:
	venv/bin/pip freeze > requirements.txt

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
	ruff check --fix
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
