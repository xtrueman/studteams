"""
Middleware для логирования в боте.

Логирует входящие сообщения и callback-запросы от пользователей.
"""

import loguru
import telebot

logger = loguru.logger


def setup_logging_middleware(bot: telebot.TeleBot):
    """Настройка middleware для логирования"""

    @bot.middleware_handler(update_types=['message'])
    def log_message(bot_instance, message):
        user_id = message.from_user.id
        username = message.from_user.username or "None"
        text = message.text or "[Non-text message]"
        logger.info(f"Message from user_id={user_id} username=@{username} text='{text}'")

    @bot.middleware_handler(update_types=['callback_query'])
    def log_callback(bot_instance, call):
        user_id = call.from_user.id
        username = call.from_user.username or "None"
        data_text = call.data or "None"
        logger.info(f"Callback from user_id={user_id} username=@{username} data='{data_text}'")
