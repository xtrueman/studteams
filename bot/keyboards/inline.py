"""
Модуль inline-клавиатур для Telegram бота.

Создает различные типы inline-клавиатур для взаимодействия с пользователем.
"""

import aiogram.types
import config

def get_confirmation_inline_keyboard(confirm_text: str = "Продолжить", cancel_text: str = "Отмена", confirm_data: str = "confirm", cancel_data: str = "cancel"):
    """Inline клавиатура подтверждения"""
    return aiogram.types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                aiogram.types.InlineKeyboardButton(text=confirm_text, callback_data=confirm_data),
                aiogram.types.InlineKeyboardButton(text=cancel_text, callback_data=cancel_data)
            ]
        ]
    )

def get_roles_inline_keyboard():
    """Inline клавиатура выбора роли"""
    roles = [
        ("📈 Product owner", "role_po"),
        ("🎯 Scrum Master", "role_sm"), 
        ("💻 Разработчик", "role_dev"),
        ("👥 Участник команды", "role_member")
    ]
    
    keyboard = []
    for i in range(0, len(roles), 2):
        row = [aiogram.types.InlineKeyboardButton(text=roles[i][0], callback_data=roles[i][1])]
        if i + 1 < len(roles):
            row.append(aiogram.types.InlineKeyboardButton(text=roles[i + 1][0], callback_data=roles[i + 1][1]))
        keyboard.append(row)
    
    keyboard.append([aiogram.types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    return aiogram.types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_sprints_inline_keyboard():
    """Inline клавиатура выбора спринта"""
    keyboard = []
    sprints = [f"Спринт №{i}" for i in range(1, config.MAX_SPRINT_NUMBER + 1)]
    
    for i in range(0, len(sprints), 3):
        row = []
        for j in range(3):
            if i + j < len(sprints):
                sprint_num = i + j + 1
                row.append(aiogram.types.InlineKeyboardButton(
                    text=sprints[i + j], 
                    callback_data=f"sprint_{sprint_num}"
                ))
        keyboard.append(row)
    
    keyboard.append([aiogram.types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return aiogram.types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ratings_inline_keyboard():
    """Inline клавиатура выбора оценки"""
    keyboard = []
    
    # Первая строка: 1-5
    row1 = []
    for i in range(config.MIN_RATING, 6):
        row1.append(aiogram.types.InlineKeyboardButton(text=f"⭐ {i}", callback_data=f"rating_{i}"))
    keyboard.append(row1)
    
    # Вторая строка: 6-10
    row2 = []
    for i in range(6, config.MAX_RATING + 1):
        row2.append(aiogram.types.InlineKeyboardButton(text=f"⭐ {i}", callback_data=f"rating_{i}"))
    keyboard.append(row2)
    
    keyboard.append([aiogram.types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return aiogram.types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_dynamic_inline_keyboard(items: list[str], callback_prefix: str, columns: int = 2):
    """Динамическая inline клавиатура для списков (участники, отчеты и т.д.)"""
    keyboard = []
    
    for i in range(0, len(items), columns):
        row = []
        for j in range(columns):
            if i + j < len(items):
                item_index = i + j
                # Обрезаем длинные элементы для лучшей читаемости
                item_text = items[item_index]
                if len(item_text) > 20:
                    item_text = item_text[:17] + "..."
                    
                row.append(aiogram.types.InlineKeyboardButton(
                    text=item_text, 
                    callback_data=f"{callback_prefix}_{item_index}"
                ))
        keyboard.append(row)
    
    keyboard.append([aiogram.types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return aiogram.types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_cancel_inline_keyboard(skip_text: str = "⏭️ Пропустить", cancel_text: str = "❌ Отмена"):
    """Inline клавиатура с кнопками Пропустить/Отмена"""
    return aiogram.types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                aiogram.types.InlineKeyboardButton(text=skip_text, callback_data="skip"),
                aiogram.types.InlineKeyboardButton(text=cancel_text, callback_data="cancel")
            ]
        ]
    )

# Специфичные клавиатуры для различных действий

def get_team_registration_confirm_keyboard():
    """Клавиатура подтверждения регистрации команды"""
    return get_confirmation_inline_keyboard("✅ Продолжить", "❌ Отмена", "confirm_team_reg", cancel_data="cancel_team_reg")

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
    keyboard = []
    
    if is_admin and len(members) > 1:  # Можно удалять только если есть кого удалять
        # Кнопки для каждого участника (кроме самого админа)
        for member in members:
            if member.student.id != current_user_id:
                # Обрезаем длинные имена для лучшей читаемости
                name = member.student.name
                if len(name) > 15:
                    name = name[:12] + "..."
                
                keyboard.append([
                    aiogram.types.InlineKeyboardButton(
                        text=f"✏️ {name}",
                        callback_data=f"edit_member_{member.student.id}"
                    ),
                    aiogram.types.InlineKeyboardButton(
                        text=f"🗑️ Delete",
                        callback_data=f"remove_member_{member.student.id}"
                    )
                ])
    
    return aiogram.types.InlineKeyboardMarkup(inline_keyboard=keyboard)