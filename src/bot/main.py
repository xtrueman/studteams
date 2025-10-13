#!/usr/bin/env python3
"""
Главный файл запуска StudHelper Bot.

Telegram-бот для отслеживания прогресса студенческих команд
и управления проектами по методологии Scrum.
"""

import signal
import sys

import loguru
import telebot

import myconn
from bot import bot_instance
from bot.handlers import admin as admin_handlers
from bot.handlers import callbacks as callback_handlers
from bot.handlers import reports as reports_handlers
from bot.handlers import reviews as reviews_handlers
from bot.handlers import start as start_handlers
from bot.handlers import team as team_handlers
from bot.middlewares import logging as logging_middleware
from config import config

# Настройка логирования с loguru
loguru.logger.add(
    config.logging.file,
    rotation=config.logging.rotation,
    retention=config.logging.retention,
    level=config.logging.level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
)

logger = loguru.logger

# Проверяем конфигурацию
if not config.bot.token:
    logger.error("BOT_TOKEN not set in config.py")
    exit(1)

# Создаем бота
bot = telebot.TeleBot(config.bot.token)
bot_instance.set_bot_instance(bot)

# Применяем middleware для логирования
logging_middleware.setup_logging_middleware(bot)

# Регистрируем обработчики
start_handlers.register_start_handlers(bot)
team_handlers.register_team_handlers(bot)
reports_handlers.register_reports_handlers(bot)
reviews_handlers.register_reviews_handlers(bot)
admin_handlers.register_admin_handlers(bot)
callback_handlers.register_callback_handlers(bot)


def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown."""
    logger.info(f"Received signal {sig}. Shutting down gracefully...")
    try:
        # Закрываем соединение с БД
        myconn.close_connection()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")
    finally:
        logger.info("Bot stopped")
        sys.exit(0)


# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

logger.info("StudHelper Bot starting...")

try:
    # Удаляем webhook если он активен
    bot.remove_webhook()
    logger.info("Webhook deleted (if it was active)")

    # Запускаем polling
    logger.info("Bot is running. Press Ctrl+C to stop.")
    bot.infinity_polling()
except KeyboardInterrupt:
    logger.info("Bot stopped by user (Ctrl+C)")
    signal_handler(signal.SIGINT, None)
except Exception as e:
    logger.error(f"Bot startup error: {e}")
    raise
