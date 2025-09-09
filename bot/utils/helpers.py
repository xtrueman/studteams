"""
Вспомогательные функции для бота.

Содержит утилиты для форматирования, валидации и обработки данных.
"""

import secrets
import string


def generate_invite_code(length: int = 8) -> str:
    """Генерация случайного кода приглашения"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def format_team_info(team_data, members_data, invite_link_text: str | None = None) -> str:
    """Форматирование информации о команде"""
    if not team_data:
        return "❌ Команда не найдена"

    text = f"👥 *{team_data.team_name}*\n"
    text += f"📱 Продукт: {team_data.product_name}\n"
    text += f"👑 Администратор: {team_data.admin.name}\n"

    # Добавляем ссылку-приглашение перед списком участников
    if invite_link_text:
        text += invite_link_text
    text += "\n"

    if members_data:
        text += "*Участники команды:*\n"
        for i, member in enumerate(members_data, 1):
            role_icon = "👑" if member.student.id == team_data.admin.id else "👤"
            text += f"{i}. {role_icon} {member.student.name} — {member.role}\n"
    else:
        text += "Участников пока нет\n"

    return text


def format_reports_list(reports) -> str:
    """Форматирование списка отчетов"""
    if not reports:
        return "📋 У вас пока нет отчетов"

    text = "📋 *Отчёты о проделанной работе:*\n\n"
    for report in reports:
        text += f"*Спринт №{report.sprint_num}:*\n"
        text += f"_{report.report_text}_\n\n"

    return text


# ... existing code ...


def extract_sprint_number(text: str) -> int | None:
    """Извлечение номера спринта из текста кнопки"""
    try:
        if "Спринт №" in text:
            return int(text.split("№")[1])
    except (ValueError, IndexError):
        pass
    return None


def validate_rating(text: str) -> int | None:
    """Валидация оценки"""
    try:
        rating = int(text)
        if 1 <= rating <= 10:
            return rating
    except ValueError:
        pass
    return None


# ... existing code ...


def is_valid_team_name(name: str) -> bool:
    """Проверка валидности названия команды"""
    return len(name.strip()) >= 3 and len(name.strip()) <= 64


def is_valid_product_name(name: str) -> bool:
    """Проверка валидности названия продукта"""
    return len(name.strip()) >= 3 and len(name.strip()) <= 100


def is_valid_group_number(group: str) -> bool:
    """Проверка валидности номера группы"""
    return len(group.strip()) >= 2 and len(group.strip()) <= 16


def format_datetime(dt) -> str:
    """Форматирование даты и времени"""
    import datetime
    if dt == 'now':
        dt = datetime.datetime.now(datetime.UTC)
    return dt.strftime("%d.%m.%Y %H:%M")


async def get_team_display_data(student_id: str | None, tg_id: int,
                                bot_username: str | None = None):
    """Получение данных для отображения информации о команде"""
    import bot.database.queries as queries
    import bot.keyboards.inline as inline_keyboards

    student = await queries.StudentQueries.get_by_tg_id(tg_id)

    if not student or not getattr(student, 'team_memberships', None):
        return None

    team_membership = student.team_memberships[0]
    team = team_membership.team

    # Получаем всех участников команды
    teammates = await queries.StudentQueries.get_teammates(student.id)

    # Создаем объект для текущего пользователя
    class MockStudent:
        def __init__(self, student_obj):
            self.id = student_obj.id
            self.name = student_obj.name

    class MockMembership:
        def __init__(self, student_obj, role):
            self.student = MockStudent(student_obj)
            self.role = role

    # Преобразуем teammate объекты в единую структуру
    teammate_memberships = []
    for teammate in teammates:
        role = teammate.team_memberships[0].role if teammate.team_memberships else "Участник команды"
        teammate_memberships.append(MockMembership(teammate, role))

    # Формируем список участников включая текущего пользователя
    all_members = [*teammate_memberships, MockMembership(student, team_membership.role)]

    # Проверяем права администратора
    is_admin = team.admin.id == student.id

    # Для админов генерируем ссылку-приглашение
    invite_link_text = None
    if is_admin and bot_username:
        invite_link_text = get_invite_link_text(team.team_name, team.invite_code, bot_username)

    team_info = format_team_info(team, all_members, invite_link_text)

    # Добавляем inline клавиатуру для управления участниками (только для админов)
    keyboard = inline_keyboards.get_team_member_management_keyboard(
        all_members, student.id, is_admin
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
