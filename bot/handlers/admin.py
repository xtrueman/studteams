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

    members_text = "*Участники команды:*\n\n"
    for teammate in teammates:
        members_text += f"• {teammate['name']} ({teammate['role']})\n"

    await message.answer(
        members_text,
        parse_mode="Markdown",
        reply_markup=inline_keyboards.get_team_member_management_keyboard(teammates, student['student_id'], True)
    )


@decorators.log_handler("remove_team_member")
async def handle_remove_team_member(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало удаления участника команды"""
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
    await state.set_state(states.AdminActions.select_member)

    # Создаем клавиатуру с выбором участников
    keyboard = inline_keyboards.get_team_members_inline_keyboard(teammates)

    await message.answer(
        "🗑️ *Удаление участника команды*\n\n"
        "Выберите участника для удаления:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


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
        if teammate['name'] == message.text:
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

    await message.answer(
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы действительно хотите удалить *{selected_member['name']}* из команды?\n\n"
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
            db.team_remove_member(
                team_id=student['team']['team_id'],
                student_id=selected_member['student_id']
            )

            await message.answer(
                f"✅ Участник *{selected_member['name']}* успешно удален из команды!",
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
    keyboard = inline_keyboards.get_team_members_inline_keyboard(teammates)

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
        if teammate['name'] == message.text:
            selected_member = teammate
            break

    if not selected_member:
        await message.answer("❌ Участник не найден. Выберите участника из списка:")
        return

    # Получаем статистику участника
    try:
        reports = db.report_get_by_student(selected_member['student_id'])
        ratings_given = db.rating_get_given_by_student(selected_member['student_id'])
        ratings_received = db.rating_get_who_rated_me(selected_member['student_id'])

        # Формируем текст статистики
        stats_text = f"📊 *Статистика участника: {selected_member['name']}*\n\n"

        # Отчеты
        stats_text += f"📝 *Отчеты:*\n"
        if reports:
            stats_text += f"Отправлено: {len(reports)}\n"
            sprint_numbers = [str(report['sprint_num']) for report in reports]
            stats_text += f"Спринты: {', '.join(sprint_numbers)}\n\n"
        else:
            stats_text += "Нет отчетов\n\n"

        # Оценки, данные другими
        stats_text += f"⭐ *Оценки, данные другими:*\n"
        if ratings_received:
            stats_text += f"Получено: {len(ratings_received)}\n"
            avg_rating = sum(rating['overall_rating'] for rating in ratings_received) / len(ratings_received)
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
    dp.message.register(handle_remove_team_member, F.text == "🗑️ Удалить участника")
    dp.message.register(handle_view_member_stats, F.text == "📊 Статистика участника")

    # FSM для удаления участника
    dp.message.register(process_member_selection, states.AdminActions.select_member)
    dp.message.register(confirm_member_removal, states.AdminActions.confirm_removal)

    # FSM для просмотра статистики
    dp.message.register(process_member_stats_selection, states.AdminActions.select_member_stats)