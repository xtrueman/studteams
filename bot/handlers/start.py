"""
Обработчики команд запуска бота.

Обрабатывают /start, /help и основные команды навигации.
"""

import aiogram
import aiogram.filters
import aiogram.fsm.context
import tgtexts
from aiogram import F
from aiogram.filters import Command

# import bot.database.queries as queries
import bot.db as db
import bot.keyboards.inline as inline_keyboards
import bot.keyboards.reply as keyboards
import bot.states.user_states as states
import bot.utils.decorators as decorators


@decorators.log_handler("start_command")
async def cmd_start(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработчик команды /start"""
    await state.clear()

    # Проверяем, есть ли код приглашения в команде
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if args:
        # /start с кодом приглашения
        invite_code = args[0]
        await handle_join_team(message, state, invite_code)
    else:
        # Обычный /start
        await handle_regular_start(message, state)


async def handle_regular_start(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка обычного старта без кода"""
    student = db.get_student_by_tg_id(message.from_user.id)

    if student:
        # Пользователь уже зарегистрирован
        has_team = 'team' in student
        is_admin = False

        if has_team:
            # In MySQL version, we have team info directly in student dict
            is_admin = student['team']['admin_student_id'] == student['student_id']

        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
        await message.answer(tgtexts.WELCOME_MESSAGE, reply_markup=keyboard, parse_mode="Markdown")
    else:
        # Новый пользователь
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
        await message.answer(
            "👋 Добро пожаловать в StudHelper!\n\n"
            "Для начала работы зарегистрируйте команду (если вы Scrum Master) "
            "или обратитесь к администратору команды за ссылкой-приглашением.",
            reply_markup=keyboard
        )


async def handle_join_team(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext, invite_code: str):
    """Обработка присоединения к команде по коду"""
    # Проверяем код приглашения
    team = db.get_team_by_invite_code(invite_code)

    if not team:
        await message.answer(
            "❌ Неверный код приглашения. Обратитесь к администратору команды за новой ссылкой."
        )
        return

    # Проверяем, не зарегистрирован ли уже пользователь
    student = db.get_student_by_tg_id(message.from_user.id)

    if student and 'team' in student:
        await message.answer(
            "❌ Вы уже состоите в команде. Для смены команды обратитесь к администратору."
        )
        return

    # Сохраняем данные команды в состояние
    await state.update_data(team_id=team['team_id'], team_name=team['team_name'])

    if student:
        # Пользователь есть в системе, но не в команде - сразу выбираем роль
        await state.set_state(states.JoinTeam.user_role)
        await message.answer(
            f"👥 Присоединяемся к команде *{team['team_name']}*\n\n"
            f"Выберите вашу роль в команде:",
            reply_markup=inline_keyboards.get_roles_inline_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # Новый пользователь - запрашиваем данные
        await state.set_state(states.JoinTeam.user_name)
        await message.answer(
            f"👥 Присоединяемся к команде *{team['team_name']}*\n\n"
            f"Введите ваше имя и фамилию:",
            parse_mode="Markdown"
        )


@decorators.log_handler("help_command")
async def cmd_help(message: aiogram.types.Message):
    """Обработчик команды /help"""
    await message.answer(tgtexts.HELP_MESSAGE, parse_mode="MarkdownV2")


@decorators.log_handler("help_button")
async def handle_help_button(message: aiogram.types.Message):
    """Обработчик кнопки Помощь"""
    await message.answer(tgtexts.HELP_MESSAGE, parse_mode="MarkdownV2")


@decorators.log_handler("update_button")
async def handle_update_button(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработчик кнопки Обновить"""
    await state.clear()

    student = db.get_student_by_tg_id(message.from_user.id)

    if student:
        has_team = 'team' in student
        is_admin = False

        if has_team:
            # In MySQL version, we have team info directly in student dict
            is_admin = student['team']['admin_student_id'] == student['student_id']

        keyboard = keyboards.get_main_menu_keyboard(is_admin=is_admin, has_team=has_team)
        await message.answer("🔄 Меню обновлено", reply_markup=keyboard)
    else:
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
        await message.answer("🔄 Меню обновлено", reply_markup=keyboard)


def register_start_handlers(dp: aiogram.Dispatcher):
    """Регистрация обработчиков"""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(handle_help_button, F.text == "Помощь")
    dp.message.register(handle_update_button, F.text == "Обновить")