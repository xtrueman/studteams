# Настройка systemd сервисов

Этот документ описывает установку и настройку systemd сервисов для автоматического запуска Telegram бота и веб-сервиса StudTeams.

## Установка

### 1. Копирование файлов сервисов

Скопируйте файлы сервисов в системную директорию:

```bash
sudo cp /srv/studteams/config/studteams-bot.service /etc/systemd/system/
sudo cp /srv/studteams/config/studteams-web.service /etc/systemd/system/
```

### 2. Перезагрузка конфигурации systemd

После копирования файлов необходимо перезагрузить конфигурацию systemd:

```bash
sudo systemctl daemon-reload
```

### 3. Включение автозапуска

Включите автозапуск сервисов при загрузке системы:

```bash
sudo systemctl enable studteams-bot
sudo systemctl enable studteams-web
```

### 4. Запуск сервисов

Запустите сервисы:

```bash
sudo systemctl start studteams-bot
sudo systemctl start studteams-web
```

## Управление сервисами

### Проверка статуса

```bash
# Статус бота
sudo systemctl status studteams-bot

# Статус веб-сервиса
sudo systemctl status studteams-web
```

### Остановка сервисов

```bash
sudo systemctl stop studteams-bot
sudo systemctl stop studteams-web
```

### Перезапуск сервисов

```bash
sudo systemctl restart studteams-bot
sudo systemctl restart studteams-web
```

### Отключение автозапуска

```bash
sudo systemctl disable studteams-bot
sudo systemctl disable studteams-web
```

## Просмотр логов

### Логи бота

```bash
# Последние записи
sudo journalctl -u studteams-bot -n 50

# Логи в реальном времени
sudo journalctl -u studteams-bot -f

# Логи за сегодня
sudo journalctl -u studteams-bot --since today
```

### Логи веб-сервиса

```bash
# Последние записи
sudo journalctl -u studteams-web -n 50

# Логи в реальном времени
sudo journalctl -u studteams-web -f

# Логи за сегодня
sudo journalctl -u studteams-web --since today
```

## Структура сервисов

### studteams-bot.service

- **Описание**: Telegram бот StudTeams
- **Рабочая директория**: `/srv/studteams`
- **Исполняемый файл**: `/srv/studteams/bot.py`
- **Пользователь**: `www-data`
- **Автоперезапуск**: Да (при падении)

### studteams-web.service

- **Описание**: Веб-интерфейс StudTeams
- **Рабочая директория**: `/srv/studteams`
- **Исполняемый файл**: `/srv/studteams/web_server.py`
- **Пользователь**: `www-data`
- **Автоперезапуск**: Да (при падении)

## Зависимости

Оба сервиса зависят от:
- `network.target` - сеть должна быть доступна
- `mysql.service` - MySQL должен быть запущен

Сервисы автоматически запускаются после запуска MySQL.

## Безопасность

В конфигурации сервисов включены следующие меры безопасности:
- `NoNewPrivileges=true` - запрет повышения привилегий
- `PrivateTmp=true` - изолированная временная директория

## Обновление после изменений кода

После обновления кода проекта необходимо перезапустить сервисы:

```bash
cd /srv/studteams
git pull
sudo systemctl restart studteams-bot
sudo systemctl restart studteams-web
```

## Проверка работоспособности

### Быстрая проверка

```bash
# Проверяем, что оба сервиса запущены
sudo systemctl is-active studteams-bot studteams-web

# Должно вывести:
# active
# active
```

### Детальная проверка

```bash
# Проверяем статус обоих сервисов
sudo systemctl status studteams-bot studteams-web

# Смотрим последние логи
sudo journalctl -u studteams-bot -u studteams-web -n 20
```

## Troubleshooting

### Сервис не запускается

1. Проверьте логи:
   ```bash
   sudo journalctl -u studteams-bot -n 100
   ```

2. Проверьте права на файлы:
   ```bash
   ls -la /srv/studteams/bot.py
   ls -la /srv/studteams/web_server.py
   ```

3. Проверьте virtualenv:
   ```bash
   /srv/studteams/venv/bin/python3 --version
   ```

### Сервис падает сразу после запуска

1. Проверьте конфигурацию в `config/secrets.yaml`
2. Проверьте подключение к MySQL
3. Проверьте логи приложения

### Изменение пользователя

Если нужно запускать сервисы от другого пользователя (не `www-data`), измените параметры `User` и `Group` в файлах сервисов и выполните:

```bash
sudo systemctl daemon-reload
sudo systemctl restart studteams-bot studteams-web
```
