"""
Обработчики callback-запросов от inline-клавиатур.

Обрабатывает все нажатия кнопок inline-клавиатур в боте.
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
import bot.utils.helpers as helpers

# Team Registration Callbacks


@decorators.log_handler("callback_confirm_team_reg")
async def callback_confirm_team_registration(
    callback: aiogram.types.CallbackQuery,
    state: aiogram.fsm.context.FSMContext,
):
    """Callback обработчик подтверждения регистрации команды"""
    data = await state.get_data()

    try:
        # Проверяем, есть ли уже пользователь в системе
        student = db.student_get_by_tg_id(callback.from_user.id)

        if not student:
            # Создаем нового пользователя только если его нет
            student = db.student_create(
                tg_id=callback.from_user.id,
                name=data['user_name'],
                group_num=data['user_group'] if data['user_group'] != "0" else None,
            )

        # Создаем команду
        invite_code = helpers.generate_invite_code()
        team = db.team_create(
            team_name=data['team_name'],
            product_name=data['product_name'],
            invite_code=invite_code,
            admin_student_id=student['student_id'],
        )

        # Добавляем администратора в команду
        db.team_add_member(
            team_id=team['team_id'],
            student_id=student['student_id'],
            role="Scrum Master",
        )

        await state.clear()

        # Отправляем главное меню
        keyboard = keyboards.get_main_menu_keyboard(is_admin=True, has_team=True)

        # Генерируем ссылку-приглашение с инструкцией
        invite_link_text = helpers.get_invite_link_text(
            data['team_name'], invite_code, show_instruction=True,
        )

        if callback.message:
            await callback.message.edit_text(
                f"🎉 *Команда успешно создана!*\n\n"
                f"👥 Команда: {data['team_name']}\n"
                f"📱 Продукт: {data['product_name']}\n"
                f"{invite_link_text}",
                parse_mode="Markdown",
            )

            await callback.message.answer("Главное меню:", reply_markup=keyboard)

    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при создании команды: {e!s}\n"
                f"Попробуйте еще раз или обратитесь к администратору.",
            )
        await state.clear()

    await callback.answer()


@decorators.log_handler("callback_cancel_team_reg")
async def callback_cancel_team_registration(
    callback: aiogram.types.CallbackQuery,
    state: aiogram.fsm.context.FSMContext,
):
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
        "role_member": "Участник команды",
    }

    if callback.data == "cancel":
        # Проверяем текущее состояние, чтобы понять контекст отмены
        current_state = await state.get_state()
        if current_state and "JoinTeam" in str(current_state):
            await callback_cancel_join_team(callback, state)
        else:
            await callback_cancel_action(callback, state)
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
            parse_mode="Markdown",
        )
    await callback.answer()

# Join Team Callbacks


@decorators.log_handler("callback_confirm_join_team")
async def callback_confirm_join_team(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения присоединения к команде"""
    data = await state.get_data()

    try:
        # Проверяем, есть ли пользователь в системе
        student = db.student_get_by_tg_id(callback.from_user.id)

        if not student:
            # Создаём нового пользователя - данные должны быть в state
            if 'user_name' not in data or 'user_group' not in data:
                await callback.answer("❌ Ошибка: недостаточно данных")
                return

            student = db.student_create(
                tg_id=callback.from_user.id,
                name=data['user_name'],
                group_num=data['user_group'] if data['user_group'] != "0" else None,
            )

        # Добавляем в команду
        db.team_add_member(
            team_id=data['team_id'],
            student_id=student['student_id'],
            role=data['user_role'],
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
                parse_mode="Markdown",
            )

            await callback.message.answer("Главное меню:", reply_markup=keyboard)

    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при присоединении к команде: {e!s}\n"
                f"Попробуйте еще раз или обратитесь к администратору.",
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


