"""
Обработчики функций отчетов по спринтам.

Обрабатывают создание, просмотр и удаление отчетов о проделанной работе.
"""

import telebot

from bot import db
from bot.bot_instance import bot
from bot.keyboards import inline as inline_keyboards
from bot.keyboards import reply as keyboards
from bot.state_storage import state_storage
from bot.utils import decorators as decorators
from bot.utils import helpers as helpers


@decorators.log_handler("my_reports")
def handle_my_reports(message: telebot.types.Message):
    """Показать отчеты пользователя"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student:
        bot.send_message(message.chat.id, "❌ Вы не зарегистрированы в системе.")
        return

    reports = db.report_get_by_student(student['student_id'])
    report_text = helpers.format_reports_list(reports)

    # Создаем inline клавиатуру для управления отчетами
    keyboard = inline_keyboards.get_report_management_keyboard(reports)

    bot.send_message(message.chat.id, report_text, parse_mode="Markdown", reply_markup=keyboard)


@decorators.log_handler("send_report")
def handle_send_report(message: telebot.types.Message, ):
    """Начало создания отчета"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    state_storage.set_state(message.from_user.id, "states.ReportCreation.sprint_selection")
    bot.send_message(message.chat.id,
        "📝 *Отправка отчета*\n\n"
        "Выберите номер спринта:",
        reply_markup=inline_keyboards.get_sprints_inline_keyboard(),
        parse_mode="Markdown",
    )


@decorators.log_handler("process_sprint_selection")
def process_sprint_selection(message: telebot.types.Message, ):
    """Обработка выбора спринта"""
    if message.text == "Отмена":
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
        bot.send_message(message.chat.id, "❌ Отправка отчета отменена.", reply_markup=keyboard)
        return

    sprint_num = helpers.extract_sprint_number(message.text)

    if sprint_num is None:
        bot.send_message(message.chat.id, "❌ Неверный формат. Выберите спринт из предложенных вариантов:")
        return

    state_storage.update_data(message.from_user.id, sprint_num=sprint_num)
    state_storage.set_state(message.from_user.id, "states.ReportCreation.report_text")

    bot.send_message(message.chat.id,
        f"✅ Спринт №{sprint_num}\n\n"
        f"📝 Введите текст отчета о проделанной работе:",
        reply_markup=keyboards.get_confirmation_keyboard("Отмена", "Назад"),
    )


@decorators.log_handler("process_report_text")
def process_report_text(message: telebot.types.Message, ):
    """Обработка текста отчета"""
    if message.text in ["Отмена", "Назад"]:
        if message.text == "Назад":
            state_storage.set_state(message.from_user.id, "states.ReportCreation.sprint_selection")
            bot.send_message(message.chat.id,
                "📝 Выберите номер спринта:",
                reply_markup=keyboards.get_sprints_keyboard(),
            )
        else:
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
            bot.send_message(message.chat.id, "❌ Отправка отчета отменена.", reply_markup=keyboard)
        return

    report_text = message.text.strip()

    if len(report_text) < 20:
        bot.send_message(message.chat.id,
            "❌ Отчет слишком короткий. Минимум 20 символов. Попробуйте еще раз:",
        )
        return

    if len(report_text) > 4000:
        bot.send_message(message.chat.id,
            "❌ Отчет слишком длинный. Максимум 4000 символов. Попробуйте еще раз:",
        )
        return

    # Сохраняем текст отчета в состоянии
    state_storage.update_data(message.from_user.id, report_text=report_text)

    # Получаем данные и сохраняем отчет сразу
    student = db.student_get_by_tg_id(message.from_user.id)
    data = state_storage.get_data(message.from_user.id)
    is_editing = data.get('editing', False)

    try:
        db.report_create_or_update(
            student_id=student['student_id'],
            sprint_num=data['sprint_num'],
            report_text=report_text,
        )

        state_storage.clear_state(message.from_user.id)

        # Показываем сообщение об успешном сохранении
        if is_editing:
            bot.send_message(message.chat.id,
                f"✅ *Отчет успешно обновлен!*\n\n"
                f"📊 Спринт: №{data['sprint_num']}\n"
                f"📅 Дата: {helpers.format_datetime('now')}",
                parse_mode="Markdown",
            )
        else:
            bot.send_message(message.chat.id,
                f"✅ *Отчет успешно отправлен!*\n\n"
                f"📊 Спринт: №{data['sprint_num']}\n"
                f"📅 Дата: {helpers.format_datetime('now')}",
                parse_mode="Markdown",
            )

        # Переходим на страницу "Мои отчёты"
        reports = db.report_get_by_student(student['student_id'])
        report_text = helpers.format_reports_list(reports)
        keyboard = inline_keyboards.get_report_management_keyboard(reports)
        bot.send_message(message.chat.id, report_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id,
            f"❌ Ошибка при сохранении отчета: {e!s}\n"
            f"Попробуйте еще раз.",
        )
        state_storage.clear_state(message.from_user.id)


def register_reports_handlers(bot_instance: telebot.TeleBot):
    """Регистрация обработчиков отчетов"""
    # FSM обработчики РЕГИСТРИРУЮТСЯ ПЕРВЫМИ

    # Основные команды (регистрируются ПОСЛЕ FSM)
    bot_instance.register_message_handler(handle_my_reports, func=lambda m: m.text == "Мои отчёты")
    bot_instance.register_message_handler(handle_send_report, func=lambda m: m.text == "Отправить отчёт")
