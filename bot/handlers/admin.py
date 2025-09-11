"""
Обработчики административных функций бота.

Обрабатывают команды администратора бота и функции управления.
"""

import aiogram
import aiogram.filters
import aiogram.fsm.context
from aiogram import F

# import bot.database.queries as queries
import bot.db as db
import bot.keyboards.inline as inline_keyboards
import bot.keyboards.reply as keyboards
import bot.states.user_states as states
import bot.utils.decorators as decorators
import bot.utils.helpers as helpers
import config


@decorators.log_handler("admin_panel")
async def handle_admin_panel(message: aiogram.types.Message):
    """Показать панель администратора"""
    # В реальной реализации здесь должна быть проверка прав администратора
    # Например, проверка по списку разрешенных user_id
    
    keyboard = keyboards.get_admin_panel_keyboard()
    await message.answer(
        "🔧 *Панель администратора*\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@decorators.log_handler("view_team_members")
async def handle_view_team_members(message: aiogram.types.Message):
    """Просмотр участников команды"""
    student = db.student_get_by_tg_id(message.from_user.id)
    
    if not student:
        await message.answer("❌ Вы не состоите в команде.")
        return

    # Check if student is in a team
    if 'team' not in student:
        await message.answer("❌ Вы не состоите в команде.")
        return

    # Check if user is admin
    if isinstance(student, dict) and 'team' in student:
        if isinstance(student['team'], dict) and 'admin_student_id' in student['team']:
            if student['team']['admin_student_id'] != student['student_id']:
                await message.answer("❌ Недостаточно прав.")
                return
        else:
            await message.answer("❌ Ошибка данных.")
            return
    else:
        await message.answer("❌ Ошибка данных.")
        return

    # Get student ID safely
    student_id = ""
    if isinstance(student, dict):
        student_id = student.get('student_id', '')
    else:
        student_id = getattr(student, 'student_id', '')

    team_data = helpers.get_team_display_data(student_id, message.from_user.id)

    if not team_data:
        await message.answer("❌ Вы не состоите в команде.")
        return

    await message.answer(team_data['team_info'], parse_mode="Markdown", reply_markup=team_data['keyboard'])


@decorators.log_handler("remove_team_member")
async def handle_remove_team_member(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало удаления участника команды"""
    # This function is now handled through inline keyboards in the view_team_members function
    # We'll keep it for backward compatibility but redirect to view_team_members
    await handle_view_team_members(message)


@decorators.log_handler("process_member_selection")
async def process_member_selection(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка выбора участника для удаления"""
    if message.text == "Отмена":
        await cancel_admin_action(message, state)
        return

    data = await state.get_data()
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
        await message.answer("❌ Участник не найден. Выберите участника из списка:")
        return

    # Сохраняем выбранного участника в состоянии
    await state.update_data(selected_member=selected_member)
    await state.set_state(states.AdminActions.confirm_removal)

    # Подтверждение удаления
    keyboard = keyboards.get_confirmation_keyboard("Подтвердить", "Отмена")

    # Get name safely
    member_name = ""
    if isinstance(selected_member, dict):
        member_name = selected_member['name']
    else:
        member_name = getattr(selected_member, 'name', 'Неизвестно')

    await message.answer(
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы действительно хотите удалить *{member_name}* из команды?\n\n"
        f"*Это действие нельзя отменить!*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@decorators.log_handler("confirm_member_removal")
async def confirm_member_removal(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Подтверждение удаления участника"""
    if message.text == "Подтвердить":
        data = await state.get_data()
        selected_member = data.get('selected_member')
        student = db.student_get_by_tg_id(message.from_user.id)

        if not selected_member or not student:
            await message.answer("❌ Ошибка данных.")
            await state.clear()
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
                student_id=student_id_int
            )

            # Get name safely
            member_name = ""
            if isinstance(selected_member, dict):
                member_name = selected_member.get('name', 'Неизвестно')
            else:
                member_name = getattr(selected_member, 'name', 'Неизвестно')

            await message.answer(
                f"✅ Участник *{member_name}* успешно удален из команды!",
                parse_mode="Markdown"
            )

        except Exception as e:
            await message.answer(
                f"❌ Ошибка при удалении участника: {e!s}"
            )

    elif message.text == "Отмена":
        await message.answer("❌ Удаление участника отменено.")

    await state.clear()


@decorators.log_handler("view_member_stats")
async def handle_view_member_stats(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Просмотр статистики участника"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        await message.answer("❌ Вы не состоите в команде.")
        return

    # Проверяем права администратора команды
    if student['team']['admin_student_id'] != student['student_id']:
        await message.answer("❌ Недостаточно прав.")
        return

    teammates = db.student_get_teammates(student['student_id'])

    if not teammates:
        await message.answer("👥 В команде нет других участников.")
        return

    # Сохраняем список участников в состоянии
    await state.update_data(teammates=teammates)
    await state.set_state(states.AdminActions.select_member_stats)

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

    await message.answer(
        "📊 *Статистика участника*\n\n"
        "Выберите участника для просмотра статистики:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@decorators.log_handler("process_member_stats_selection")
async def process_member_stats_selection(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка выбора участника для просмотра статистики"""
    if message.text == "Отмена":
        await cancel_admin_action(message, state)
        return

    data = await state.get_data()
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
        await message.answer("❌ Участник не найден. Выберите участника из списка:")
        return

    # Получаем статистику участника
    try:
        # Get ID safely
        member_id = ""
        if isinstance(selected_member, dict):
            member_id = selected_member['student_id']
        else:
            member_id = getattr(selected_member, 'student_id', '')

        reports = db.report_get_by_student(member_id)
        ratings_given = db.rating_get_given_by_student(member_id)
        ratings_received = db.rating_get_who_rated_me(member_id)

        # Get name safely
        member_name = ""
        if isinstance(selected_member, dict):
            member_name = selected_member['name']
        else:
            member_name = getattr(selected_member, 'name', 'Неизвестно')

        # Формируем текст статистики
        stats_text = f"📊 *Статистика участника: {member_name}*\n\n"

        # Отчеты
        stats_text += f"📝 *Отчеты:*\n"
        if reports:
            stats_text += f"Отправлено: {len(reports)}\n"
            sprint_numbers = []
            for report in reports:
                if isinstance(report, dict):
                    sprint_numbers.append(str(report['sprint_num']))
                else:
                    sprint_numbers.append(str(getattr(report, 'sprint_num', '')))
            stats_text += f"Спринты: {', '.join(sprint_numbers)}\n\n"
        else:
            stats_text += "Нет отчетов\n\n"

        # Оценки, данные другими
        stats_text += f"⭐ *Оценки, данные другими:*\n"
        if ratings_received:
            stats_text += f"Получено: {len(ratings_received)}\n"
            if ratings_received:  # Check if list is not empty before accessing elements
                total_rating = 0
                count = 0
                for rating in ratings_received:
                    if isinstance(rating, dict):
                        total_rating += rating.get('overall_rating', 0)
                    else:
                        total_rating += getattr(rating, 'overall_rating', 0)
                    count += 1
                if count > 0:
                    avg_rating = total_rating / count
                    stats_text += f"Средняя оценка: {avg_rating:.1f}/10\n\n"
        else:
            stats_text += "Пока никто не оценил\n\n"

        # Оценки, данные участником
        stats_text += f"👥 *Оценки, данные участником:*\n"
        if ratings_given:
            stats_text += f"Отправлено: {len(ratings_given)}\n"
        else:
            stats_text += "Не оценивал других\n"

        await message.answer(stats_text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при получении статистики: {e!s}"
        )

    await state.clear()


@decorators.log_handler("team_report")
async def handle_team_report(message: aiogram.types.Message):
    """Просмотр отчёта о команде"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        await message.answer("❌ Вы не состоите в команде.")
        return

    # Получаем всех участников команды, включая администратора
    all_members = db.team_get_all_members(student['team']['team_id'])

    if not all_members:
        await message.answer("👥 В команде нет участников.")
        return

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
        reports = db.report_get_by_student(member_id)
        reports_count = len(reports) if reports else 0

        # Получаем количество оценок, данных участником
        ratings_given = db.rating_get_given_by_student(member_id)
        ratings_given_count = len(ratings_given) if ratings_given else 0

        # Получаем количество оценок, полученных участником
        ratings_received = db.rating_get_who_rated_me(member_id)
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
            'avg_rating': avg_rating
        })

    # Формируем текст отчета
    report_text = f"📊 *Отчёт о команде: {student['team']['team_name']}*\n\n"
    
    for stats in team_stats:
        report_text += f"👤 {stats['name']} ({stats['role']})\n"
        report_text += f"   📝 Отчеты: {stats['reports_count']}\n"
        report_text += f"   ⭐ Оценки от меня: {stats['ratings_given_count']}\n"
        report_text += f"   👀 Оценки мне: {stats['ratings_received_count']}"
        if stats['avg_rating'] > 0:
            report_text += f" (средняя: {stats['avg_rating']}/10)"
        report_text += "\n\n"

    await message.answer(report_text, parse_mode="Markdown")


async def cancel_admin_action(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Отмена административного действия"""
    await state.clear()
    student = db.student_get_by_tg_id(message.from_user.id)

    if student:
        has_team = 'team' in student
        is_admin = False
        if has_team:
            is_admin = student['team']['admin_student_id'] == student['student_id']

        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
    else:
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)

    await message.answer("❌ Действие отменено.", reply_markup=keyboard)


def register_admin_handlers(dp: aiogram.Dispatcher):
    """Регистрация обработчиков административных функций"""
    dp.message.register(handle_admin_panel, F.text == "🔧 Админ панель")
    dp.message.register(handle_view_team_members, F.text == "👥 Участники команды")
    dp.message.register(handle_view_member_stats, F.text == "📊 Статистика участника")

    # FSM для просмотра статистики
    dp.message.register(process_member_stats_selection, states.AdminActions.select_member_stats)