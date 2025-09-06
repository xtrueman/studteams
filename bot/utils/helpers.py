"""
Вспомогательные функции для бота.

Содержит утилиты для форматирования, валидации и обработки данных.
"""

import uuid
import secrets
import string

def generate_invite_code(length: int = 8) -> str:
    """Генерация случайного кода приглашения"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def format_team_info(team_data, members_data) -> str:
    """Форматирование информации о команде"""
    if not team_data:
        return "❌ Команда не найдена"
    
    text = f"👥 *{team_data['team_name']}*\n"
    text += f"📱 Продукт: {team_data['product_name']}\n"
    text += f"👑 Администратор: {team_data['admin']['name']}\n\n"
    
    if members_data:
        text += "*Участники команды:*\n"
        for i, member in enumerate(members_data, 1):
            role_icon = "👑" if member['student']['id'] == team_data['admin']['id'] else "👤"
            text += f"{i}. {role_icon} {member['student']['name']} - {member['role']}\n"
    else:
        text += "Участников пока нет\n"
    
    return text

def format_reports_list(reports) -> str:
    """Форматирование списка отчетов"""
    if not reports:
        return "📋 У вас пока нет отчетов"
    
    text = "📋 *Ваши отчеты:*\n\n"
    for report in reports:
        date_str = report['report_date'].strftime("%d.%m.%Y %H:%M")
        text += f"*Спринт №{report['sprint_num']}*\n"
        text += f"📅 {date_str}\n"
        text += f"📝 {report['report_text'][:100]}{'...' if len(report['report_text']) > 100 else ''}\n\n"
    
    return text

def format_ratings_list(ratings) -> str:
    """Форматирование списка оценок"""
    if not ratings:
        return "⭐ Вас пока никто не оценил"
    
    text = "⭐ *Ваши оценки:*\n\n"
    for rating in ratings:
        date_str = rating['rate_date'].strftime("%d.%m.%Y")
        text += f"👤 *{rating['assessor']['name']}*\n"
        text += f"⭐ Оценка: {rating['overall_rating']}/10\n"
        text += f"✅ Плюсы: {rating['advantages']}\n"
        text += f"📈 Что улучшить: {rating['disadvantages']}\n"
        text += f"📅 {date_str}\n\n"
    
    return text

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

def is_valid_name(name: str) -> bool:
    """Проверка валидности имени"""
    return len(name.strip()) >= 2 and len(name.strip()) <= 64

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
        dt = datetime.datetime.now()
    return dt.strftime("%d.%m.%Y %H:%M")