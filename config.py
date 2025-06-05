# StudHelper Bot Configuration

BOT_TOKEN = "5102428240:AAEkizPNNjnJna97FNYRApvjhPvEsExWePs"
EDGEDB_DSN = "edgedb://localhost:10701/studteams"

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

# Messages
HELP_MESSAGE = """
🤖 *StudHelper Bot* - помощник для студенческих команд

*Основные функции:*
• Регистрация команды и управление участниками  
• Отправка отчётов по спринтам
• Взаимное оценивание участников команды
• Просмотр статистики команды

*Для начала работы:*
1. Scrum Master регистрирует команду
2. Рассылает ссылку-приглашение участникам
3. Участники отчитываются о проделанной работе после каждого спринта

*Команды:*
/start - начать работу с ботом
/help - показать эту справку

*Поддержка:* @studhelper_support
"""

WELCOME_MESSAGE = "👋 Добро пожаловать в StudHelper!\n\nВыберите действие из меню:"
