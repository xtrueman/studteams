# 🚀 Развёртывание StudTeams на production сервере

Подробная инструкция по развёртыванию проекта StudTeams на production сервере с Ubuntu/Debian.

## 📋 Требования

### Системные требования
- Ubuntu 20.04+ / Debian 11+ (или другой Linux с systemd)
- Python 3.14+
- MySQL 8.0+
- Nginx 1.18+
- 1GB+ RAM
- 10GB+ свободного места на диске

### Необходимые доступы
- SSH доступ к серверу с sudo правами
- Доступ к настройке DNS для вашего домена
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)

## 🔧 Подготовка сервера

### 1. Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Установка необходимых пакетов

```bash
# Основные утилиты
sudo apt install -y git curl wget nano htop

# Python 3.14 и зависимости
sudo apt install -y python3.14 python3.14-venv python3.14-dev python3-pip

# Nginx
sudo apt install -y nginx

# MySQL Server
sudo apt install -y mysql-server

# Дополнительные пакеты для сборки
sudo apt install -y build-essential libssl-dev libffi-dev
```

### 3. Настройка MySQL

```bash
# Запуск скрипта безопасной установки
sudo mysql_secure_installation

# Создание базы данных и пользователя
sudo mysql -u root -p
```

В консоли MySQL выполните:

```sql
CREATE DATABASE studteams CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'studteams'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON studteams.* TO 'studteams'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**⚠️ Важно:** Замените `STRONG_PASSWORD_HERE` на надёжный пароль!

## 📦 Развёртывание приложения

### 1. Создание директории проекта

```bash
# Создаём директорию
sudo mkdir -p /srv/studteams
sudo chown $USER:$USER /srv/studteams
cd /srv/studteams
```

### 2. Клонирование репозитория

```bash
# Клонируем проект
git clone https://github.com/yourusername/studteams.git .

# Или через SSH
git clone git@github.com:yourusername/studteams.git .
```

### 3. Создание виртуального окружения

```bash
# Создаём venv с Python 3.14
python3.14 -m venv venv

# Активируем
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 4. Настройка конфигурации

```bash
# Создаём директорию для секретов
mkdir -p config

# Создаём файл с секретами
nano config/secrets.yaml
```

Добавьте в `config/secrets.yaml`:

```yaml
bot:
  token: "YOUR_BOT_TOKEN_HERE"
  username: "your_bot_username"

database:
  host: "localhost"
  port: 3306
  user: "studteams"
  password: "YOUR_DB_PASSWORD_HERE"
  database: "studteams"
```

**⚠️ Важно:** Замените значения на реальные!

```bash
# Устанавливаем правильные права доступа
chmod 600 config/secrets.yaml
```

### 5. Инициализация базы данных

```bash
# Импортируем схему БД
mysql -u studteams -p studteams < dbschema/mysql.sql

# Проверяем что таблицы созданы
mysql -u studteams -p studteams -e "SHOW TABLES;"
```

### 6. Проверка работоспособности

```bash
# Тестовый запуск бота
python3 bot.py

# Если всё работает, останавливаем (Ctrl+C)
```

## 🔐 Настройка systemd сервисов

### 1. Копирование systemd unit файлов

```bash
# Копируем сервисы
sudo cp config/studteams-bot.service /etc/systemd/system/
sudo cp config/studteams-web.service /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload
```

### 2. Проверка и правка путей

Убедитесь что пути в сервисах корректны:

```bash
sudo nano /etc/systemd/system/studteams-bot.service
```

Проверьте:
- `WorkingDirectory=/srv/studteams`
- `ExecStart=/srv/studteams/venv/bin/python3 /srv/studteams/bot.py`

### 3. Запуск сервисов

```bash
# Запускаем бота
sudo systemctl start studteams-bot
sudo systemctl enable studteams-bot

# Запускаем веб-сервер (если нужен)
sudo systemctl start studteams-web
sudo systemctl enable studteams-web

# Проверяем статус
sudo systemctl status studteams-bot
sudo systemctl status studteams-web
```

### 4. Просмотр логов

```bash
# Логи бота
sudo journalctl -u studteams-bot -f

# Логи веб-сервиса
sudo journalctl -u studteams-web -f

# Последние 100 строк
sudo journalctl -u studteams-bot -n 100
```

## 🌐 Настройка Nginx

### 1. Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/studteams
```

Добавьте базовую конфигурацию:

```nginx
server {
    listen 80;
    server_name studteams.example.com;

    # Корневая директория для статики
    root /srv/studteams/web/static;
    
    # ACME challenge для Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Проксирование на FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Ограничение размера загружаемых файлов
    client_max_body_size 10M;
}
```

**⚠️ Замените `studteams.example.com` на ваш реальный домен!**

### 2. Активация конфигурации

```bash
# Создаём символическую ссылку
sudo ln -s /etc/nginx/sites-available/studteams /etc/nginx/sites-enabled/

# Удаляем дефолтную конфигурацию (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверяем конфигурацию
sudo nginx -t

# Перезагружаем Nginx
sudo systemctl reload nginx
```

## 🔒 Настройка SSL (HTTPS)

### 1. Установка Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

Или через Makefile проекта:

```bash
make install-certbot
```

### 2. Получение SSL сертификата

```bash
# Автоматическая настройка
sudo certbot --nginx -d studteams.example.com

# Или через Makefile
make setup-ssl DOMAIN=studteams.example.com EMAIL=your@email.com
```

### 3. Проверка автообновления

```bash
# Тест обновления
sudo certbot renew --dry-run