# Report Callbacks
@decorators.log_handler("callback_confirm_report")
async def callback_confirm_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения отправки отчета"""
    data = await state.get_data()
    is_editing = data.get('editing', False)

    try:
        student = db.student_get_by_tg_id(callback.from_user.id)

        db.report_create_or_update(
            student_id=student['student_id'],
            sprint_num=data['sprint_num'],
            report_text=data['report_text'],
        )

        await state.clear()

        # Показываем сообщение об успешном сохранении
        if callback.message:
            if is_editing:
                await callback.message.edit_text(
                    f"✅ *Отчет успешно обновлен!*\n\n"
                    f"📊 Спринт: №{data['sprint_num']}\n"
                    f"📅 Дата: {helpers.format_datetime('now')}",
                    parse_mode="Markdown",
                )
            else:
                await callback.message.edit_text(
                    f"✅ *Отчет успешно отправлен!*\n\n"
                    f"📊 Спринт: №{data['sprint_num']}\n"
                    f"📅 Дата: {helpers.format_datetime('now')}",
                    parse_mode="Markdown",
                )

            # Переходим на страницу "Мои отчёты"
            reports = db.report_get_by_student(student['student_id'])
            report_text = helpers.format_reports_list(reports)
            keyboard = inline_keyboards.get_report_management_keyboard(reports)
            await callback.message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при сохранении отчета: {e!s}\n"
                f"Попробуйте еще раз.",
            )
        await state.clear()

    await callback.answer()


@decorators.log_handler("callback_cancel_report")
async def callback_cancel_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены отправки отчета"""
    await state.clear()
    student = db.student_get_by_tg_id(callback.from_user.id)

    if callback.message:
        await callback.message.edit_text("❌ Отправка отчета отменена.")

        if student:
            has_team = 'team' in student
            is_admin = False
            if has_team:
                is_admin = student['team']['admin_student_id'] == student['student_id']

            keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
        else:
            keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)

        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()


