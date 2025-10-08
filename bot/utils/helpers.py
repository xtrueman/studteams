"""
Вспомогательные функции для бота StudHelper.

Содержит вспомогательные утилиты для форматирования, валидации и других общих задач.
"""

import datetime
import random
import string

import config

import bot.db as db


def is_valid_team_name(name: str) -> bool:
    """Проверяет валидность названия команды"""
    return 3 <= len(name) <= 64


def is_valid_product_name(name: str) -> bool:
    """Проверяет валидность названия продукта"""
    return 3 <= len(name) <= 100


def is_valid_group_number(group: str) -> bool:
    """Проверяет валидность номера группы"""
    return 2 <= len(group) <= 16


def extract_sprint_number(text: str) -> int | None:
    """Извлекает номер спринта из текста"""
    import re
    # Ищем первое число в тексте
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return None


def generate_invite_code(length: int = 8) -> str:
    """Генерирует случайный код приглашения"""
    characters = string.ascii_uppercase + string.digits
    # Исключаем похожие символы: 0, O, I, l
    characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('l', '')
    return ''.join(random.choice(characters) for _ in range(length))


def format_datetime(dt: str | datetime.datetime) -> str:
    """Форматирует дату и время для отображения"""
    if dt == "now":
        dt = datetime.datetime.now()
    elif isinstance(dt, str):
        # Пытаемся распарсить строку в datetime
        try:
            dt = datetime.datetime.fromisoformat(dt)
        except ValueError:
            return dt  # Возвращаем как есть если не удалось распарсить
    return dt.strftime("%d.%m.%Y %H:%M")


def format_reports_list(reports: list) -> str:
    """Форматирует список отчетов для отображения"""
    if not reports:
        return "📝 У вас пока нет отчетов."

    text = "*Мои отчёты:*\n\n"
    for report in reports:
        # For MySQL version, dates might be strings, so we handle them appropriately
        date_str = report['report_date']
        if isinstance(date_str, datetime.datetime):
            date_str = format_datetime(date_str)

        text += f"📊 Спринт №{report['sprint_num']} ({date_str})\n"
        # Truncate report text for preview
        preview = report['report_text'][:100] + "..." if len(report['report_text']) > 100 else report['report_text']
        text += f"{preview}\n\n"

    return text


def get_invite_link_text(team_name: str, invite_code: str, show_instruction: bool = False) -> str:
    """Генерация текста с ссылкой-приглашением"""
    invite_url = f"https://t.me/{config.BOT_USERNAME}?start={invite_code}"
    base_text = (
        f"🔗 *Ссылка-приглашение:*\n"
        f"`{invite_url}`\n"
    )

    if show_instruction:
        base_text += "\n\n📤 Отправьте эту ссылку участникам команды для присоединения."

    return base_text


def format_team_info(team: dict, all_members: list) -> str:
    """Форматирует информацию о команде для отображения"""
    team_info = (
        f"👥 Команда: *«{team['team_name']}»*\n"
        f"📱 Продукт: «{team['product_name']}»\n"
    )

    # Генерируем и показываем ссылку-приглашение всегда
    invite_link_text = get_invite_link_text(team['team_name'], team['invite_code'])
    team_info += f"\n{invite_link_text}\n"

    team_info += "*Участники команды:*\n"
    for member in all_members:
        # Direct dictionary access for MySQL data
        name = member['name']
        role = member['role']

        team_info += f"• {name} ({role})\n"

    return team_info


def get_team_display_data(student_id: str, tg_id: int):
    """Получение данных для отображения информации о команде"""
    import bot.keyboards.inline as inline_keyboards

    student = db.student_get_by_tg_id(tg_id)

    if not student:
        return None

    # Check if student is in a team
    if 'team' not in student:
        return None

    team = student['team']

    # Получаем всех участников команды, включая администратора
    all_members = db.team_get_all_members(team['team_id'])

    # Проверяем права администратора
    is_admin = team['admin_student_id'] == student['student_id']

    team_info = format_team_info(team, all_members)

    # Добавляем inline клавиатуру для управления участниками (только для админов)
    keyboard = inline_keyboards.get_team_member_management_keyboard(
        all_members, student['student_id'], is_admin
    )

    return {
        'team_info': team_info,
        'keyboard': keyboard,
        'is_admin': is_admin,
        'team': team,
        'all_members': all_members
    }
