"""
Модуль reply-клавиатур для Telegram бота.

Создает клавиатуры основного меню и навигации по боту.
"""

import telebot.types
from config import config


def get_main_menu_keyboard(is_admin: bool = False, has_team: bool = False):
    """Создает основную клавиатуру в зависимости от статуса пользователя"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    if not has_team:
        # Незарегистрированные пользователи
        markup.row(
            telebot.types.KeyboardButton(text="Регистрация команды"),
            telebot.types.KeyboardButton(text="Помощь"),
        )
    else:
        # Участники команды
        buttons_row1 = [telebot.types.KeyboardButton(text="Моя команда")]

        # Добавляем кнопку "Отчёт о команде" справа от "Моя команда" для всех участников при включенных отзывах
        if config.features.enable_reviews:
            buttons_row1.append(telebot.types.KeyboardButton(text="📊 Отчёт о команде"))

        if config.features.enable_reviews:
            markup.row(
                telebot.types.KeyboardButton(text="Оценить участников команды"),
                telebot.types.KeyboardButton(text="Кто меня оценил?"),
            )

        markup.row(*buttons_row1)
        markup.row(
            telebot.types.KeyboardButton(text="Мои отчеты"),
            telebot.types.KeyboardButton(text="Отправить отчет"),
        )

        # Последняя строка - служебные кнопки
        markup.row(
            telebot.types.KeyboardButton(text="Помощь"),
            telebot.types.KeyboardButton(text="Обновить"),
        )

    return markup


def get_confirmation_keyboard(confirm_text: str = "Продолжить", cancel_text: str = "Отмена"):
    """Клавиатура подтверждения"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(
        telebot.types.KeyboardButton(text=confirm_text),
        telebot.types.KeyboardButton(text=cancel_text),
    )
    return markup


def get_roles_keyboard():
    """Клавиатура выбора роли"""
    roles = ["Product owner", "Scrum Master", "Разработчик", "Участник команды"]
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for i in range(0, len(roles), 2):
        buttons = [telebot.types.KeyboardButton(text=roles[i])]
        if i + 1 < len(roles):
            buttons.append(telebot.types.KeyboardButton(text=roles[i + 1]))
        markup.row(*buttons)

    markup.row(telebot.types.KeyboardButton(text="Отмена"))
    return markup


def get_sprints_keyboard():
    """Клавиатура выбора спринта"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    sprints = [f"Спринт №{i}" for i in range(1, config.features.max_sprint_number + 1)]

    for i in range(0, len(sprints), 3):
        buttons = []
        for j in range(3):
            if i + j < len(sprints):
                buttons.append(telebot.types.KeyboardButton(text=sprints[i + j]))
        if buttons:
            markup.row(*buttons)

    markup.row(telebot.types.KeyboardButton(text="Отмена"))
    return markup


def get_ratings_keyboard():
    """Клавиатура выбора оценки"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    # Первая строка: 1-5
    row1 = [telebot.types.KeyboardButton(text=str(i)) for i in range(config.features.min_rating, 6)]
    # Вторая строка: 6-10
    row2 = [
        telebot.types.KeyboardButton(text=str(i))
        for i in range(6, config.features.max_rating + 1)
    ]

    markup.row(*row1)
    markup.row(*row2)
    markup.row(telebot.types.KeyboardButton(text="Отмена"))
    return markup


def get_dynamic_keyboard(items: list[str], columns: int = 2):
    """Динамическая клавиатура для списков (участники, отчеты и т.д.)"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for i in range(0, len(items), columns):
        buttons = []
        for j in range(columns):
            if i + j < len(items):
                buttons.append(telebot.types.KeyboardButton(text=items[i + j]))
        if buttons:
            markup.row(*buttons)

    markup.row(telebot.types.KeyboardButton(text="Отмена"))
    return markup


def get_admin_panel_keyboard():
    """Клавиатура панели администратора"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        telebot.types.KeyboardButton(text="👥 Участники команды"),
        telebot.types.KeyboardButton(text="📊 Статистика участника"),
    )
    markup.row(telebot.types.KeyboardButton(text="Назад"))
    return markup
