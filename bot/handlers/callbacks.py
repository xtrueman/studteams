"""
Обработчики callback-запросов от inline-клавиатур.

Обрабатывает все нажатия кнопок inline-клавиатур в боте.
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

# Team Registration Callbacks


@decorators.log_handler("callback_confirm_team_reg")
async def callback_confirm_team_registration(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения регистрации команды"""
    data = await state.get_data()
    
    try:
        # Проверяем, есть ли уже пользователь в системе
        student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
        
        if not student:
            # Создаем нового пользователя только если его нет
            student = await queries.StudentQueries.create(
                tg_id=callback.from_user.id,
                name=data['user_name'],
                group_num=data['user_group']
            )
        
        # Создаем команду
        invite_code = helpers.generate_invite_code()
        team = await queries.TeamQueries.create(
            team_name=data['team_name'],
            product_name=data['product_name'],
            invite_code=invite_code,
            admin_id=student.id
        )
        
        # Добавляем администратора в команду
        await queries.TeamQueries.add_member(
            team_id=team.id,
            student_id=student.id,
            role="Scrum Master"
        )
        
        await state.clear()
        
        # Отправляем главное меню
        keyboard = keyboards.get_main_menu_keyboard(is_admin=True, has_team=True)
        
        # Генерируем ссылку-приглашение с инструкцией
        bot_info = await callback.bot.get_me()
        bot_username = bot_info.username if bot_info else None
        if bot_username:
            invite_link_text = await helpers.get_invite_link_text(
                data['team_name'], invite_code, bot_username, show_instruction=True
            )
        else:
            invite_link_text = ""
        
        if callback.message:
            await callback.message.edit_text(
                f"🎉 *Команда успешно создана!*\n\n"
                f"👥 Команда: {data['team_name']}\n"
                f"📱 Продукт: {data['product_name']}\n"
                f"🔗 Код приглашения: `{invite_code}`"
                f"{invite_link_text}",
                parse_mode="Markdown"
            )
            
            await callback.message.answer("Главное меню:", reply_markup=keyboard)
        
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при создании команды: {str(e)}\n"
                f"Попробуйте еще раз или обратитесь к администратору."
            )
        await state.clear()
    
    await callback.answer()


@decorators.log_handler("callback_cancel_team_reg")
async def callback_cancel_team_registration(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены регистрации команды"""
    await state.clear()
    keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
    
    if callback.message:
        await callback.message.edit_text("❌ Регистрация команды отменена.")
        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()

# Role Selection Callbacks


@decorators.log_handler("callback_role_selection")
async def callback_role_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик выбора роли"""
    role_mapping = {
        "role_po": "Product owner",
        "role_sm": "Scrum Master",
        "role_dev": "Разработчик",
        "role_member": "Участник команды"
    }
    
    if callback.data == "cancel":
        await callback_cancel_join_team(callback, state)
        return
    
    if not callback.data:
        await callback.answer("❌ Неверные данные")
        return
        
    role = role_mapping.get(callback.data)
    if not role:
        await callback.answer("❌ Неверная роль")
        return
    
    await state.update_data(user_role=role)
    await state.set_state(states.JoinTeam.confirm)
    
    # Показываем данные для подтверждения
    data = await state.get_data()
    
    confirmation_text = (
        f"📋 *Проверьте данные:*\n\n"
        f"👥 Команда: {data['team_name']}\n"
        f"👤 Ваше имя: {data.get('user_name', 'Уже зарегистрирован')}\n"
        f"🎓 Группа: {data.get('user_group', 'Уже указана')}\n"
        f"💼 Роль: {role}\n\n"
        f"Присоединиться к команде?"
    )
    
    if callback.message:
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=inline_keyboards.get_join_team_confirm_keyboard(),
            parse_mode="Markdown"
        )
    await callback.answer()

# Join Team Callbacks


