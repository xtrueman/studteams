"""
Обработчики административных функций бота.

Обрабатывают команды администратора бота и функции управления.
"""

import telebot

from bot import db
from bot.bot_instance import bot
from bot.keyboards import inline as inline_keyboards
from bot.keyboards import reply as keyboards
from bot.state_storage import state_storage
from bot.utils import decorators as decorators
from bot.utils import helpers as helpers


def get_team_member_stats(member_id: int) -> dict:
    """
    Получение статистики участника команды.

    Args:
        member_id: ID участника

    Returns:
        Словарь со статистикой участника
    """
    try:
        # Получаем отчеты участника
        reports = db.report_get_by_student(member_id)

        # Получаем оценки, данные участником
        ratings_given = db.rating_get_given_by_student(member_id)

        # Получаем оценки, полученные участником
        ratings_received = db.rating_get_who_rated_me(member_id)

        # Считаем среднюю оценку, если есть оценки
        avg_rating = 0
        if ratings_received:
            total_rating = 0
            count = 0
            for rating in ratings_received:
                if isinstance(rating, dict):
                    total_rating += rating.get('overall_rating', 0)
                else:
                    total_rating += getattr(rating, 'overall_rating', 0)
                count += 1
            if count > 0:
                avg_rating = round(total_rating / count, 1)

        return {
            'success': True,
            'reports': reports,
            'reports_count': len(reports),
            'ratings_given': ratings_given,
            'ratings_given_count': len(ratings_given),
            'ratings_received': ratings_received,
            'ratings_received_count': len(ratings_received),
            'average_rating': avg_rating,
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


def get_team_overall_stats(team_id: int) -> dict:
    """
    Получение общей статистики команды.

    Args:
        team_id: ID команды

    Returns:
        Словарь с общей статистикой команды
    """
    try:
        # Получаем всех участников команды, включая администратора
        all_members = db.team_get_all_members(team_id)

        if not all_members:
            return {
                'success': False,
                'error': 'В команде нет участников',
            }

        # Собираем статистику для каждого участника
        team_stats = []

        for member in all_members:
            # Получаем ID участника
            member_id = ""
            member_name = ""
            member_role = ""

            if isinstance(member, dict):
                member_id = member.get('student_id', '')
                member_name = member.get('name', 'Неизвестно')
                member_role = member.get('role', 'Участник')
            else:
                member_id = getattr(member, 'student_id', '')
                member_name = getattr(member, 'name', 'Неизвестно')
                member_role = getattr(member, 'role', 'Участник')

            # Получаем количество отчетов
            # Конвертируем member_id в int если это строка
            member_id_int = int(member_id) if isinstance(member_id, str) else member_id
            reports = db.report_get_by_student(member_id_int)
            reports_count = len(reports) if reports else 0

            # Получаем количество оценок, данных участником
            ratings_given = db.rating_get_given_by_student(member_id_int)
            ratings_given_count = len(ratings_given) if ratings_given else 0

            # Получаем количество оценок, полученных участником
            ratings_received = db.rating_get_who_rated_me(member_id_int)
            ratings_received_count = len(ratings_received) if ratings_received else 0

            # Считаем среднюю оценку, если есть оценки
            avg_rating = 0
            if ratings_received:
                total_rating = 0
                count = 0
                for rating in ratings_received:
                    if isinstance(rating, dict):
                        total_rating += rating.get('overall_rating', 0)
                    else:
                        total_rating += getattr(rating, 'overall_rating', 0)
                    count += 1
                if count > 0:
                    avg_rating = round(total_rating / count, 1)

            team_stats.append({
                'name': member_name,
                'role': member_role,
                'reports_count': reports_count,
                'ratings_given_count': ratings_given_count,
                'ratings_received_count': ratings_received_count,
                'avg_rating': avg_rating,
            })

        return {
            'success': True,
            'members': all_members,
            'stats': team_stats,
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


@decorators.log_handler("admin_panel")
def handle_admin_panel(message: telebot.types.Message):
    """Показать панель администратора"""
    # В реальной реализации здесь должна быть проверка прав администратора
    # Например, проверка по списку разрешенных user_id

    keyboard = keyboards.get_admin_panel_keyboard()
    bot.send_message(message.chat.id,
        "🔧 *Панель администратора*\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@decorators.log_handler("view_team_members")
def handle_view_team_members(message: telebot.types.Message):
    """Просмотр участников команды"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    # Check if student is in a team
    if 'team' not in student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    # Check if user is admin
    if isinstance(student, dict) and 'team' in student:
        if isinstance(student['team'], dict) and 'admin_student_id' in student['team']:
            if student['team']['admin_student_id'] != student['student_id']:
                bot.send_message(message.chat.id, "❌ Недостаточно прав.")
                return
        else:
            bot.send_message(message.chat.id, "❌ Ошибка данных.")
            return
    else:
        bot.send_message(message.chat.id, "❌ Ошибка данных.")
        return

    # Get student ID safely
    student_id = ""
    if isinstance(student, dict):
        student_id = student.get('student_id', '')
    else:
        student_id = getattr(student, 'student_id', '')

    team_data = helpers.get_team_display_data(student_id, message.from_user.id)

    if not team_data:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    bot.send_message(message.chat.id, team_data['team_info'], parse_mode="Markdown", reply_markup=team_data['keyboard'])


@decorators.log_handler("remove_team_member")
def handle_remove_team_member(message: telebot.types.Message, ):
    """Начало удаления участника команды"""
    # This function is now handled through inline keyboards in the view_team_members function
    # We'll keep it for backward compatibility but redirect to view_team_members
    handle_view_team_members(message)


@decorators.log_handler("process_member_selection")
def process_member_selection(message: telebot.types.Message, ):
    """Обработка выбора участника для удаления"""
    if message.text == "Отмена":
        cancel_admin_action(message)
        return

    data = state_storage.get_data(message.from_user.id)
    teammates = data.get('teammates', [])

    # Находим выбранного участника
    selected_member = None
    for teammate in teammates:
        # Ensure teammate is a dictionary
        if isinstance(teammate, dict):
            if teammate['name'] == message.text:
                selected_member = teammate
                break
        else:
            # Handle case where teammate might be a different type
            if getattr(teammate, 'name', '') == message.text:
                selected_member = teammate
                break

    if not selected_member:
        bot.send_message(message.chat.id, "❌ Участник не найден. Выберите участника из списка:")
        return

    # Сохраняем выбранного участника в состоянии
    state_storage.update_data(message.from_user.id, selected_member=selected_member)
    state_storage.set_state(message.from_user.id, "states.AdminActions.confirm_removal")

    # Подтверждение удаления
    keyboard = keyboards.get_confirmation_keyboard("Подтвердить", "Отмена")

    # Get name safely
    member_name = ""
    if isinstance(selected_member, dict):
        member_name = selected_member['name']
    else:
        member_name = getattr(selected_member, 'name', 'Неизвестно')

    bot.send_message(message.chat.id,
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы действительно хотите удалить *{member_name}* из команды?\n\n"
        f"*Это действие нельзя отменить!*",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@decorators.log_handler("confirm_member_removal")
def confirm_member_removal(message: telebot.types.Message, ):
    """Подтверждение удаления участника"""
    if message.text == "Подтвердить":
        data = state_storage.get_data(message.from_user.id)
        selected_member = data.get('selected_member')
        student = db.student_get_by_tg_id(message.from_user.id)

        if not selected_member or not student:
            bot.send_message(message.chat.id, "❌ Ошибка данных.")
            state_storage.clear_state(message.from_user.id)
            return

        try:
            # Get IDs safely
            team_id = ""
            student_id = ""

            if isinstance(student, dict) and 'team' in student:
                if isinstance(student['team'], dict):
                    team_id = student['team'].get('team_id', '')
                else:
                    team_id = getattr(student['team'], 'team_id', '')
            elif hasattr(student, 'team'):
                team_id = getattr(student['team'], 'team_id', '')

            if isinstance(selected_member, dict):
                student_id = selected_member.get('student_id', '')
            else:
                student_id = getattr(selected_member, 'student_id', '')

            # Convert to integers for database operations
            team_id_int = int(team_id) if str(team_id).isdigit() else 0
            student_id_int = int(student_id) if str(student_id).isdigit() else 0

            db.team_remove_member(
                team_id=team_id_int,
                student_id=student_id_int,
            )

            # Get name safely
            member_name = ""
            if isinstance(selected_member, dict):
                member_name = selected_member.get('name', 'Неизвестно')
            else:
                member_name = getattr(selected_member, 'name', 'Неизвестно')

            bot.send_message(message.chat.id,
                f"✅ Участник *{member_name}* успешно удален из команды!",
                parse_mode="Markdown",
            )

        except Exception as e:
            bot.send_message(message.chat.id,
                f"❌ Ошибка при удалении участника: {e!s}",
            )

    elif message.text == "Отмена":
        bot.send_message(message.chat.id, "❌ Удаление участника отменено.")

    state_storage.clear_state(message.from_user.id)


@decorators.log_handler("view_member_stats")
def handle_view_member_stats(message: telebot.types.Message, ):
    """Просмотр статистики участника"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    # Проверяем права администратора команды
    if student['team']['admin_student_id'] != student['student_id']:
        bot.send_message(message.chat.id, "❌ Недостаточно прав.")
        return

    teammates = db.student_get_teammates(student['student_id'])

    if not teammates:
        bot.send_message(message.chat.id, "👥 В команде нет других участников.")
        return

    # Сохраняем список участников в состоянии
    state_storage.update_data(message.from_user.id, teammates=teammates)
    state_storage.set_state(message.from_user.id, "states.AdminActions.select_member_stats")

    # Создаем клавиатуру с выбором участников
    teammate_names = []
    for teammate in teammates:
        # Ensure teammate is a dictionary
        if isinstance(teammate, dict):
            teammate_names.append(teammate['name'])
        else:
            # Handle case where teammate might be a different type
            teammate_names.append(getattr(teammate, 'name', 'Неизвестно'))

    keyboard = inline_keyboards.get_dynamic_inline_keyboard(teammate_names, "member", columns=2)

    bot.send_message(message.chat.id,
        "📊 *Статистика участника*\n\n"
        "Выберите участника для просмотра статистики:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@decorators.log_handler("process_member_stats_selection")
def process_member_stats_selection(message: telebot.types.Message, ):
    """Обработка выбора участника для просмотра статистики"""
    if message.text == "Отмена":
        cancel_admin_action(message)
        return

    data = state_storage.get_data(message.from_user.id)
    teammates = data.get('teammates', [])

    # Находим выбранного участника
    selected_member = None
    for teammate in teammates:
        # Ensure teammate is a dictionary
        if isinstance(teammate, dict):
            if teammate['name'] == message.text:
                selected_member = teammate
                break
        else:
            # Handle case where teammate might be a different type
            if getattr(teammate, 'name', '') == message.text:
                selected_member = teammate
                break

    if not selected_member:
        bot.send_message(message.chat.id, "❌ Участник не найден. Выберите участника из списка:")
        return

    # Получаем статистику участника с помощью новой функции
    try:
        # Get ID safely
        member_id = ""
        if isinstance(selected_member, dict):
            member_id = selected_member['student_id']
        else:
            member_id = getattr(selected_member, 'student_id', '')

        # Используем новую функцию для получения статистики
        stats = get_team_member_stats(member_id)

        if not stats['success']:
            bot.send_message(message.chat.id, f"❌ Ошибка при получении статистики: {stats['error']}")
            state_storage.clear_state(message.from_user.id)
            return

        # Get name safely
        member_name = ""
        if isinstance(selected_member, dict):
            member_name = selected_member['name']
        else:
            member_name = getattr(selected_member, 'name', 'Неизвестно')

        # Формируем текст статистики
        stats_text = f"📊 *Статистика участника: {member_name}*\n\n"

        # Отчеты
        stats_text += "📝 *Отчеты:*\n"
        if stats['reports']:
            stats_text += f"Отправлено: {stats['reports_count']}\n"
            sprint_numbers = []
            for report in stats['reports']:
                if isinstance(report, dict):
                    sprint_numbers.append(str(report['sprint_num']))
                else:
                    sprint_numbers.append(str(getattr(report, 'sprint_num', '')))
            stats_text += f"Спринты: {', '.join(sprint_numbers)}\n\n"
        else:
            stats_text += "Нет отчетов\n\n"

        # Оценки, данные другими
        stats_text += "⭐ *Оценки, данные другими:*\n"
        if stats['ratings_received']:
            stats_text += f"Получено: {stats['ratings_received_count']}\n"
            stats_text += f"Средняя оценка: {stats['average_rating']:.1f}/10\n\n"
        else:
            stats_text += "Пока никто не оценил\n\n"

        # Оценки, данные участником
        stats_text += "👥 *Оценки, данные участником:*\n"
        if stats['ratings_given']:
            stats_text += f"Отправлено: {stats['ratings_given_count']}\n"
        else:
            stats_text += "Не оценивал других\n"

        bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(message.chat.id,
            f"❌ Ошибка при получении статистики: {e!s}",
        )

    state_storage.clear_state(message.from_user.id)


@decorators.log_handler("team_report")
def handle_team_report(message: telebot.types.Message):
    """Просмотр отчёта о команде"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    # Получаем общую статистику команды с помощью новой функции
    team_stats_result = get_team_overall_stats(student['team']['team_id'])

    if not team_stats_result['success']:
        bot.send_message(message.chat.id, f"❌ Ошибка при получении отчета: {team_stats_result['error']}")
        return

    # Формируем текст отчета
    report_text = f"📊 *Отчёт о команде: {student['team']['team_name']}*\n\n"

    for stats in team_stats_result['stats']:
        report_text += f"👤 {stats['name']} ({stats['role']})\n"
        report_text += f"   📝 Отчеты: {stats['reports_count']}\n"
        report_text += f"   ⭐ Оценки от меня: {stats['ratings_given_count']}\n"
        report_text += f"   👀 Оценки мне: {stats['ratings_received_count']}"
        if stats['avg_rating'] > 0:
            report_text += f" (средняя: {stats['avg_rating']}/10)"
        report_text += "\n\n"

    bot.send_message(message.chat.id, report_text, parse_mode="Markdown")


def cancel_admin_action(message: telebot.types.Message, ):
    """Отмена административного действия"""
    state_storage.clear_state(message.from_user.id)
    student = db.student_get_by_tg_id(message.from_user.id)

    if student:
        has_team = 'team' in student
        is_admin = False
        if has_team:
            is_admin = student['team']['admin_student_id'] == student['student_id']

        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
    else:
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)

    bot.send_message(message.chat.id, "❌ Действие отменено.", reply_markup=keyboard)


def register_admin_handlers(bot_instance: telebot.TeleBot):
    """Регистрация обработчиков административных функций"""
    bot_instance.register_message_handler(handle_admin_panel, func=lambda m: m.text == "🔧 Админ панель")
    bot_instance.register_message_handler(handle_view_team_members, func=lambda m: m.text == "👥 Участники команды")
    bot_instance.register_message_handler(handle_view_member_stats, func=lambda m: m.text == "📊 Статистика участника")

    # FSM для просмотра статистики
