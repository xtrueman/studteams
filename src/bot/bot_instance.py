"""
Глобальный экземпляр бота.

Этот модуль содержит глобальный экземпляр бота, который используется во всех handlers.
"""

import telebot

# Глобальный экземпляр бота (будет инициализирован в main.py)
bot: telebot.TeleBot | None = None


def set_bot_instance(bot_instance: telebot.TeleBot):
    """Установить глобальный экземпляр бота"""
    global bot
    bot = bot_instance
