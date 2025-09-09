"""
Обработчики функций оценивания участников команды.

Обрабатывают процесс взаимного оценивания и просмотр полученных оценок.
"""

import aiogram
import aiogram.filters
import aiogram.fsm.context
import config
from aiogram import F

import bot.database.queries as queries
import bot.keyboards.inline as inline_keyboards
import bot.keyboards.reply as keyboards
import bot.states.user_states as states
import bot.utils.decorators as decorators
import bot.utils.helpers as helpers


@decorators.log_handler("rate_teammates")
async def handle_rate_teammates(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало оценивания участников команды"""
    if not config.ENABLE_REVIEWS:
        await message.answer("❌ Функция оценивания временно отключена.")
        return
    
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    
    if not student or not getattr(student, 'team_memberships', None):
        await message.answer("❌ Вы не состоите в команде.")
        return
    
    # Получаем участников команды, которых еще не оценил пользователь
    teammates_to_rate = await queries.StudentQueries.get_teammates_not_rated(student.id)
    
    if not teammates_to_rate:
        await message.answer(
            "✅ Вы уже оценили всех участников команды!\n\n"
            "Используйте кнопку \"Кто меня оценил?\" чтобы посмотреть свои оценки."
        )
        return
    
    # Создаем список имен для выбора
    teammate_names = [teammate.name for teammate in teammates_to_rate]
    
    await state.update_data(teammates_to_rate=teammates_to_rate)
    await state.set_state(states.ReviewProcess.teammate_selection)
    
    await message.answer(
        "⭐ *Оценивание участников команды*\n\n"
        "Выберите участника для оценки:",
        reply_markup=inline_keyboards.get_dynamic_inline_keyboard(teammate_names, "teammate", columns=2),
        parse_mode="Markdown"
    )


@decorators.log_handler("who_rated_me")
async def handle_who_rated_me(message: aiogram.types.Message):
    """Показать кто оценил пользователя"""
    if not config.ENABLE_REVIEWS:
        await message.answer("❌ Функция оценивания временно отключена.")
        return
    
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    
    if not student or not getattr(student, 'team_memberships', None):
        await message.answer("❌ Вы не состоите в команде.")
        return
    
    # Получаем оценки пользователя
    ratings = await queries.RatingQueries.get_who_rated_me(student.id)
    
    if not ratings:
        await message.answer(
            "⭐ Вас пока никто не оценил.\n\n"
            "Оценки появятся здесь после того, как участники команды "
            "воспользуются функцией \"Оценить участников команды\"."
        )
        return
    
    # Получаем информацию о команде для статистики
    teammates = await queries.StudentQueries.get_teammates(student.id)
    total_teammates = len(teammates)
    rated_count = len(ratings)
    
    ratings_text = helpers.format_ratings_list(ratings)
    
    status_text = (
        f"📊 *Статус оценок:*\n"
        f"✅ Оценили: {rated_count}\n"
        f"⏳ Осталось: {total_teammates - rated_count}\n"
        f"👥 Всего участников: {total_teammates}\n\n"
    )
    
    full_text = status_text + ratings_text
    
    await message.answer(full_text, parse_mode="Markdown")


@decorators.log_handler("process_teammate_selection")
async def process_teammate_selection(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка выбора участника для оценки"""
    if message.text == "Отмена":
        await cancel_review(message, state)
        return
    
    data = await state.get_data()
    teammates_to_rate = data.get('teammates_to_rate', [])
    
    # Находим выбранного участника
    selected_teammate = None
    for teammate in teammates_to_rate:
        if teammate.name == message.text:
            selected_teammate = teammate
            break
    
    if not selected_teammate:
        await message.answer("❌ Участник не найден. Выберите из предложенного списка:")
        return
    
    await state.update_data(
        selected_teammate=selected_teammate,
        teammate_name=selected_teammate.name
    )
    await state.set_state(states.ReviewProcess.rating_input)
    
    await message.answer(
        f"⭐ *Оценивание: {selected_teammate.name}*\n\n"
        f"Поставьте общую оценку от {config.MIN_RATING} до {config.MAX_RATING}:",
        reply_markup=inline_keyboards.get_ratings_inline_keyboard(),
        parse_mode="Markdown"
    )


@decorators.log_handler("process_rating_input")
async def process_rating_input(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка ввода оценки"""
    if message.text == "Отмена":
        await cancel_review(message, state)
        return
    
    rating = helpers.validate_rating(message.text)
    
    if rating is None:
        await message.answer(
            f"❌ Неверная оценка. Введите число от {config.MIN_RATING} до {config.MAX_RATING}:"
        )
        return
    
    data = await state.get_data()
    await state.update_data(overall_rating=rating)
    await state.set_state(states.ReviewProcess.advantages_input)
    
    await message.answer(
        f"✅ Оценка: {rating}/10\n\n"
        f"👍 *Положительные качества*\n"
        f"Напишите, что вам нравится в работе {data['teammate_name']}:",
        reply_markup=inline_keyboards.get_skip_cancel_inline_keyboard("Пропустить", "Отмена"),
        parse_mode="Markdown"
    )


@decorators.log_handler("process_advantages_input")
async def process_advantages_input(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка ввода положительных качеств"""
    if message.text == "Отмена":
        await cancel_review(message, state)
        return
    
    advantages = "Не указано" if message.text == "Пропустить" else message.text.strip()
    
    if len(advantages) > 1000:
        await message.answer("❌ Текст слишком длинный. Максимум 1000 символов:")
        return
    
    data = await state.get_data()
    await state.update_data(advantages=advantages)
    await state.set_state(states.ReviewProcess.disadvantages_input)
    
    await message.answer(
        f"✅ Положительные качества записаны\n\n"
        f"📈 *Области для улучшения*\n"
        f"Напишите, что {data['teammate_name']} мог бы улучшить:",
        reply_markup=inline_keyboards.get_skip_cancel_inline_keyboard("Пропустить", "Отмена"),
        parse_mode="Markdown"
    )


@decorators.log_handler("process_disadvantages_input")
async def process_disadvantages_input(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка ввода областей для улучшения"""
    if message.text == "Отмена":
        await cancel_review(message, state)
        return
    
    disadvantages = "Не указано" if message.text == "Пропустить" else message.text.strip()
    
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
        parse_mode="Markdown"
    )


@decorators.log_handler("confirm_review")
async def confirm_review(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Подтверждение отправки оценки"""
    if message.text == "Отправить":
        student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
        data = await state.get_data()
        
        try:
            await queries.RatingQueries.create(
                assessor_id=student.id,
                assessed_id=data['selected_teammate'].id,
                overall_rating=data['overall_rating'],
                advantages=data['advantages'],
                disadvantages=data['disadvantages']
            )
            
            await state.clear()
            
            # Возвращаем главное меню
            has_team = bool(getattr(student, 'team_memberships', []))
            is_admin = False
            if has_team:
                team_membership = student.team_memberships[0]
                is_admin = team_membership.team.admin.id == student.id
            
            keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
            
            await message.answer(
                f"✅ *Оценка отправлена!*\n\n"
                f"👤 {data['teammate_name']}\n"
                f"⭐ Оценка: {data['overall_rating']}/10\n\n"
                f"Спасибо за обратную связь!",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при сохранении оценки: {str(e)}\n"
                f"Попробуйте еще раз."
            )
            await state.clear()
    
    elif message.text == "Отмена":
        await cancel_review(message, state)


async def cancel_review(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Отмена процесса оценивания"""
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
    
    await message.answer("❌ Оценивание отменено.", reply_markup=keyboard)


def register_reviews_handlers(dp: aiogram.Dispatcher):
    """Регистрация обработчиков оценок"""
    if not config.ENABLE_REVIEWS:
        return
    
    # Основные команды
    dp.message.register(handle_rate_teammates, F.text == "Оценить участников команды")
    dp.message.register(handle_who_rated_me, F.text == "Кто меня оценил?")
    
    # FSM для процесса оценивания (только текстовые поля)
    # process_teammate_selection, process_rating_input, confirm_review теперь обрабатываются через callback
    dp.message.register(process_advantages_input, states.ReviewProcess.advantages_input)
    dp.message.register(process_disadvantages_input, states.ReviewProcess.disadvantages_input)
