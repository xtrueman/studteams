"""
Вспомогательные функции для бота StudHelper.

Содержит вспомогательные утилиты для форматирования, валидации и других общих задач.
"""

import datetime
import random
import string

# import bot.database.queries as queries
import bot.db as db
import config


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
    if text.startswith("Спринт №"):
        try:
            return int(text.split("№")[1])
        except (ValueError, IndexError):
            return None
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
        date_str = report.get('report_date', 'Неизвестно')
        if isinstance(date_str, datetime.datetime):
            date_str = format_datetime(date_str)
        
        text += f"📊 Спринт №{report['sprint_num']} ({date_str})\n"
        # Truncate report text for preview
        preview = report['report_text'][:100] + "..." if len(report['report_text']) > 100 else report['report_text']
        text += f"{preview}\n\n"

    return text


def format_team_info(team: dict, all_members: list, invite_link_text: str | None = None) -> str:
    """Форматирует информацию о команде для отображения"""
    team_info = (
        f"👥 *Команда: {team['team_name']}*\n"
        f"📱 Продукт: {team['product_name']}\n"
        f"🔗 Код приглашения: `{team['invite_code']}`\n\n"
    )

    if invite_link_text:
        team_info += invite_link_text + "\n"

    team_info += "*Участники команды:*\n"
    for member in all_members:
        # Handle both object attributes and dictionary access
        if hasattr(member, 'role'):
            role = member.role
        elif isinstance(member, dict) and 'role' in member:
            role = member['role']
        else:
            role = 'Участник команды'
            
        # Handle student name access
        if hasattr(member, 'student') and hasattr(member.student, 'name'):
            name = member.student.name
        elif isinstance(member, dict) and 'name' in member:
            name = member['name']
        else:
            name = 'Неизвестно'
            
        team_info += f"• {name} ({role})\n"

    return team_info


async def get_team_display_data(student_id: str | None, tg_id: int,
                                bot_username: str | None = None):
    """Получение данных для отображения информации о команде"""
    # import bot.database.queries as queries
    import bot.keyboards.inline as inline_keyboards

    student = db.get_student_by_tg_id(tg_id)

    if not student or 'team' not in student:
        return None

    team = student['team']

    # Получаем всех участников команды
    teammates = db.get_teammates(student['student_id'])

    # Создаем объект для текущего пользователя
    class MockStudent:
        def __init__(self, student_obj):
            self.id = student_obj['student_id']
            self.name = student_obj['name']

    class MockMembership:
        def __init__(self, student_obj, role):
            self.student = MockStudent(student_obj)
            self.role = role

    # Преобразуем teammate объекты в единую структуру
    teammate_memberships = []
    for teammate in teammates:
        role = teammate.get('role', 'Участник команды')
        teammate_memberships.append(MockMembership(teammate, role))

    # Формируем список участников включая текущего пользователя
    # Для текущего пользователя мы берем роль из team_memberships если она есть
    current_user_role = 'Scrum Master' if team['admin_student_id'] == student['student_id'] else 'Участник команды'
    all_members = [*teammate_memberships, MockMembership(student, current_user_role)]

    # Проверяем права администратора
    is_admin = team['admin_student_id'] == student['student_id']

    # Для админов генерируем ссылку-приглашение
    invite_link_text = None
    if is_admin and bot_username:
        invite_link_text = get_invite_link_text(team['team_name'], team['invite_code'], bot_username)

    team_info = format_team_info(team, all_members, invite_link_text)

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


def get_invite_link_text(team_name: str, invite_code: str, bot_username: str | None,
                         show_instruction: bool = False) -> str:
    """Генерация текста с ссылкой-приглашением"""
    invite_url = f"https://t.me/{bot_username}?start={invite_code}"
    base_text = (
        f"\n🔗 *Ссылка-приглашение:*\n"
        f"`{invite_url}`\n"
    )

    if show_instruction:
        base_text += "\n\n📤 Отправьте эту ссылку участникам команды для присоединения."

    return base_text