@decorators.log_handler("callback_confirm_join_team")
async def callback_confirm_join_team(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения присоединения к команде"""
    data = await state.get_data()
    
    try:
        # Проверяем, есть ли пользователь в системе
        student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
        
        if not student:
            # Создаём нового пользователя - данные должны быть в state
            if 'user_name' not in data or 'user_group' not in data:
                await callback.answer("❌ Ошибка: недостаточно данных")
                return
                
            student = await queries.StudentQueries.create(
                tg_id=callback.from_user.id,
                name=data['user_name'],
                group_num=data['user_group']
            )
        
        # Добавляем в команду
        await queries.TeamQueries.add_member(
            team_id=data['team_id'],
            student_id=student.id,
            role=data['user_role']
        )
        
        await state.clear()
        
        # Отправляем главное меню
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=True)
        
        if callback.message:
            await callback.message.edit_text(
                f"🎉 *Добро пожаловать в команду!*\n\n"
                f"👥 Команда: {data['team_name']}\n"
                f"💼 Ваша роль: {data['user_role']}\n\n"
                f"Теперь вы можете отправлять отчеты о проделанной работе и "
                f"взаимодействовать с участниками команды.",
                parse_mode="Markdown"
            )
            
            await callback.message.answer("Главное меню:", reply_markup=keyboard)
        
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при присоединении к команде: {str(e)}\n"
                f"Попробуйте еще раз или обратитесь к администратору."
            )
        await state.clear()
    
    await callback.answer()


@decorators.log_handler("callback_cancel_join_team")
async def callback_cancel_join_team(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены присоединения к команде"""
    await state.clear()
    keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
    
    if callback.message:
        await callback.message.edit_text("❌ Присоединение к команде отменено.")
        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()

# Sprint Selection Callbacks


@decorators.log_handler("callback_sprint_selection")
async def callback_sprint_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Обработчик callback выбора спринта"""
    if not callback.data:
        await callback.answer("❌ Неверные данные")
        return
        
    if callback.data == "cancel":
        await callback_cancel_action(callback, state)
        return
    
    if not callback.data.startswith("sprint_"):
        await callback.answer("❌ Неверный формат")
        return
    
    sprint_num = int(callback.data.split("_")[1])
    
    await state.update_data(sprint_num=sprint_num)
    await state.set_state(states.ReportCreation.report_text)
    
    if callback.message:
        await callback.message.edit_text(
            f"✅ Спринт №{sprint_num}\n\n"
            f"📝 Введите текст отчета о проделанной работе:"
        )
    await callback.answer()

# Reports Callbacks


@decorators.log_handler("callback_confirm_report")
async def callback_confirm_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения отправки отчета"""
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    data = await state.get_data()
    
    try:
        await queries.ReportQueries.create_or_update(
            student_id=student.id,
            sprint_num=data['sprint_num'],
            report_text=data['report_text']
        )
        
        await state.clear()
        
        # Возвращаем главное меню
        has_team = bool(getattr(student, 'team_memberships', []))
        is_admin = False
        if has_team:
            team_membership = student.team_memberships[0]
            is_admin = team_membership.team.admin.id == student.id
        
        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
        
        if callback.message:
            await callback.message.edit_text(
                f"✅ *Отчет успешно отправлен!*\n\n"
                f"📊 Спринт: №{data['sprint_num']}\n"
                f"📅 Дата: {helpers.format_datetime('now')}",
                parse_mode="Markdown"
            )
            
            await callback.message.answer("Главное меню:", reply_markup=keyboard)
        
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при сохранении отчета: {str(e)}\n"
                f"Попробуйте еще раз."
            )
        await state.clear()
    
    await callback.answer()


@decorators.log_handler("callback_cancel_report")
async def callback_cancel_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены отправки отчета"""
    await callback_cancel_action(callback, state)


@decorators.log_handler("callback_confirm_delete_report")
async def callback_confirm_delete_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения удаления отчета"""
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    data = await state.get_data()
    
    try:
        await queries.ReportQueries.delete_report(
            student_id=student.id,
            sprint_num=data['sprint_num']
        )
        
        await state.clear()
        
        if callback.message:
            await callback.message.edit_text(
                f"🗑 *Отчет удален*\n\n"
                f"📊 Спринт №{data['sprint_num']} - отчет успешно удален",
                parse_mode="Markdown"
            )
            
            # Переходим на страницу "Мои отчёты"
            reports = await queries.ReportQueries.get_by_student(student.id)
            report_text = helpers.format_reports_list(reports)
            keyboard = inline_keyboards.get_report_management_keyboard(reports)
            await callback.message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при удалении отчета: {str(e)}\n"
                f"Попробуйте еще раз."
            )
        await state.clear()
    
    await callback.answer()


