# Запуск StudHelper Bot

## 📋 Требования

- Python 3.11+
- MySQL 8.0+
- Telegram Bot Token

## 🚀 Установка и настройка

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка MySQL
```bash
# Создайте базу данных согласно схеме в dbschema/mysql.sql
# Импортируйте схему в вашу MySQL базу данных
```

### 3. Конфигурация
```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте config.py или .env файл
# Укажите ваш BOT_TOKEN от @BotFather и параметры MySQL
```

### 4. Запуск бота
```bash
python studhelper-bot.py
```

## ⚙️ Конфигурация

### В config.py:
```python
BOT_TOKEN = "your_bot_token_here"
MYSQL_HOST = "localhost"
MYSQL_USER = "your_mysql_user"
MYSQL_PASS = "your_mysql_password"
MYSQL_BDNAME = "studteams"
ENABLE_REVIEWS = True  # Включить/выключить систему оценок
MAX_SPRINT_NUMBER = 6
```

### Альтернативно через .env:
```bash
BOT_TOKEN=your_bot_token_here
MYSQL_HOST=localhost
MYSQL_USER=your_mysql_user
MYSQL_PASS=your_mysql_password
MYSQL_BDNAME=studteams
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
├── db.py             # MySQL интеграция
└── utils/           # Вспомогательные функции
```

### Логи:
Логи выводятся в консоль с уровнем INFO.

## 🐛 Отладка

### Проверка MySQL:
```bash
mysql -u your_mysql_user -p studteams  # Подключиться к БД через CLI
```

### Тестовые запросы:
```sql
SELECT * FROM students;
SELECT * FROM teams;
SELECT * FROM team_members;
```