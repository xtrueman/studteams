"""
Обработчики функций оценивания участников команды.

Обрабатывают процесс взаимного оценивания и просмотр полученных оценок.
"""

import telebot

from config import config

from bot.state_storage import state_storage
from bot import db
from bot.bot_instance import bot
from bot.keyboards import inline as inline_keyboards
from bot.keyboards import reply as keyboards
from bot.utils import decorators as decorators


@decorators.log_handler("rate_teammates")
def handle_rate_teammates(message: telebot.types.Message, ):
    """Начало оценивания участников команды"""
    if not config.features.enable_reviews:
        bot.send_message(message.chat.id, "❌ Функция оценивания временно отключена.")
        return

    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    # Получаем участников команды, которых еще не оценил пользователь
    teammates_to_rate = db.student_get_teammates_not_rated(student['student_id'])

    if not teammates_to_rate:
        bot.send_message(message.chat.id,
            "✅ Вы уже оценили всех участников команды!\n\n"
            "Используйте кнопку \"Кто меня оценил?\" чтобы посмотреть свои оценки.",
        )
        return

    # Создаем список имен для выбора
    teammate_names = [teammate['name'] for teammate in teammates_to_rate]

    state_storage.update_data(message.from_user.id, teammates_to_rate=teammates_to_rate)
    state_storage.set_state(message.from_user.id, "states.ReviewProcess.teammate_selection")

    bot.send_message(message.chat.id,
        "⭐ *Оценивание участников команды*\n\n"
        "Выберите участника для оценки:",
        reply_markup=inline_keyboards.get_dynamic_inline_keyboard(teammate_names, "teammate", columns=2),
        parse_mode="Markdown",
    )


@decorators.log_handler("who_rated_me")
def handle_who_rated_me(message: telebot.types.Message):
    """Показать кто оценил пользователя"""
    if not config.features.enable_reviews:
        bot.send_message(message.chat.id, "❌ Функция оценивания временно отключена.")
        return

    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    # Получаем оценки пользователя
    ratings = db.rating_get_who_rated_me(student['student_id'])

    if not ratings:
        bot.send_message(message.chat.id,
            "⭐ Вас пока никто не оценил.\n\n"
            "Оценки появятся здесь после того, как участники команды "
            "воспользуются функцией \"Оценить участников команды\".",
        )
        return

    # Получаем информацию о команде для статистики
    teammates = db.student_get_teammates(student['student_id'])
    total_teammates = len(teammates)
    rated_count = len(ratings)

    # Формируем текст со списком оценивших
    if not ratings:
        ratings_text = "⭐ Вас пока никто не оценил"
    else:
        ratings_text = "*Меня оценили:*\n"
        for rating in ratings:
            # For MySQL version, we don't have datetime objects, so we need to handle this differently
            # Let's assume the date is already formatted as a string
            date_str = rating.get('rate_date', 'Неизвестно')
            ratings_text += f"• {rating['assessor_name']} ({date_str})\n"

    status_text = (
        f"*Статус оценок:*\n"
        f"✅ Оценили: {rated_count}\n"
        f"⏳ Осталось: {total_teammates - rated_count}\n"
        f"👥 Всего участников: {total_teammates}\n\n"
    )

    full_text = status_text + ratings_text

    bot.send_message(message.chat.id, full_text, parse_mode="Markdown")


@decorators.log_handler("process_rating_input")
def process_rating_input(message: telebot.types.Message, ):
    """Обработка ввода оценки"""
    if message.text == "Отмена":
        cancel_review(message)
        return

    try:
        rating = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id,
            f"❌ Введите число от {config.features.min_rating} до {config.features.max_rating}:",
        )
        return

    if rating < config.features.min_rating or rating > config.features.max_rating:
        bot.send_message(message.chat.id,
            "❌ Оценка должна быть от "
            f"{config.features.min_rating} до {config.features.max_rating}. "
            "Попробуйте еще раз:",
        )
        return

    state_storage.update_data(message.from_user.id, overall_rating=rating)
    state_storage.set_state(message.from_user.id, "states.ReviewProcess.advantages_input")

    bot.send_message(message.chat.id,
        f"✅ Оценка: {rating}/10\n\n"
        f"👍 *Положительные качества*\n"
        f"Напишите положительные качества участника:",
        parse_mode="Markdown",
    )


@decorators.log_handler("process_advantages_input")
def process_advantages_input(message: telebot.types.Message, ):
    """Обработка ввода положительных качеств"""
    if message.text == "Отмена":
        cancel_review(message)
        return

    advantages = message.text.strip() if message.text and message.text.strip() else ""

    if len(advantages) < 15:
        bot.send_message(message.chat.id,
            "❌ Ответ слишком короткий. Минимум 15 символов.\n\n"
            "👍 Напишите положительные качества ещё раз:",
        )
        return

    if len(advantages) > 1000:
        bot.send_message(message.chat.id, "❌ Текст слишком длинный. Максимум 1000 символов:")
        return

    data = state_storage.get_data(message.from_user.id)
    state_storage.update_data(message.from_user.id, advantages=advantages)
    state_storage.set_state(message.from_user.id, "states.ReviewProcess.disadvantages_input")

    bot.send_message(message.chat.id,
        text=f"📈 *Области для улучшения*\n"
        f"Напишите, что {data['teammate_name']} мог бы улучшить:",
        parse_mode="Markdown",
    )


