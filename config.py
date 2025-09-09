"""
Модуль конфигурации StudHelper Bot.

Содержит настройки бота, параметры базы данных и логирования.
"""

# StudHelper Bot Configuration

BOT_TOKEN = "8307678596:AAEeJm_M1rV4yMU6rRT4W7lqQPqLnwfRogo" # noqa S105
# EdgeDB DSN для локальной разработки (без аутентификации, с отключенным SSL)
EDGEDB_DSN= None # "edgedb://localhost:10701/studteams?tls_security=insecure"

# Features
ENABLE_REVIEWS = True
MAX_SPRINT_NUMBER = 6
MIN_RATING = 1
MAX_RATING = 10

# Logging
LOG_FILE = "logs/studhelper-bot.log"
LOG_LEVEL = "INFO"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "1 month"
