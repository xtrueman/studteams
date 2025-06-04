# Запуск StudHelper Bot

## 📋 Требования

- Python 3.11+
- EdgeDB 5.0+
- Telegram Bot Token

## 🚀 Установка и настройка

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка EdgeDB
```bash
# Следуйте инструкциям в gel-setup.md
gel project init
gel migrate
```

### 3. Конфигурация
```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте config.py или .env файл
# Укажите ваш BOT_TOKEN от @BotFather
```

### 4. Запуск бота
```bash
python studhelper-bot.py
```

## ⚙️ Конфигурация

### В config.py:
```python
BOT_TOKEN = "your_bot_token_here"
EDGEDB_DSN = "edgedb://localhost:5656/studteams"
ENABLE_REVIEWS = True  # Включить/выключить систему оценок
MAX_SPRINT_NUMBER = 6
```

### Альтернативно через .env:
```bash
BOT_TOKEN=your_bot_token_here
EDGEDB_DSN=edgedb://localhost:5656/studteams
ENABLE_REVIEWS=true
```

## 📱 Функции бота

### Для всех пользователей:
- 🔄 `/start` - начало работы
- 📖 `Помощь` - справочная информация
- 🔄 `Обновить` - обновление меню

### Для Scrum Master:
- 👥 `Регистрация команды` - создание новой команды
- 🔗 `Ссылка-приглашение` - генерация ссылок для участников
- 🗑 `Удалить участника` - исключение из команды
- 📊 `Отчёт о команде` - статистика команды

### Для участников команды:
- 👥 `Моя команда` - информация о команде
- 📝 `Мои отчёты` - просмотр отчетов
- 📤 `Отправить отчёт` - создание отчета по спринту
- 🗑 `Удалить отчёт` - удаление отчета

### Система оценивания (если ENABLE_REVIEWS=true):
- ⭐ `Оценить участников команды` - peer-to-peer оценивание
- 👀 `Кто меня оценил?` - просмотр полученных оценок

## 🔧 Разработка

### Структура проекта:
```
studhelper-bot.py       # Главный файл
config.py              # Конфигурация
bot/
├── handlers/          # Обработчики команд
├── states/           # FSM состояния
├── keyboards/        # Telegram клавиатуры
├── database/         # EdgeDB интеграция
└── utils/           # Вспомогательные функции
```

### Логи:
Логи выводятся в консоль с уровнем INFO.

## 🐛 Отладка

### Проверка EdgeDB:
```bash
gel ui  # Открыть веб-интерфейс EdgeDB
gel     # Подключиться к БД через CLI
```

### Тестовые запросы:
```edgeql
SELECT Student { name, tg_id };
SELECT Team { team_name, admin: { name } };
```