# Или через Makefile
make test-ssl-renewal
```

Подробнее см. [config/SSL.md](config/SSL.md)

## 🔥 Настройка файрвола

### UFW (Ubuntu/Debian)

```bash
# Включаем UFW
sudo ufw enable

# Разрешаем SSH
sudo ufw allow ssh

# Разрешаем HTTP и HTTPS
sudo ufw allow 'Nginx Full'

# Проверяем статус
sudo ufw status
```

### Firewalld (CentOS/RHEL)

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 📊 Мониторинг и обслуживание

### Проверка состояния сервисов

```bash
# Статус всех сервисов
sudo systemctl status studteams-bot studteams-web nginx mysql

# Просмотр логов в реальном времени
sudo journalctl -u studteams-bot -f

# Использование ресурсов
htop
```

### Резервное копирование базы данных

Создайте скрипт `/srv/studteams/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/srv/studteams/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/studteams_$DATE.sql"

mkdir -p $BACKUP_DIR

# Создаём бэкап
mysqldump -u studteams -p'YOUR_DB_PASSWORD' studteams > $BACKUP_FILE

# Сжимаем
gzip $BACKUP_FILE

# Удаляем бэкапы старше 30 дней
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE.gz"
```

Сделайте его исполняемым и добавьте в cron:

```bash
chmod +x /srv/studteams/backup.sh

# Добавляем в crontab (ежедневно в 2:00)
(crontab -l 2>/dev/null; echo "0 2 * * * /srv/studteams/backup.sh") | crontab -
```

### Обновление приложения

```bash
cd /srv/studteams

# Получаем последние изменения
git pull

# Активируем venv
source venv/bin/activate

# Обновляем зависимости
pip install --upgrade -r requirements.txt

# Применяем миграции БД (если есть)
# mysql -u studteams -p studteams < dbschema/migrations/xxx.sql

# Перезапускаем сервисы
sudo systemctl restart studteams-bot
sudo systemctl restart studteams-web

# Проверяем статус
sudo systemctl status studteams-bot studteams-web
```

## 🐛 Troubleshooting

### Бот не запускается

```bash
# Проверяем логи
sudo journalctl -u studteams-bot -n 100

# Проверяем конфигурацию
cat config/secrets.yaml

# Проверяем подключение к БД
mysql -u studteams -p studteams -e "SELECT 1;"

# Тестируем бота вручную
cd /srv/studteams
source venv/bin/activate
python3 bot.py
```

### Nginx возвращает 502 Bad Gateway

```bash
# Проверяем что web-сервис запущен
sudo systemctl status studteams-web

# Проверяем логи nginx
sudo tail -f /var/log/nginx/error.log

# Проверяем что порт 8000 слушается
sudo netstat -tlnp | grep 8000
```

### SSL сертификат не обновляется

```bash
# Проверяем логи certbot
sudo journalctl -u certbot.timer

# Проверяем конфигурацию обновления
sudo cat /etc/letsencrypt/renewal/studteams.example.com.conf

# Тестируем обновление
sudo certbot renew --dry-run
```

### База данных не отвечает

```bash
# Проверяем статус MySQL
sudo systemctl status mysql

# Проверяем логи MySQL
sudo tail -f /var/log/mysql/error.log

# Перезапускаем MySQL
sudo systemctl restart mysql
```

## 📈 Оптимизация производительности

### MySQL

Настройте `/etc/mysql/mysql.conf.d/mysqld.cnf`:

```ini
[mysqld]
max_connections = 100
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
query_cache_size = 0
query_cache_type = 0
```

### Nginx

Добавьте кэширование в конфигурацию nginx:

```nginx
# В блоке http
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m inactive=60m;
proxy_cache_key "$scheme$request_method$host$request_uri";

# В блоке location /
proxy_cache my_cache;
proxy_cache_valid 200 60m;
proxy_cache_bypass $http_cache_control;
add_header X-Cache-Status $upstream_cache_status;
```

## 🔐 Безопасность

### Рекомендации

1. ✅ Используйте HTTPS (SSL сертификат)
2. ✅ Храните секреты в `config/secrets.yaml` с правами 600
3. ✅ Регулярно обновляйте систему: `sudo apt update && sudo apt upgrade`
4. ✅ Настройте автоматические бэкапы БД
5. ✅ Используйте сильные пароли для БД
6. ✅ Ограничьте доступ к серверу через SSH (только по ключу)
7. ✅ Настройте fail2ban для защиты от brute-force атак
8. ✅ Регулярно проверяйте логи на подозрительную активность

### Дополнительная защита

```bash
# Установка fail2ban
sudo apt install -y fail2ban

# Настройка SSH (только ключи)
sudo nano /etc/ssh/sshd_config
# Установите: PasswordAuthentication no
sudo systemctl restart sshd
```

## 📞 Поддержка

### Полезные ссылки

- [README.md](README.md) - Общая информация о проекте
- [config/SSL.md](config/SSL.md) - Подробная настройка SSL
- [bot-setup.md](bot-setup.md) - Настройка и функции бота

### Команды для быстрого доступа

```bash
# Статус всех сервисов
make status  # (если добавить в Makefile)

# Логи бота
sudo journalctl -u studteams-bot -f

# Логи веб-сервиса
sudo journalctl -u studteams-web -f

# Перезапуск всех сервисов
sudo systemctl restart studteams-bot studteams-web nginx
```

---

**✨ Готово!** Ваш проект StudTeams развёрнут и работает на production сервере!

Не забудьте протестировать бота через Telegram и веб-интерфейс через браузер.
