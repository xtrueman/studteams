"""
Обработчики функций отчетов по спринтам.

Обрабатывают создание, просмотр и удаление отчетов о проделанной работе.
"""

import aiogram
import aiogram.filters
import aiogram.fsm.context
from aiogram import F

import bot.database.queries as queries
import bot.keyboards.inline as inline_keyboards
import bot.keyboards.reply as keyboards
import bot.states.user_states as states
import bot.utils.decorators as decorators
import bot.utils.helpers as helpers


@decorators.log_handler("my_reports")
async def handle_my_reports(message: aiogram.types.Message):
    """Показать отчеты пользователя"""
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)

    if not student:
        await message.answer("❌ Вы не зарегистрированы в системе.")
        return

    reports = await queries.ReportQueries.get_by_student(student.id)
    report_text = helpers.format_reports_list(reports)

    # Создаем inline клавиатуру для управления отчетами
    keyboard = inline_keyboards.get_report_management_keyboard(reports)

    await message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)


@decorators.log_handler("send_report")
async def handle_send_report(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало создания отчета"""
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)

    if not student or not getattr(student, 'team_memberships', None):
        await message.answer("❌ Вы не состоите в команде.")
        return

    await state.set_state(states.ReportCreation.sprint_selection)
    await message.answer(
        "📝 *Отправка отчета*\n\n"
        "Выберите номер спринта:",
        reply_markup=inline_keyboards.get_sprints_inline_keyboard(),
        parse_mode="Markdown"
    )


@decorators.log_handler("process_sprint_selection")
async def process_sprint_selection(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка выбора спринта"""
    if message.text == "Отмена":
        await cancel_action(message, state)
        return

    sprint_num = helpers.extract_sprint_number(message.text)

    if sprint_num is None:
        await message.answer("❌ Неверный формат. Выберите спринт из предложенных вариантов:")
        return

    await state.update_data(sprint_num=sprint_num)
    await state.set_state(states.ReportCreation.report_text)

    await message.answer(
        f"✅ Спринт №{sprint_num}\n\n"
        f"📝 Введите текст отчета о проделанной работе:",
        reply_markup=keyboards.get_confirmation_keyboard("Отмена", "Назад")
    )


@decorators.log_handler("process_report_text")
async def process_report_text(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка текста отчета"""
    if message.text in ["Отмена", "Назад"]:
        if message.text == "Назад":
            await state.set_state(states.ReportCreation.sprint_selection)
            await message.answer(
                "📝 Выберите номер спринта:",
                reply_markup=keyboards.get_sprints_keyboard()
            )
        else:
            await cancel_action(message, state)
        return

    report_text = message.text.strip()

    if len(report_text) < 20:
        await message.answer(
            "❌ Отчет слишком короткий. Минимум 20 символов. Попробуйте еще раз:"
        )
        return

    if len(report_text) > 4000:
        await message.answer(
            "❌ Отчет слишком длинный. Максимум 4000 символов. Попробуйте еще раз:"
        )
        return

    # Получаем данные и сохраняем отчет сразу
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    data = await state.get_data()
    is_editing = data.get('editing', False)

    try:
        await queries.ReportQueries.create_or_update(
            student_id=student.id,
            sprint_num=data['sprint_num'],
            report_text=report_text
        )

        await state.clear()

        # Показываем сообщение об успешном сохранении
        if is_editing:
            await message.answer(
                f"✅ *Отчет успешно обновлен!*\n\n"
                f"📊 Спринт: №{data['sprint_num']}\n"
                f"📅 Дата: {helpers.format_datetime('now')}",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                f"✅ *Отчет успешно отправлен!*\n\n"
                f"📊 Спринт: №{data['sprint_num']}\n"
                f"📅 Дата: {helpers.format_datetime('now')}",
                parse_mode="Markdown"
            )

        # Переходим на страницу "Мои отчёты"
        reports = await queries.ReportQueries.get_by_student(student.id)
        report_text = helpers.format_reports_list(reports)
        keyboard = inline_keyboards.get_report_management_keyboard(reports)
        await message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении отчета: {e!s}\n"
            f"Попробуйте еще раз."
        )
        await state.clear()


@decorators.log_handler("delete_report")
async def handle_delete_report(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало удаления отчета"""
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)

    if not student:
        await message.answer("❌ Вы не зарегистрированы в системе.")
        return

    # Получаем отчеты пользователя
    reports = await queries.ReportQueries.get_by_student(student.id)

    if not reports:
        await message.answer("📋 У вас нет отчетов для удаления.")
        return

    # Создаем список спринтов с отчетами
    sprint_options = [f"Спринт №{report.sprint_num}" for report in reports]

    await state.set_state(states.ReportDeletion.sprint_selection)
    await message.answer(
        "🗑 *Удаление отчета*\n\n"
        "Выберите спринт для удаления отчета:",
        reply_markup=keyboards.get_dynamic_keyboard(sprint_options, columns=3),
        parse_mode="Markdown"
    )


@decorators.log_handler("process_delete_sprint_selection")
async def process_delete_sprint_selection(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка выбора спринта для удаления"""
    if message.text == "Отмена":
        await cancel_action(message, state)
        return

    sprint_num = helpers.extract_sprint_number(message.text)

    if sprint_num is None:
        await message.answer("❌ Неверный формат. Выберите спринт из списка:")
        return

    await state.update_data(sprint_num=sprint_num)
    await state.set_state(states.ReportDeletion.confirmation)

    await message.answer(
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы действительно хотите удалить отчет по спринту №{sprint_num}?\n\n"
        f"*Это действие нельзя отменить!*",
        reply_markup=inline_keyboards.get_report_delete_confirm_keyboard(),
        parse_mode="Markdown"
    )


@decorators.log_handler("confirm_delete_report")
async def confirm_delete_report(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Подтверждение удаления отчета"""
    if message.text == "Удалить":
        student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
        data = await state.get_data()

        try:
            await queries.ReportQueries.delete_report(
                student_id=student.id,
                sprint_num=data['sprint_num']
            )

            await state.clear()

            # Возвращаем главное меню
            has_team = bool(getattr(student, 'team_memberships', None))
            is_admin = False
            if has_team:
                team_membership = student.team_memberships[0]
                is_admin = team_membership.team.admin.id == student.id

            keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)

            await message.answer(
                f"🗑 *Отчет удален*\n\n"
                f"📊 Спринт №{data['sprint_num']} - отчет успешно удален",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

        except Exception as e:
            await message.answer(
                f"❌ Ошибка при удалении отчета: {e!s}\n"
                f"Попробуйте еще раз."
            )
            await state.clear()

    elif message.text == "Отмена":
        await cancel_action(message, state)


async def cancel_action(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Отмена текущего действия"""
    await state.clear()

    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)

    if student:
        has_team = bool(getattr(student, 'team_memberships', []))
        is_admin = False
        if has_team:
            team_membership = student.team_memberships[0]
            is_admin = team_membership.team.admin.id == student.id

        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
    else:
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)

    await message.answer("❌ Действие отменено.", reply_markup=keyboard)


def register_reports_handlers(dp: aiogram.Dispatcher):
    """Регистрация обработчиков отчетов"""
    # Основные команды
    dp.message.register(handle_my_reports, F.text == "Мои отчёты")
    dp.message.register(handle_send_report, F.text == "Отправить отчёт")
    # Кнопка "Удалить отчёт" удалена из главного меню

    # FSM для создания отчета (только текстовые поля)
    # process_sprint_selection теперь обрабатывается через callback
    dp.message.register(process_report_text, states.ReportCreation.report_text)
    # confirm_report больше не нужен - отчет сохраняется сразу

    # handle_delete_report, process_delete_sprint_selection удалены из регистрации
