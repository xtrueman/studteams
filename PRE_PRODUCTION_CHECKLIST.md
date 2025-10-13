# Pre-Production Checklist для StudTeams

## ✅ Выполнено

### Код и качество
- [x] Все тесты проходят (28/28)
- [x] Flake8 чистый
- [x] Ruff чистый
- [x] Нет хардкоженных секретов в коде
- [x] SQL-запросы параметризованы (защита от SQL-инъекций)
- [x] Настроено логирование через loguru
- [x] Структура проекта чистая (src/bot, src/web)

### База данных
- [x] Используется connection pooling через myconn
- [x] Autocommit включен
- [x] Параметризованные запросы
- [x] Тестовая и prod БД разделены

### Конфигурация
- [x] Секреты вынесены в secrets.yaml (не в git)
- [x] Разделение prod/test окружений
- [x] Настройки логирования

## 🔧 Рекомендуется доделать

### Высокий приоритет

1. **Завершить TODO в callbacks.py**
   ```python
   # TODO: Implement member editing functionality
   ```
   Решение: Либо реализовать, либо убрать кнопку редактирования

2. **Добавить health-check endpoint для веб-сервера**
   ```python
   # src/web/app.py
   @app.get("/health")
   async def health_check():
       return {"status": "healthy", "version": "1.0.0"}
   ```

3. **Настроить graceful shutdown**
   - Добавить обработку сигналов SIGTERM/SIGINT
   - Корректное закрытие БД соединений

4. **Добавить rate limiting для бота**
   - Защита от спама
   - Ограничение запросов на пользователя

### Средний приоритет

5. **Улучшить обработку ошибок БД**
   ```python
   # Добавить retry логику для временных сбоев
   # Логировать ошибки БД в отдельный файл
   ```

6. **Добавить метрики**
   - Количество активных пользователей
   - Время отклика БД
   - Количество ошибок

7. **Создать systemd service файлы**
   ```ini
   [Unit]
   Description=StudTeams Bot
   After=network.target mysql.service

   [Service]
   Type=simple
   User=studteams
   WorkingDirectory=/path/to/studteams
   Environment="PYTHONPATH=/path/to/studteams/src"
   ExecStart=/usr/bin/python3 /path/to/studteams/src/bot/main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

8. **Настроить логирование в production**
   - Отдельные файлы для errors
   - Ротация логов
   - Централизованное хранение (опционально)

### Низкий приоритет

9. **Добавить мониторинг**
   - Prometheus metrics endpoint
   - Grafana dashboard
   - Alertmanager для критических ошибок

10. **Оптимизация БД**
    - Проверить индексы на часто запрашиваемых полях
    - EXPLAIN для медленных запросов
    - Добавить кэширование для редко меняющихся данных

11. **Документация**
    - Добавить примеры конфигурации
    - Документировать API endpoints
    - Создать troubleshooting guide

12. **Backup стратегия**
    - Автоматический backup БД
    - Backup конфигурации
    - План восстановления

## 🚀 Минимальный production checklist

Перед запуском ОБЯЗАТЕЛЬНО:

1. ✅ Создать production secrets.yaml
2. ✅ Настроить БД (создать базу, пользователя, таблицы)
3. ✅ Настроить права доступа к файлам
4. ✅ Проверить, что все зависимости установлены
5. ✅ Запустить тесты в production окружении
6. ✅ Настроить автозапуск (systemd/supervisor)
7. ✅ Настроить мониторинг доступности
8. ✅ Подготовить процедуру rollback

## 📝 Заметки

### Текущая версия БД библиотеки
- mysql-connector-python 8.3.0 (совместима с MySQL 8.4+)
- НЕ обновлять до 9.x без тестирования!

### Логи
- Расположение: `logs/studteams.log`
- Ротация: 10 MB
- Хранение: 1 месяц

### Порты
- Web: 8000 (настраивается в run_web.py)
- MySQL: 3306 (по умолчанию)

## 🔒 Безопасность

### Уже реализовано
- Секреты не в git
- SQL инъекции защищены (параметризованные запросы)
- Валидация входных данных в helpers.py

### Рекомендуется
- Настроить firewall (только нужные порты)
- HTTPS для веб-интерфейса (nginx reverse proxy)
- Регулярные обновления зависимостей
- Мониторинг попыток атак
