"""
Обработчики функций оценивания участников команды.

Обрабатывают процесс взаимного оценивания и просмотр полученных оценок.
"""

import aiogram
import aiogram.fsm.context
from aiogram import F
from config import config

import bot.db as db
import bot.keyboards.inline as inline_keyboards
import bot.keyboards.reply as keyboards
import bot.states.user_states as states
import bot.utils.decorators as decorators


@decorators.log_handler("rate_teammates")
async def handle_rate_teammates(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало оценивания участников команды"""
    if not config.features.enable_reviews:
        await message.answer("❌ Функция оценивания временно отключена.")
        return

    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        await message.answer("❌ Вы не состоите в команде.")
        return

    # Получаем участников команды, которых еще не оценил пользователь
    teammates_to_rate = db.student_get_teammates_not_rated(student['student_id'])

    if not teammates_to_rate:
        await message.answer(
            "✅ Вы уже оценили всех участников команды!\n\n"
            "Используйте кнопку \"Кто меня оценил?\" чтобы посмотреть свои оценки.",
        )
        return

    # Создаем список имен для выбора
    teammate_names = [teammate['name'] for teammate in teammates_to_rate]

    await state.update_data(teammates_to_rate=teammates_to_rate)
    await state.set_state(states.ReviewProcess.teammate_selection)

    await message.answer(
        "⭐ *Оценивание участников команды*\n\n"
        "Выберите участника для оценки:",
        reply_markup=inline_keyboards.get_dynamic_inline_keyboard(teammate_names, "teammate", columns=2),
        parse_mode="Markdown",
    )


@decorators.log_handler("who_rated_me")
async def handle_who_rated_me(message: aiogram.types.Message):
    """Показать кто оценил пользователя"""
    if not config.features.enable_reviews:
        await message.answer("❌ Функция оценивания временно отключена.")
        return

    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        await message.answer("❌ Вы не состоите в команде.")
        return

    # Получаем оценки пользователя
    ratings = db.rating_get_who_rated_me(student['student_id'])

    if not ratings:
        await message.answer(
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

    await message.answer(full_text, parse_mode="Markdown")


@decorators.log_handler("process_rating_input")
async def process_rating_input(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка ввода оценки"""
    if message.text == "Отмена":
        await cancel_review(message, state)
        return

    try:
        rating = int(message.text.strip())
    except ValueError:
        await message.answer(
            f"❌ Введите число от {config.features.min_rating} до {config.features.max_rating}:",
        )
        return

    if rating < config.features.min_rating or rating > config.features.max_rating:
        await message.answer(
            "❌ Оценка должна быть от "
            f"{config.features.min_rating} до {config.features.max_rating}. "
            "Попробуйте еще раз:",
        )
        return

    await state.update_data(overall_rating=rating)
    await state.set_state(states.ReviewProcess.advantages_input)

    await message.answer(
        f"✅ Оценка: {rating}/10\n\n"
        f"👍 *Положительные качества*\n"
        f"Напишите положительные качества участника:",
        parse_mode="Markdown",
    )


@decorators.log_handler("process_advantages_input")
async def process_advantages_input(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка ввода положительных качеств"""
    if message.text == "Отмена":
        await cancel_review(message, state)
        return

    advantages = message.text.strip() if message.text and message.text.strip() else ""

    if len(advantages) < 15:
        await message.answer(
            "❌ Ответ слишком короткий. Минимум 15 символов.\n\n"
            "👍 Напишите положительные качества ещё раз:",
        )
        return

    if len(advantages) > 1000:
        await message.answer("❌ Текст слишком длинный. Максимум 1000 символов:")
        return

    data = await state.get_data()
    await state.update_data(advantages=advantages)
    await state.set_state(states.ReviewProcess.disadvantages_input)

    await message.answer(
        text=f"📈 *Области для улучшения*\n"
        f"Напишите, что {data['teammate_name']} мог бы улучшить:",
        parse_mode="Markdown",
    )


@decorators.log_handler("process_disadvantages_input")
async def process_disadvantages_input(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка ввода областей для улучшения"""
    if message.text == "Отмена":
        await cancel_review(message, state)
        return

    disadvantages = message.text.strip() if message.text and message.text.strip() else ""

    if len(disadvantages) < 15:
        await message.answer(
            "❌ Ответ слишком короткий. Минимум 15 символов.\n\n"
            "📈 Напишите области для улучшения ещё раз:",
        )
        return

    if len(disadvantages) > 1000:
        await message.answer("❌ Текст слишком длинный. Максимум 1000 символов:")
        return

    await state.update_data(disadvantages=disadvantages)
    await state.set_state(states.ReviewProcess.confirmation)

    # Показываем итоговую оценку
    data = await state.get_data()

    confirmation_text = (
        f"📋 *Проверьте оценку:*\n\n"
        f"👤 Участник: {data['teammate_name']}\n"
        f"⭐ Оценка: {data['overall_rating']}/10\n"
        f"👍 Плюсы: {data['advantages'][:100]}{'...' if len(data['advantages']) > 100 else ''}\n"
        f"📈 Что улучшить: {disadvantages[:100]}{'...' if len(disadvantages) > 100 else ''}\n\n"
        f"Отправить оценку?"
    )

    await message.answer(
        confirmation_text,
        reply_markup=inline_keyboards.get_review_confirm_keyboard(),
        parse_mode="Markdown",
    )


@decorators.log_handler("confirm_review")
async def confirm_review(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Подтверждение отправки оценки"""
    if message.text == "Отправить":
        student = db.student_get_by_tg_id(message.from_user.id)
        data = await state.get_data()

        try:
            db.rating_create(
                assessor_student_id=student['student_id'],
                assessored_student_id=data['selected_teammate_id'],
                overall_rating=data['overall_rating'],
                advantages=data['advantages'],
                disadvantages=data['disadvantages'],
            )

            await state.clear()

            await message.answer(
                f"✅ *Оценка успешно отправлена!*\n\n"
                f"👤 Участник: {data['teammate_name']}\n"
                f"⭐ Оценка: {data['overall_rating']}/10",
                parse_mode="Markdown",
            )

            # Переходим на страницу "Оценить участников команды"
            if config.features.enable_reviews:
                teammates_to_rate = db.student_get_teammates_not_rated(student['student_id'])

                if not teammates_to_rate:
                    await message.answer(
                        "✅ Вы уже оценили всех участников команды!\n\n"
                        "Используйте кнопку \"Кто меня оценил?\" чтобы посмотреть свои оценки.",
                    )
                else:
                    # Создаем список имен для выбора
                    teammate_names = [teammate['name'] for teammate in teammates_to_rate]

                    await state.update_data(teammates_to_rate=teammates_to_rate)
                    await state.set_state(states.ReviewProcess.teammate_selection)

                    keyboard = inline_keyboards.get_dynamic_inline_keyboard(
                        teammate_names, "teammate", columns=2,
                    )
                    await message.answer(
                        "⭐ *Оценивание участников команды*\n\n"
                        "Выберите участника для оценки:",
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )

        except Exception as e:
            await message.answer(
                f"❌ Ошибка при отправке оценки: {e!s}\n"
                f"Попробуйте еще раз.",
            )
            await state.clear()

    elif message.text == "Отмена":
        await cancel_review(message, state)


async def cancel_review(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Отмена оценивания"""
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

    await message.answer("❌ Оценивание отменено.", reply_markup=keyboard)


def register_reviews_handlers(dp: aiogram.Dispatcher):
    """Регистрация обработчиков оценивания"""
    # FSM обработчики РЕГИСТРИРУЮТСЯ ПЕРВЫМИ
    dp.message.register(process_rating_input, states.ReviewProcess.rating_input)
    dp.message.register(process_advantages_input, states.ReviewProcess.advantages_input)
    dp.message.register(process_disadvantages_input, states.ReviewProcess.disadvantages_input)
    dp.message.register(confirm_review, states.ReviewProcess.confirmation)

    # Основные команды (регистрируются ПОСЛЕ FSM)
    dp.message.register(handle_rate_teammates, F.text == "Оценить участников команды")
    dp.message.register(handle_who_rated_me, F.text == "Кто меня оценил?")