@decorators.log_handler("process_disadvantages_input")
def process_disadvantages_input(message: telebot.types.Message, ):
    """Обработка ввода областей для улучшения"""
    if message.text == "Отмена":
        cancel_review(message)
        return

    disadvantages = message.text.strip() if message.text and message.text.strip() else ""

    if len(disadvantages) < 15:
        bot.send_message(message.chat.id,
            "❌ Ответ слишком короткий. Минимум 15 символов.\n\n"
            "📈 Напишите области для улучшения ещё раз:",
        )
        return

    if len(disadvantages) > 1000:
        bot.send_message(message.chat.id, "❌ Текст слишком длинный. Максимум 1000 символов:")
        return

    state_storage.update_data(message.from_user.id, disadvantages=disadvantages)
    state_storage.set_state(message.from_user.id, "states.ReviewProcess.confirmation")

    # Показываем итоговую оценку
    data = state_storage.get_data(message.from_user.id)

    confirmation_text = (
        f"📋 *Проверьте оценку:*\n\n"
        f"👤 Участник: {data['teammate_name']}\n"
        f"⭐ Оценка: {data['overall_rating']}/10\n"
        f"👍 Плюсы: {data['advantages'][:100]}{'...' if len(data['advantages']) > 100 else ''}\n"
        f"📈 Что улучшить: {disadvantages[:100]}{'...' if len(disadvantages) > 100 else ''}\n\n"
        f"Отправить оценку?"
    )

    bot.send_message(message.chat.id,
        confirmation_text,
        reply_markup=inline_keyboards.get_review_confirm_keyboard(),
        parse_mode="Markdown",
    )


@decorators.log_handler("confirm_review")
def confirm_review(message: telebot.types.Message, ):
    """Подтверждение отправки оценки"""
    if message.text == "Отправить":
        student = db.student_get_by_tg_id(message.from_user.id)
        data = state_storage.get_data(message.from_user.id)

        try:
            db.rating_create(
                assessor_student_id=student['student_id'],
                assessored_student_id=data['selected_teammate_id'],
                overall_rating=data['overall_rating'],
                advantages=data['advantages'],
                disadvantages=data['disadvantages'],
            )

            state_storage.clear_state(message.from_user.id)

            bot.send_message(message.chat.id,
                f"✅ *Оценка успешно отправлена!*\n\n"
                f"👤 Участник: {data['teammate_name']}\n"
                f"⭐ Оценка: {data['overall_rating']}/10",
                parse_mode="Markdown",
            )

            # Переходим на страницу "Оценить участников команды"
            if config.features.enable_reviews:
                teammates_to_rate = db.student_get_teammates_not_rated(student['student_id'])

                if not teammates_to_rate:
                    bot.send_message(message.chat.id,
                        "✅ Вы уже оценили всех участников команды!\n\n"
                        "Используйте кнопку \"Кто меня оценил?\" чтобы посмотреть свои оценки.",
                    )
                else:
                    # Создаем список имен для выбора
                    teammate_names = [teammate['name'] for teammate in teammates_to_rate]

                    state_storage.update_data(message.from_user.id, teammates_to_rate=teammates_to_rate)
                    state_storage.set_state(message.from_user.id, "states.ReviewProcess.teammate_selection")

                    keyboard = inline_keyboards.get_dynamic_inline_keyboard(
                        teammate_names, "teammate", columns=2,
                    )
                    bot.send_message(message.chat.id,
                        "⭐ *Оценивание участников команды*\n\n"
                        "Выберите участника для оценки:",
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )

        except Exception as e:
            bot.send_message(message.chat.id,
                f"❌ Ошибка при отправке оценки: {e!s}\n"
                f"Попробуйте еще раз.",
            )
            state_storage.clear_state(message.from_user.id)

    elif message.text == "Отмена":
        cancel_review(message)


def cancel_review(message: telebot.types.Message, ):
    """Отмена оценивания"""
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

    bot.send_message(message.chat.id, "❌ Оценивание отменено.", reply_markup=keyboard)


def register_reviews_handlers(bot_instance: telebot.TeleBot):
    """Регистрация обработчиков оценивания"""
    # FSM обработчики РЕГИСТРИРУЮТСЯ ПЕРВЫМИ

    # Основные команды (регистрируются ПОСЛЕ FSM)
    bot_instance.register_message_handler(handle_rate_teammates, func=lambda m: m.text == "Оценить участников команды")
    bot_instance.register_message_handler(handle_who_rated_me, func=lambda m: m.text == "Кто меня оценил?")
