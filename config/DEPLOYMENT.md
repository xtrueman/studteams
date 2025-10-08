# Инструкция по развертыванию StudTeams на сервере

## Требования

- Ubuntu/Debian Linux сервер
- Python 3.12+
- MySQL 8.0+
- Nginx
- Systemd (для автозапуска сервисов)

## 1. Подготовка сервера

### Установка необходимых пакетов

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip nginx mysql-server git
```

### Создание директорий проекта

```bash
sudo mkdir -p /srv/studteams
sudo chown $USER:$USER /srv/studteams
```

## 2. Клонирование проекта

```bash
cd /srv
git clone <repository_url> studteams
cd studteams
```

## 3. Настройка Python окружения

```bash
# Создание виртуального окружения
python3.12 -m venv venv

# Активация окружения
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Настройка конфигурации

### Копирование и заполнение секретов

```bash
cd /srv/studteams/config

# Скопируйте шаблоны
cp secrets.yaml.template secrets.yaml
cp secrets-tgbot.yaml.template secrets-tgbot.yaml

# Отредактируйте секреты
nano secrets.yaml
nano secrets-tgbot.yaml
```

### Проверка конфигурации

```bash
cd /srv/studteams
source venv/bin/activate
python3 -c "import config; print('Config OK')"
```

## 5. Настройка базы данных

### Создание базы данных и пользователя

```bash
sudo mysql -u root -p
```

```sql
-- Создание базы данных
CREATE DATABASE studteams CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Создание пользователя
CREATE USER 'studteams'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Предоставление прав
GRANT ALL PRIVILEGES ON studteams.* TO 'studteams'@'localhost';
FLUSH PRIVILEGES;

-- Выход
EXIT;
```

### Импорт схемы базы данных

```bash
mysql -u studteams -p studteams < database/schema.sql
```

## 6. Настройка Nginx

### Копирование конфигурации

```bash
sudo cp /srv/studteams/config/nginx-studteams.conf /etc/nginx/sites-available/studteams
```

### Редактирование конфигурации

```bash
sudo nano /etc/nginx/sites-available/studteams
```

Измените `server_name` на ваш домен или IP-адрес.

### Создание симлинка и проверка

```bash
# Создание симлинка
sudo ln -s /etc/nginx/sites-available/studteams /etc/nginx/sites-enabled/

# Удаление дефолтного сайта (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезагрузка nginx
sudo systemctl reload nginx
```

## 7. Создание Systemd сервиса для веб-приложения

### Создание файла сервиса

```bash
sudo nano /etc/systemd/system/studteams-web.service
```

Содержимое файла:

```ini
[Unit]
Description=StudTeams Web Application
After=network.target mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/srv/studteams
Environment="PATH=/srv/studteams/venv/bin"
ExecStart=/srv/studteams/venv/bin/uvicorn web.studhelper:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=studteams-web

[Install]
WantedBy=multi-user.target
```

### Создание файла сервиса для Telegram бота

```bash
sudo nano /etc/systemd/system/studteams-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=StudTeams Telegram Bot
After=network.target mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/srv/studteams
Environment="PATH=/srv/studteams/venv/bin"
ExecStart=/srv/studteams/venv/bin/python3 bot.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=studteams-bot

[Install]
WantedBy=multi-user.target
```

### Настройка прав доступа

```bash
# Изменение владельца файлов
sudo chown -R www-data:www-data /srv/studteams

# Создание директории для логов
sudo mkdir -p /srv/studteams/logs
sudo chown www-data:www-data /srv/studteams/logs
```

### Запуск сервисов

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Запуск веб-приложения
sudo systemctl start studteams-web
sudo systemctl enable studteams-web

# Запуск бота
sudo systemctl start studteams-bot
sudo systemctl enable studteams-bot

# Проверка статуса
sudo systemctl status studteams-web
sudo systemctl status studteams-bot
```

## 8. Настройка SSL (опционально, но рекомендуется)

### Установка Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Получение сертификата

```bash
sudo certbot --nginx -d studteams.example.com
```

Certbot автоматически настроит SSL и обновит конфигурацию nginx.

### Автоматическое обновление сертификата

```bash
# Проверка автообновления
sudo certbot renew --dry-run
```

## 9. Управление сервисами

### Просмотр логов

```bash
# Логи веб-приложения
sudo journalctl -u studteams-web -f

# Логи бота
sudo journalctl -u studteams-bot -f

# Логи nginx
sudo tail -f /var/log/nginx/studteams-access.log
sudo tail -f /var/log/nginx/studteams-error.log
```

### Перезапуск сервисов

```bash
# Перезапуск веб-приложения
sudo systemctl restart studteams-web

# Перезапуск бота
sudo systemctl restart studteams-bot

# Перезагрузка nginx
sudo systemctl reload nginx
```

### Остановка сервисов

```bash
sudo systemctl stop studteams-web
sudo systemctl stop studteams-bot
```

## 10. Обновление приложения

```bash
cd /srv/studteams

# Получение обновлений
git pull

# Активация окружения
source venv/bin/activate

# Обновление зависимостей
pip install --upgrade -r requirements.txt

# Перезапуск сервисов
sudo systemctl restart studteams-web
sudo systemctl restart studteams-bot
```

## 11. Мониторинг и обслуживание

### Проверка статуса

```bash
# Статус всех сервисов
sudo systemctl status studteams-*

# Проверка nginx
sudo nginx -t
curl -I http://localhost
```

### Ротация логов

Создайте `/etc/logrotate.d/studteams`:

```
/srv/studteams/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl reload studteams-web > /dev/null 2>&1 || true
        systemctl reload studteams-bot > /dev/null 2>&1 || true
    endscript
}
```

## 12. Безопасность

### Firewall

```bash
# Разрешаем HTTP, HTTPS и SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Регулярные обновления

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y
```

## Проблемы и решения

### Сервис не запускается

```bash
# Проверка логов
sudo journalctl -u studteams-web -n 50

# Проверка прав доступа
ls -la /srv/studteams
```

### 502 Bad Gateway

- Проверьте, что приложение запущено: `sudo systemctl status studteams-web`
- Проверьте порт в nginx и в systemd сервисе (должен быть 8000)
- Проверьте логи: `sudo journalctl -u studteams-web -f`

### Статика не загружается

- Проверьте права доступа: `ls -la /srv/studteams/web/static/`
- Проверьте конфигурацию nginx: `sudo nginx -t`
- Проверьте логи nginx: `sudo tail -f /var/log/nginx/studteams-error.log`