@decorators.log_handler("callback_cancel_delete_report")
async def callback_cancel_delete_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены удаления отчета"""
    await callback_cancel_action(callback, state)

# Member Selection Callbacks


@decorators.log_handler("callback_member_selection")
async def callback_member_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Обработчик callback выбора участника для удаления"""
    if not callback.data:
        await callback.answer("❌ Неверные данные")
        return
        
    if callback.data == "cancel":
        await callback_cancel_admin_action(callback, state)
        return
    
    if not callback.data.startswith("member_"):
        await callback.answer("❌ Неверный формат")
        return
    
    member_index = int(callback.data.split("_")[1])
    data = await state.get_data()
    teammates = data.get('teammates', [])
    
    if member_index >= len(teammates):
        await callback.answer("❌ Участник не найден")
        return
    
    selected_member = teammates[member_index]
    
    await state.update_data(selected_member=selected_member)
    await state.set_state(states.MemberRemoval.confirmation)
    
    if callback.message:
        await callback.message.edit_text(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Вы действительно хотите удалить *{selected_member.name}* из команды?\n\n"
            f"*Это действие нельзя отменить!*\n"
            f"Участник потеряет доступ ко всем функциям команды.",
            reply_markup=inline_keyboards.get_member_removal_confirm_keyboard(),
            parse_mode="Markdown"
        )
    await callback.answer()


