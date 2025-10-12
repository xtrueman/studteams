"""
Модуль inline-клавиатур для Telegram бота.

Создает различные типы inline-клавиатур для взаимодействия с пользователем.
"""

import telebot.types
from config import config


def get_confirmation_inline_keyboard(
    confirm_text: str = "Продолжить",
    cancel_text: str = "Отмена",
    confirm_data: str = "confirm",
    cancel_data: str = "cancel",
):
    """Inline клавиатура подтверждения"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton(text=confirm_text, callback_data=confirm_data),
        telebot.types.InlineKeyboardButton(text=cancel_text, callback_data=cancel_data),
    )
    return markup


def get_roles_inline_keyboard():
    """Inline клавиатура выбора роли"""
    roles = [
        ("📈 Product owner", "role_po"),
        ("🎯 Scrum Master", "role_sm"),
        ("💻 Разработчик", "role_dev"),
        ("👥 Участник команды", "role_member"),
    ]

    markup = telebot.types.InlineKeyboardMarkup()
    for i in range(0, len(roles), 2):
        buttons = [telebot.types.InlineKeyboardButton(text=roles[i][0], callback_data=roles[i][1])]
        if i + 1 < len(roles):
            buttons.append(telebot.types.InlineKeyboardButton(text=roles[i + 1][0], callback_data=roles[i + 1][1]))
        markup.row(*buttons)

    markup.row(telebot.types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return markup


def get_sprints_inline_keyboard():
    """Иnline клавиатура выбора спринта"""
    markup = telebot.types.InlineKeyboardMarkup()
    sprints = [f"Спринт №{i}" for i in range(1, config.features.max_sprint_number + 1)]

    for i in range(0, len(sprints), 3):
        buttons = []
        for j in range(3):
            if i + j < len(sprints):
                sprint_num = i + j + 1
                buttons.append(
                    telebot.types.InlineKeyboardButton(
                        text=sprints[i + j],
                        callback_data=f"sprint_{sprint_num}",
                    )
                )
        if buttons:
            markup.row(*buttons)

    markup.row(telebot.types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return markup


def get_ratings_inline_keyboard():
    """Иnline клавиатура выбора оценки"""
    markup = telebot.types.InlineKeyboardMarkup()

    # Первая строка: 1-5
    row1 = []
    for i in range(config.features.min_rating, 6):
        row1.append(telebot.types.InlineKeyboardButton(text=f"⭐ {i}", callback_data=f"rating_{i}"))

    # Вторая строка: 6-10
    row2 = []
    for i in range(6, config.features.max_rating + 1):
        row2.append(telebot.types.InlineKeyboardButton(text=f"⭐ {i}", callback_data=f"rating_{i}"))

    markup.row(*row1)
    markup.row(*row2)
    return markup


def get_dynamic_inline_keyboard(items: list[str], callback_prefix: str, columns: int = 2):
    """Динамическая inline клавиатура для списков (участники, отчеты и т.д.)"""
    markup = telebot.types.InlineKeyboardMarkup()

    for i in range(0, len(items), columns):
        buttons = []
        for j in range(columns):
            if i + j < len(items):
                item_index = i + j
                # Обрезаем длинные элементы для лучшей читаемости
                item_text = items[item_index]
                if len(item_text) > 20:
                    item_text = item_text[:17] + "..."

                buttons.append(
                    telebot.types.InlineKeyboardButton(
                        text=item_text,
                        callback_data=f"{callback_prefix}_{item_index}",
                    )
                )
        if buttons:
            markup.row(*buttons)

    markup.row(telebot.types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return markup


# Удалено: get_skip_cancel_inline_keyboard - больше не используется

# Специфичные клавиатуры для различных действий


def get_team_registration_confirm_keyboard():
    """Клавиатура подтверждения регистрации команды"""
    return get_confirmation_inline_keyboard(
        "✅ Продолжить",
        "❌ Отмена",
        "confirm_team_reg",
        cancel_data="cancel_team_reg",
    )


def get_join_team_confirm_keyboard():
    """Клавиатура подтверждения присоединения к команде"""
    return get_confirmation_inline_keyboard("✅ Присоединиться", "❌ Отмена", "confirm_join_team", "cancel_join_team")


def get_report_confirm_keyboard():
    """Клавиатура подтверждения отправки отчета"""
    return get_confirmation_inline_keyboard("📤 Отправить", "❌ Отмена", "confirm_report", "cancel_report")


def get_report_delete_confirm_keyboard():
    """Клавиатура подтверждения удаления отчета"""
    return get_confirmation_inline_keyboard("🗑️ Удалить", "❌ Отмена", "confirm_delete_report", "cancel_delete_report")


def get_member_removal_confirm_keyboard():
    """Клавиатура подтверждения удаления участника"""
    return get_confirmation_inline_keyboard("⚠️ Удалить", "❌ Отмена", "confirm_remove_member", "cancel_remove_member")


def get_review_confirm_keyboard():
    """Клавиатура подтверждения отправки оценки"""
    return get_confirmation_inline_keyboard("⭐ Отправить", "❌ Отмена", "confirm_review", "cancel_review")


def get_team_member_management_keyboard(members, current_user_id, is_admin=False):
    """Клавиатура управления участниками команды"""
    markup = telebot.types.InlineKeyboardMarkup()

    if is_admin and len(members) > 1:  # Можно удалять только если есть кого удалять
        # Кнопки для каждого участника (кроме самого админа)
        for member in members:
            # Direct dictionary access
            member_id = member.get('student_id')
            member_name = member.get('name')

            # Skip if this is the current user
            if member_id == current_user_id:
                continue

            if member_id and member_name:
                # Обрезаем длинные имена для лучшей читаемости
                name = member_name
                if len(name) > 15:
                    name = name[:12] + "..."

                markup.row(
                    telebot.types.InlineKeyboardButton(
                        text=f"✏️ {name}",
                        callback_data=f"edit_member_{member_id}",
                    ),
                    telebot.types.InlineKeyboardButton(
                        text="🗑️ Удалить",
                        callback_data=f"remove_member_{member_id}",
                    ),
                )

    return markup


def get_report_management_keyboard(reports):
    """Клавиатура управления отчетами"""
    markup = telebot.types.InlineKeyboardMarkup()

    if reports:
        # Кнопки для каждого отчета
        for report in reports:
            # Обрезаем длинный текст отчета для отображения
            preview_text = report['report_text'][:30] if len(report['report_text']) > 30 else report['report_text']
            if len(report['report_text']) > 30:
                preview_text += "..."

            sprint_text = f"Спринт №{report['sprint_num']}"

            markup.row(
                telebot.types.InlineKeyboardButton(
                    text=f"✏️ {sprint_text}",
                    callback_data=f"edit_report_{report['sprint_num']}",
                ),
                telebot.types.InlineKeyboardButton(
                    text="🗑️ Удалить",
                    callback_data=f"delete_report_{report['sprint_num']}",
                ),
            )

    return markup
