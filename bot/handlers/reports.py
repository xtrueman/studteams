"""
Обработчики функций отчетов по спринтам.

Обрабатывают создание, просмотр и удаление отчетов о проделанной работе.
"""

import aiogram
import aiogram.filters
import aiogram.fsm.context
from aiogram import F

import bot.db as db
import bot.keyboards.inline as inline_keyboards
import bot.keyboards.reply as keyboards
import bot.states.user_states as states
import bot.utils.decorators as decorators
import bot.utils.helpers as helpers


@decorators.log_handler("my_reports")
async def handle_my_reports(message: aiogram.types.Message):
    """Показать отчеты пользователя"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student:
        await message.answer("❌ Вы не зарегистрированы в системе.")
        return

    reports = db.report_get_by_student(student['student_id'])
    report_text = helpers.format_reports_list(reports)

    # Создаем inline клавиатуру для управления отчетами
    keyboard = inline_keyboards.get_report_management_keyboard(reports)

    await message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)


@decorators.log_handler("send_report")
async def handle_send_report(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало создания отчета"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
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
        await message.answer("❌ Отправка отчета отменена.", reply_markup=keyboard)
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
            await message.answer("❌ Отправка отчета отменена.", reply_markup=keyboard)
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

    # Сохраняем текст отчета в состоянии
    await state.update_data(report_text=report_text)

    # Получаем данные и сохраняем отчет сразу
    student = db.student_get_by_tg_id(message.from_user.id)
    data = await state.get_data()
    is_editing = data.get('editing', False)

    try:
        db.report_create_or_update(
            student_id=student['student_id'],
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
        reports = db.report_get_by_student(student['student_id'])
        report_text = helpers.format_reports_list(reports)
        keyboard = inline_keyboards.get_report_management_keyboard(reports)
        await message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении отчета: {e!s}\n"
            f"Попробуйте еще раз."
        )
        await state.clear()


def register_reports_handlers(dp: aiogram.Dispatcher):
    """Регистрация обработчиков отчетов"""
    # FSM обработчики РЕГИСТРИРУЮТСЯ ПЕРВЫМИ
    dp.message.register(process_report_text, states.ReportCreation.report_text)

    # Основные команды (регистрируются ПОСЛЕ FSM)
    dp.message.register(handle_my_reports, F.text == "Мои отчёты")
    dp.message.register(handle_send_report, F.text == "Отправить отчёт")
