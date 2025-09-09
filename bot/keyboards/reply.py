"""
Модуль reply-клавиатур для Telegram бота.

Создает клавиатуры основного меню и навигации по боту.
"""

import aiogram.types
import config


def get_main_menu_keyboard(is_admin: bool = False, has_team: bool = False):
    """Создает основную клавиатуру в зависимости от статуса пользователя"""
    keyboard = aiogram.types.ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    if not has_team:
        # Незарегистрированные пользователи
        keyboard.keyboard.append([
            aiogram.types.KeyboardButton(text="Регистрация команды"),
            aiogram.types.KeyboardButton(text="Помощь")
        ])
    else:
        # Участники команды
        row1 = [aiogram.types.KeyboardButton(text="Моя команда")]

        # Добавляем кнопку "Отчёт о команде" справа от "Моя команда" для админов при включенных отзывах
        if is_admin and config.ENABLE_REVIEWS:
            row1.append(aiogram.types.KeyboardButton(text="Отчёт о команде"))

        row2 = [
            aiogram.types.KeyboardButton(text="Мои отчёты"),
            aiogram.types.KeyboardButton(text="Отправить отчёт")
        ]

        if config.ENABLE_REVIEWS:
            row4 = [
                aiogram.types.KeyboardButton(text="Оценить участников команды"),
                aiogram.types.KeyboardButton(text="Кто меня оценил?")
            ]
            keyboard.keyboard.append(row4)

        keyboard.keyboard.extend([row1, row2])

        # Последняя строка - служебные кнопки
        last_row = [
            aiogram.types.KeyboardButton(text="Помощь"),
            aiogram.types.KeyboardButton(text="Обновить")
        ]
        keyboard.keyboard.append(last_row)

    return keyboard


def get_confirmation_keyboard(confirm_text: str = "Продолжить", cancel_text: str = "Отмена"):
    """Клавиатура подтверждения"""
    return aiogram.types.ReplyKeyboardMarkup(
        keyboard=[
            [
                aiogram.types.KeyboardButton(text=confirm_text),
                aiogram.types.KeyboardButton(text=cancel_text)
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_roles_keyboard():
    """Клавиатура выбора роли"""
    roles = ["Product owner", "Scrum Master", "Разработчик", "Участник команды"]
    keyboard = aiogram.types.ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    for i in range(0, len(roles), 2):
        row = [aiogram.types.KeyboardButton(text=roles[i])]
        if i + 1 < len(roles):
            row.append(aiogram.types.KeyboardButton(text=roles[i + 1]))
        keyboard.keyboard.append(row)

    keyboard.keyboard.append([aiogram.types.KeyboardButton(text="Отмена")])
    return keyboard


def get_sprints_keyboard():
    """Клавиатура выбора спринта"""
    keyboard = aiogram.types.ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    sprints = [f"Спринт №{i}" for i in range(1, config.MAX_SPRINT_NUMBER + 1)]

    for i in range(0, len(sprints), 3):
        row = []
        for j in range(3):
            if i + j < len(sprints):
                row.append(aiogram.types.KeyboardButton(text=sprints[i + j]))
        keyboard.keyboard.append(row)

    keyboard.keyboard.append([aiogram.types.KeyboardButton(text="Отмена")])
    return keyboard


def get_ratings_keyboard():
    """Клавиатура выбора оценки"""
    keyboard = aiogram.types.ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    # Первая строка: 1-5
    row1 = [aiogram.types.KeyboardButton(text=str(i)) for i in range(config.MIN_RATING, 6)]
    # Вторая строка: 6-10
    row2 = [aiogram.types.KeyboardButton(text=str(i)) for i in range(6, config.MAX_RATING + 1)]

    keyboard.keyboard.extend([row1, row2])
    keyboard.keyboard.append([aiogram.types.KeyboardButton(text="Отмена")])
    return keyboard


def get_dynamic_keyboard(items: list[str], columns: int = 2):
    """Динамическая клавиатура для списков (участники, отчеты и т.д.)"""
    keyboard = aiogram.types.ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    for i in range(0, len(items), columns):
        row = []
        for j in range(columns):
            if i + j < len(items):
                row.append(aiogram.types.KeyboardButton(text=items[i + j]))
        keyboard.keyboard.append(row)

    keyboard.keyboard.append([aiogram.types.KeyboardButton(text="Отмена")])
    return keyboard