@decorators.log_handler("callback_confirm_remove_member")
async def callback_confirm_remove_member(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения удаления участника"""
    data = await state.get_data()
    selected_member = data['selected_member']
    team_id = data['team_id']
    
    try:
        await queries.TeamQueries.remove_member(
            team_id=team_id,
            student_id=selected_member.id
        )
        
        await state.clear()
        
        # Получаем обновленную информацию о команде
        bot_info = await callback.bot.get_me()
        bot_username = bot_info.username if bot_info else None
        team_data = await helpers.get_team_display_data(None, callback.from_user.id, bot_username)
        
        if callback.message:
            if team_data:
                await callback.message.edit_text(
                    f"🗑 *Участник удален*\n\n"
                    f"👤 {selected_member.name} исключен из команды\n\n"
                    f"{team_data['team_info']}",
                    reply_markup=team_data['keyboard'],
                    parse_mode="Markdown"
                )
            else:
                await callback.message.edit_text(
                    f"🗑 *Участник удален*\n\n"
                    f"👤 {selected_member.name} исключен из команды",
                    parse_mode="Markdown"
                )
        
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при удалении участника: {str(e)}\n"
                f"Попробуйте еще раз."
            )
        await state.clear()
    
    await callback.answer()


@decorators.log_handler("callback_cancel_remove_member")
async def callback_cancel_remove_member(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены удаления участника"""
    await callback_cancel_admin_action(callback, state)

# Teammate Selection Callbacks (for reviews)


@decorators.log_handler("callback_teammate_selection")
async def callback_teammate_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик выбора участника для оценки"""
    if callback.data == "cancel":
        await callback_cancel_review(callback, state)
        return
    
    if not callback.data.startswith("teammate_"):
        await callback.answer("❌ Неверный формат")
        return
    
    teammate_index = int(callback.data.split("_")[1])
    data = await state.get_data()
    teammates_to_rate = data.get('teammates_to_rate', [])
    
    if teammate_index >= len(teammates_to_rate):
        await callback.answer("❌ Участник не найден")
        return
    
    selected_teammate = teammates_to_rate[teammate_index]
    
    await state.update_data(
        selected_teammate=selected_teammate,
        teammate_name=selected_teammate.name
    )
    await state.set_state(states.ReviewProcess.rating_input)
    
    if callback.message:
        await callback.message.edit_text(
            f"⭐ *Оценивание: {selected_teammate.name}*\n\n"
            f"Поставьте общую оценку от {config.MIN_RATING} до {config.MAX_RATING}:",
            reply_markup=inline_keyboards.get_ratings_inline_keyboard(),
            parse_mode="Markdown"
        )
    await callback.answer()

# Rating Selection Callbacks


@decorators.log_handler("callback_rating_selection")
async def callback_rating_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик выбора оценки"""
    if callback.data == "cancel":
        await callback_cancel_review(callback, state)
        return
    
    if not callback.data.startswith("rating_"):
        await callback.answer("❌ Неверный формат")
        return
    
    rating = int(callback.data.split("_")[1])
    
    if rating < config.MIN_RATING or rating > config.MAX_RATING:
        await callback.answer("❌ Неверная оценка")
        return
    
    data = await state.get_data()
    await state.update_data(overall_rating=rating)
    await state.set_state(states.ReviewProcess.advantages_input)
    
    if callback.message:
        await callback.message.edit_text(
            f"✅ Оценка: {rating}/10\n\n"
            f"👍 *Положительные качества*\n"
            f"Напишите, что вам нравится в работе {data['teammate_name']}:",
            reply_markup=inline_keyboards.get_skip_cancel_inline_keyboard("Пропустить", "Отмена"),
            parse_mode="Markdown"
        )
    await callback.answer()

# Skip/Cancel Callbacks (for reviews)


@decorators.log_handler("callback_skip")
async def callback_skip(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик пропуска ввода"""
    current_state = await state.get_state()
    
    if current_state == states.ReviewProcess.advantages_input:
        data = await state.get_data()
        await state.update_data(advantages="Не указано")
        await state.set_state(states.ReviewProcess.disadvantages_input)
        
        if callback.message:
            await callback.message.edit_text(
                f"✅ Положительные качества записаны\n\n"
                f"📈 *Области для улучшения*\n"
                f"Напишите, что {data['teammate_name']} мог бы улучшить:",
                reply_markup=inline_keyboards.get_skip_cancel_inline_keyboard("Пропустить", "Отмена"),
                parse_mode="Markdown"
            )
    
    elif current_state == states.ReviewProcess.disadvantages_input:
        await state.update_data(disadvantages="Не указано")
        await state.set_state(states.ReviewProcess.confirmation)
        
        # Показываем итоговую оценку
        data = await state.get_data()
        
        confirmation_text = (
            f"📋 *Проверьте оценку:*\n\n"
            f"👤 Участник: {data['teammate_name']}\n"
            f"⭐ Оценка: {data['overall_rating']}/10\n"
            f"👍 Плюсы: {data['advantages'][:100]}{'...' if len(data['advantages']) > 100 else ''}\n"
            f"📈 Что улучшить: {data['disadvantages'][:100]}{'...' if len(data['disadvantages']) > 100 else ''}\n\n"
            f"Отправить оценку?"
        )
        
        if callback.message:
            await callback.message.edit_text(
                confirmation_text,
                reply_markup=inline_keyboards.get_review_confirm_keyboard(),
                parse_mode="Markdown"
            )
    
    await callback.answer()

# Review Confirm Callbacks


@decorators.log_handler("callback_confirm_review")
async def callback_confirm_review(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения отправки оценки"""
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    data = await state.get_data()
    
    try:
        await queries.RatingQueries.create(
            assessor_id=student.id,
            assessed_id=data['selected_teammate']['id'],
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
        
        if callback.message:
            await callback.message.edit_text(
                f"✅ *Оценка отправлена!*\n\n"
                f"👤 {data['teammate_name']}\n"
                f"⭐ Оценка: {data['overall_rating']}/10\n\n"
                f"Спасибо за обратную связь!",
                parse_mode="Markdown"
            )
            
            await callback.message.answer("Главное меню:", reply_markup=keyboard)
        
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при сохранении оценки: {str(e)}\n"
                f"Попробуйте еще раз."
            )
        await state.clear()
    
    await callback.answer()


@decorators.log_handler("callback_cancel_review")
async def callback_cancel_review(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены оценивания"""
    await state.clear()
    
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    
    if student:
        has_team = bool(getattr(student, 'team_memberships', []))
        is_admin = False
        if has_team:
            team_membership = student.team_memberships[0]
            is_admin = team_membership.team.admin.id == student.id
        
        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
    else:
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
    
    if callback.message:
        await callback.message.edit_text("❌ Оценивание отменено.")
        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()

# General Cancel Callbacks


@decorators.log_handler("callback_cancel_action")
async def callback_cancel_action(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик общей отмены действия"""
    await state.clear()
    
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    
    if student:
        has_team = bool(getattr(student, 'team_memberships', []))
        is_admin = False
        if has_team:
            team_membership = student.team_memberships[0]
            is_admin = team_membership.team.admin.id == student.id
        
        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
    else:
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
    
    if callback.message:
        await callback.message.edit_text("❌ Действие отменено.")
        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()


@decorators.log_handler("callback_cancel_admin_action")
async def callback_cancel_admin_action(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены админского действия"""
    await state.clear()
    keyboard = keyboards.get_main_menu_keyboard(is_admin=True, has_team=True)
    
    if callback.message:
        await callback.message.edit_text("❌ Действие отменено.")
        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()

# Team Member Management Callbacks


@decorators.log_handler("callback_edit_member")
async def callback_edit_member(callback: aiogram.types.CallbackQuery):
    """Callback обработчик редактирования участника"""
    # Пока что просто заглушка - в будущем можно добавить функционал редактирования роли
    await callback.answer("⚠️ Функция редактирования участников будет доступна в следующих версиях", show_alert=True)

# Report Management Callbacks


@decorators.log_handler("callback_edit_report")
async def callback_edit_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик редактирования отчета"""
    if not callback.data.startswith("edit_report_"):
        await callback.answer("❌ Неверный формат")
        return
    
    sprint_num = int(callback.data.split("_")[2])
    
    # Получаем текущий отчет
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    
    if not student:
        await callback.answer("❌ Вы не зарегистрированы в системе")
        return
    
    reports = await queries.ReportQueries.get_by_student(student.id)
    current_report = None
    
    for report in reports:
        if report.sprint_num == sprint_num:
            current_report = report
            break
    
    if not current_report:
        await callback.answer("❌ Отчет не найден")
        return
    
    # Сохраняем данные в состоянии для редактирования
    await state.update_data(sprint_num=sprint_num, editing=True)
    await state.set_state(states.ReportCreation.report_text)
    
    if callback.message:
        await callback.message.edit_text(
            f"✏️ *Редактирование отчета*\n\n"
            f"📊 *Спринт №{sprint_num}:*\n"
            f"_{current_report.report_text}_\n\n"
            f"Введите новый текст отчета:",
            parse_mode="Markdown"
        )
    await callback.answer()


@decorators.log_handler("callback_delete_report_inline")
async def callback_delete_report_inline(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик удаления отчета через inline кнопку"""
    if not callback.data.startswith("delete_report_"):
        await callback.answer("❌ Неверный формат")
        return
    
    sprint_num = int(callback.data.split("_")[2])
    
    # Проверяем, что отчет существует
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    
    if not student:
        await callback.answer("❌ Вы не зарегистрированы в системе")
        return
    
    reports = await queries.ReportQueries.get_by_student(student.id)
    report_exists = any(report.sprint_num == sprint_num for report in reports)
    
    if not report_exists:
        await callback.answer("❌ Отчет не найден")
        return
    
    # Сохраняем данные в состоянии
    await state.update_data(sprint_num=sprint_num)
    
    if callback.message:
        await callback.message.edit_text(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Вы действительно хотите удалить отчет по спринту №{sprint_num}?\n\n"
            f"*Это действие нельзя отменить!*",
            reply_markup=inline_keyboards.get_report_delete_confirm_keyboard(),
            parse_mode="Markdown"
        )
    await callback.answer()


@decorators.log_handler("callback_remove_member_inline")
async def callback_remove_member_inline(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик удаления участника через inline кнопку"""
    if not callback.data.startswith("remove_member_"):
        await callback.answer("❌ Неверный формат")
        return
    
    member_id = callback.data.split("_")[2]
    
    # Проверяем права администратора
    student = await queries.StudentQueries.get_by_tg_id(callback.from_user.id)
    
    if not student or not getattr(student, 'team_memberships', None):
        await callback.answer("❌ Вы не состоите в команде")
        return
    
    team_membership = student.team_memberships[0]
    team = team_membership.team
    
    if team.admin.id != student.id:
        await callback.answer("❌ Удалять участников может только администратор команды")
        return
    
    # Получаем информацию об участнике
    member_to_remove = await queries.StudentQueries.get_by_id(member_id)
    
    if not member_to_remove:
        await callback.answer("❌ Участник не найден")
        return
    
    # Сохраняем данные в состоянии
    await state.update_data(
        selected_member=member_to_remove,
        team_id=team.id
    )
    
    if callback.message:
        await callback.message.edit_text(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Вы действительно хотите удалить *{member_to_remove.name}* из команды?\n\n"
            f"*Это действие нельзя отменить!*\n"
            f"Участник потеряет доступ ко всем функциям команды.",
            reply_markup=inline_keyboards.get_member_removal_confirm_keyboard(),
            parse_mode="Markdown"
        )
    await callback.answer()


def register_callback_handlers(dp: aiogram.Dispatcher):
    """Регистрация callback обработчиков"""
    # Team registration callbacks
    dp.callback_query.register(callback_confirm_team_registration, F.data == "confirm_team_reg")
    dp.callback_query.register(callback_cancel_team_registration, F.data == "cancel_team_reg")
    
    # Role selection callbacks
    dp.callback_query.register(callback_role_selection, F.data.in_(["role_po", "role_sm", "role_dev", "role_member", "cancel"]))
    
    # Join team callbacks
    dp.callback_query.register(callback_confirm_join_team, F.data == "confirm_join_team")
    dp.callback_query.register(callback_cancel_join_team, F.data == "cancel_join_team")
    
    # Sprint selection callbacks
    dp.callback_query.register(callback_sprint_selection, F.data.startswith("sprint_") | (F.data == "cancel"))
    
    # Report callbacks
    dp.callback_query.register(callback_confirm_report, F.data == "confirm_report")
    dp.callback_query.register(callback_cancel_report, F.data == "cancel_report")
    dp.callback_query.register(callback_confirm_delete_report, F.data == "confirm_delete_report")
    dp.callback_query.register(callback_cancel_delete_report, F.data == "cancel_delete_report")
    
    # Member selection callbacks
    dp.callback_query.register(callback_member_selection, F.data.startswith("member_") | (F.data == "cancel"))
    dp.callback_query.register(callback_confirm_remove_member, F.data == "confirm_remove_member")
    dp.callback_query.register(callback_cancel_remove_member, F.data == "cancel_remove_member")
    
    # Team member management callbacks (inline)
    dp.callback_query.register(callback_edit_member, F.data.startswith("edit_member_"))
    dp.callback_query.register(callback_remove_member_inline, F.data.startswith("remove_member_"))
    
    # Report management callbacks (inline)
    dp.callback_query.register(callback_edit_report, F.data.startswith("edit_report_"))
    dp.callback_query.register(callback_delete_report_inline, F.data.startswith("delete_report_"))
    
    # Review callbacks
    dp.callback_query.register(callback_teammate_selection, F.data.startswith("teammate_") | (F.data == "cancel"))
    dp.callback_query.register(callback_rating_selection, F.data.startswith("rating_") | (F.data == "cancel"))
    dp.callback_query.register(callback_skip, F.data == "skip")
    dp.callback_query.register(callback_confirm_review, F.data == "confirm_review")
    dp.callback_query.register(callback_cancel_review, F.data == "cancel_review")
    
    # General cancel callback (fallback)
    dp.callback_query.register(callback_cancel_action, F.data == "cancel")