@decorators.log_handler("callback_edit_report")
async def callback_edit_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик редактирования отчета"""
    if not callback.data or not callback.data.startswith("edit_report_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем номер спринта из callback_data
    try:
        sprint_num = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    student = db.student_get_by_tg_id(callback.from_user.id)

    # Получаем существующий отчет
    reports = db.report_get_by_student(student['student_id'])
    report_to_edit = None
    for report in reports:
        if report['sprint_num'] == sprint_num:
            report_to_edit = report
            break

    if not report_to_edit:
        await callback.answer("❌ Отчет не найден")
        return

    # Сохраняем данные в состоянии
    await state.update_data(
        sprint_num=sprint_num,
        report_text=report_to_edit['report_text'],
        editing=True,
    )

    await state.set_state(states.ReportCreation.report_text)

    if callback.message:
        report_preview = report_to_edit['report_text'][:200]
        ellipsis = '...' if len(report_to_edit['report_text']) > 200 else ''
        await callback.message.edit_text(
            f"📝 *Редактирование отчета*\n\n"
            f"📊 Спринт: №{sprint_num}\n\n"
            f"Текущий текст отчета:\n{report_preview}{ellipsis}\n\n"
            f"Введите новый текст отчета:",
            reply_markup=inline_keyboards.get_confirmation_inline_keyboard(
                "Отмена", "Назад", "cancel", "back",
            ),
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_delete_report_inline")
async def callback_delete_report_inline(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик удаления отчета (из inline клавиатуры)"""
    if not callback.data or not callback.data.startswith("delete_report_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем номер спринта из callback_data
    try:
        sprint_num = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    student = db.student_get_by_tg_id(callback.from_user.id)

    # Сохраняем данные в состоянии
    await state.update_data(
        sprint_num=sprint_num,
        student_id=student['student_id'],
    )

    if callback.message:
        await callback.message.edit_text(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Вы действительно хотите удалить отчет за *Спринт №{sprint_num}*?\n\n"
            f"*Это действие нельзя отменить!*",
            reply_markup=inline_keyboards.get_report_delete_confirm_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_confirm_delete_report")
async def callback_confirm_delete_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения удаления отчета"""
    data = await state.get_data()

    try:
        db.report_delete(
            student_id=data['student_id'],
            sprint_num=data['sprint_num'],
        )

        await state.clear()

        if callback.message:
            await callback.message.edit_text(
                f"✅ *Отчет за Спринт №{data['sprint_num']} успешно удален!*",
                parse_mode="Markdown",
            )

            # Переходим на страницу "Мои отчёты"
            student = db.student_get_by_tg_id(callback.from_user.id)
            reports = db.report_get_by_student(student['student_id'])
            report_text = helpers.format_reports_list(reports)
            keyboard = inline_keyboards.get_report_management_keyboard(reports)
            await callback.message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при удалении отчета: {e!s}\n"
                f"Попробуйте еще раз.",
            )
        await state.clear()

    await callback.answer()


@decorators.log_handler("callback_cancel_delete_report")
async def callback_cancel_delete_report(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены удаления отчета"""
    await state.clear()
    student = db.student_get_by_tg_id(callback.from_user.id)

    if callback.message:
        await callback.message.edit_text("❌ Удаление отчета отменено.")

        # Переходим на страницу "Мои отчёты"
        reports = db.report_get_by_student(student['student_id'])
        report_text = helpers.format_reports_list(reports)
        keyboard = inline_keyboards.get_report_management_keyboard(reports)
        await callback.message.answer(report_text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


# Review Callbacks
@decorators.log_handler("callback_confirm_review")
async def callback_confirm_review(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения отправки оценки"""
    if callback.data == "confirm_review":
        student = db.student_get_by_tg_id(callback.from_user.id)
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

            if callback.message:
                await callback.message.edit_text(
                    f"✅ *Оценка успешно отправлена!*\n\n"
                    f"👤 Участник: {data['teammate_name']}\n"
                    f"⭐ Оценка: {data['overall_rating']}/10",
                    parse_mode="Markdown",
                )

                # Переходим на страницу "Оценить участников команды"
                if config.features.enable_reviews:
                    teammates_to_rate = db.student_get_teammates_not_rated(student['student_id'])

                    if not teammates_to_rate:
                        await callback.message.answer(
                            "✅ Вы уже оценили всех участников команды!\n\n"
                            "Используйте кнопку \"Кто меня оценил?\" чтобы посмотреть свои оценки.",
                        )
                    else:
                        # Создаем список имен для выбора
                        teammate_names = [teammate['name'] for teammate in teammates_to_rate]

                        await state.set_state(states.ReviewProcess.teammate_selection)

                        keyboard = inline_keyboards.get_dynamic_inline_keyboard(
                            teammate_names, "teammate", columns=2,
                        )
                        await callback.message.answer(
                            "⭐ *Оценивание участников команды*\n\n"
                            "Выберите участника для оценки:",
                            reply_markup=keyboard,
                            parse_mode="Markdown",
                        )

        except Exception as e:
            if callback.message:
                await callback.message.edit_text(
                    f"❌ Ошибка при отправке оценки: {e!s}\n"
                    f"Попробуйте еще раз.",
                )
            await state.clear()

    await callback.answer()


@decorators.log_handler("callback_cancel_review")
async def callback_cancel_review(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены отправки оценки"""
    await state.clear()
    student = db.student_get_by_tg_id(callback.from_user.id)

    if callback.message:
        await callback.message.edit_text("❌ Отправка оценки отменена.")

        if student:
            has_team = 'team' in student
            is_admin = False
            if has_team:
                is_admin = student['team']['admin_student_id'] == student['student_id']

            keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
        else:
            keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)

        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()


# Team Member Management Callbacks
@decorators.log_handler("callback_remove_member_inline")
async def callback_remove_member_inline(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик удаления участника команды (из inline клавиатуры)"""
    if not callback.data or not callback.data.startswith("remove_member_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем ID участника из callback_data
    try:
        member_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    student = db.student_get_by_tg_id(callback.from_user.id)

    # Проверяем, что пользователь является администратором команды
    if not student or 'team' not in student or student['team']['admin_student_id'] != student['student_id']:
        await callback.answer("❌ Недостаточно прав")
        return

    team = student['team']

    # Получаем информацию об участнике
    member_to_remove = db.student_get_by_id(member_id)

    if not member_to_remove:
        await callback.answer("❌ Участник не найден")
        return

    # Сохраняем данные в состоянии
    await state.update_data(
        selected_member=member_to_remove,
        team_id=team['team_id'],
    )

    if callback.message:
        await callback.message.edit_text(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Вы действительно хотите удалить *{member_to_remove['name']}* из команды?\n\n"
            f"*Это действие нельзя отменить!*\n"
            f"Участник потеряет доступ ко всем функциям команды.",
            reply_markup=inline_keyboards.get_member_removal_confirm_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_confirm_remove_member")
async def callback_confirm_remove_member(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик подтверждения удаления участника"""
    data = await state.get_data()

    try:
        db.team_remove_member(
            team_id=data['team_id'],
            student_id=data['selected_member']['student_id'],
        )

        await state.clear()

        if callback.message:
            await callback.message.edit_text(
                f"✅ *Участник {data['selected_member']['name']} успешно удален из команды!*",
                parse_mode="Markdown",
            )

            # Обновляем информацию о команде
            team_data = helpers.get_team_display_data("", callback.from_user.id)

            if team_data:
                await callback.message.answer(
                    team_data['team_info'],
                    parse_mode="Markdown",
                    reply_markup=team_data['keyboard'],
                )

    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ Ошибка при удалении участника: {e!s}\n"
                f"Попробуйте еще раз.",
            )
        await state.clear()

    await callback.answer()


@decorators.log_handler("callback_cancel_remove_member")
async def callback_cancel_remove_member(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены удаления участника"""
    await state.clear()

    if callback.message:
        await callback.message.edit_text("❌ Удаление участника отменено.")

        # Обновляем информацию о команде
        team_data = helpers.get_team_display_data("", callback.from_user.id)

        if team_data:
            await callback.message.answer(
                team_data['team_info'],
                parse_mode="Markdown",
                reply_markup=team_data['keyboard'],
            )
    await callback.answer()


# Dynamic Callbacks (pattern-based)
@decorators.log_handler("callback_sprint_selection")
async def callback_sprint_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик выбора спринта"""
    if not callback.data or not callback.data.startswith("sprint_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем номер спринта из callback_data
    try:
        sprint_num = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    await state.update_data(sprint_num=sprint_num)
    await state.set_state(states.ReportCreation.report_text)

    if callback.message:
        await callback.message.edit_text(
            f"✅ Спринт №{sprint_num}\n\n"
            f"📝 Введите текст отчета о проделанной работе:",
            reply_markup=inline_keyboards.get_confirmation_inline_keyboard("Отмена", "Назад", "cancel", "back"),
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_member_selection")
async def callback_member_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик выбора участника команды"""
    if not callback.data or not callback.data.startswith("member_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем индекс участника из callback_data
    try:
        member_index = int(callback.data.split("_", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    data = await state.get_data()
    teammates = data.get('teammates_to_rate', [])

    # Проверяем, что индекс корректный
    if member_index < 0 or member_index >= len(teammates):
        await callback.answer("❌ Участник не найден")
        return

    # Получаем выбранного участника по индексу
    selected_teammate = teammates[member_index]

    # Сохраняем выбранного участника в состоянии
    await state.update_data(
        selected_teammate_id=selected_teammate['student_id'],
        teammate_name=selected_teammate['name'],
    )

    await state.set_state(states.ReviewProcess.rating_input)

    if callback.message:
        await callback.message.edit_text(
            f"⭐ *Оценка участника: {selected_teammate['name']}*\n\n"
            f"Поставьте оценку от {config.features.min_rating} до {config.features.max_rating}:",
            reply_markup=inline_keyboards.get_ratings_inline_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_teammate_selection")
async def callback_teammate_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик выбора участника для оценки"""
    if not callback.data or not callback.data.startswith("teammate_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем индекс участника из callback_data
    try:
        teammate_index = int(callback.data.split("_", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    data = await state.get_data()
    teammates = data.get('teammates_to_rate', [])

    # Проверяем, что индекс корректный
    if teammate_index < 0 or teammate_index >= len(teammates):
        await callback.answer("❌ Участник не найден")
        return

    # Получаем выбранного участника по индексу
    selected_teammate = teammates[teammate_index]

    # Сохраняем выбранного участника в состоянии
    await state.update_data(
        selected_teammate_id=selected_teammate['student_id'],
        teammate_name=selected_teammate['name'],
    )

    await state.set_state(states.ReviewProcess.rating_input)

    if callback.message:
        await callback.message.edit_text(
            f"⭐ *Оценка участника: {selected_teammate['name']}*\n\n"
            f"Поставьте оценку от {config.features.min_rating} до {config.features.max_rating}:",
            reply_markup=inline_keyboards.get_ratings_inline_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_rating_selection")
async def callback_rating_selection(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик выбора оценки"""
    if not callback.data or not callback.data.startswith("rating_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем оценку из callback_data
    try:
        rating = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    if rating < config.features.min_rating or rating > config.features.max_rating:
        await callback.answer(
            f"❌ Оценка должна быть от {config.features.min_rating} до {config.features.max_rating}",
        )
        return

    await state.update_data(overall_rating=rating)
    await state.set_state(states.ReviewProcess.advantages_input)

    if callback.message:
        await callback.message.edit_text(
            f"✅ Оценка: {rating}/10\n\n"
            f"👍 *Положительные качества*\n"
            f"Напишите положительные качества участника:",
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_edit_member")
async def callback_edit_member(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик редактирования участника команды"""
    if not callback.data or not callback.data.startswith("edit_member_"):
        await callback.answer("❌ Неверные данные")
        return

    # Извлекаем ID участника из callback_data
    try:
        member_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверные данные")
        return

    student = db.student_get_by_tg_id(callback.from_user.id)

    # Проверяем, что пользователь является администратором команды
    if not student or 'team' not in student or student['team']['admin_student_id'] != student['student_id']:
        await callback.answer("❌ Недостаточно прав")
        return

    # Получаем информацию об участнике
    member_to_edit = db.student_get_by_id(member_id)

    if not member_to_edit:
        await callback.answer("❌ Участник не найден")
        return

    # TODO: Implement member editing functionality
    # For now, we'll just show member info
    if callback.message:
        await callback.message.edit_text(
            f"✏️ *Редактирование участника*\n\n"
            f"Имя: {member_to_edit['name']}\n"
            f"ID: {member_to_edit['student_id']}\n\n"
            f"Функция редактирования пока не реализована.",
            parse_mode="Markdown",
        )
    await callback.answer()


@decorators.log_handler("callback_cancel_action")
async def callback_cancel_action(callback: aiogram.types.CallbackQuery, state: aiogram.fsm.context.FSMContext):
    """Callback обработчик отмены действия (универсальный)"""
    await state.clear()
    student = db.student_get_by_tg_id(callback.from_user.id)

    if callback.message:
        await callback.message.edit_text("❌ Действие отменено.")

        if student:
            has_team = 'team' in student
            is_admin = False
            if has_team:
                is_admin = student['team']['admin_student_id'] == student['student_id']

            keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
        else:
            keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)

        await callback.message.answer("Главное меню:", reply_markup=keyboard)
    await callback.answer()


def register_callback_handlers(dp: aiogram.Dispatcher):
    """Регистрация callback обработчиков"""
    # Team registration callbacks
    dp.callback_query.register(callback_confirm_team_registration, F.data == "confirm_team_reg")
    dp.callback_query.register(callback_cancel_team_registration, F.data == "cancel_team_reg")

    # Join team callbacks
    dp.callback_query.register(callback_confirm_join_team, F.data == "confirm_join_team")
    dp.callback_query.register(callback_cancel_join_team, F.data == "cancel_join_team")

    # Report callbacks - specific callbacks first
    dp.callback_query.register(callback_confirm_report, F.data == "confirm_report")
    dp.callback_query.register(callback_cancel_report, F.data == "cancel_report")
    dp.callback_query.register(callback_confirm_delete_report, F.data == "confirm_delete_report")
    dp.callback_query.register(callback_cancel_delete_report, F.data == "cancel_delete_report")

    # Review callbacks - specific callbacks first
    dp.callback_query.register(callback_confirm_review, F.data == "confirm_review")
    dp.callback_query.register(callback_cancel_review, F.data == "cancel_review")

    # Member management callbacks - specific callbacks first
    dp.callback_query.register(callback_confirm_remove_member, F.data == "confirm_remove_member")
    dp.callback_query.register(callback_cancel_remove_member, F.data == "cancel_remove_member")

    # Pattern-based callbacks with mixed patterns - more specific first
    dp.callback_query.register(callback_role_selection, F.data.in_(["role_po", "role_sm", "role_dev", "role_member"]))
    dp.callback_query.register(callback_sprint_selection, F.data.startswith("sprint_"))
    dp.callback_query.register(callback_member_selection, F.data.startswith("member_"))
    dp.callback_query.register(callback_teammate_selection, F.data.startswith("teammate_"))
    dp.callback_query.register(callback_rating_selection, F.data.startswith("rating_"))

    # Team member management callbacks (inline)
    dp.callback_query.register(callback_edit_member, F.data.startswith("edit_member_"))
    dp.callback_query.register(callback_remove_member_inline, F.data.startswith("remove_member_"))

    # Report management callbacks (inline)
    dp.callback_query.register(callback_edit_report, F.data.startswith("edit_report_"))
    dp.callback_query.register(callback_delete_report_inline, F.data.startswith("delete_report_"))

    # General cancel callback (fallback) - MUST BE LAST
    dp.callback_query.register(callback_cancel_action, F.data == "cancel")
